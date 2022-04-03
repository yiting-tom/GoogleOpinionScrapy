from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Tuple

import scrapy

from ..items import PostItem
from ..model import PostInfo, PushInfo


class MobilecommSpider(scrapy.Spider):
    name: str = 'mobileComm'
    allowed_domains: List[str] = ['www.ptt.cc']
    start_urls: List[str] = [
        'https://www.ptt.cc/bbs/MobileComm/index.html',
    ]

    XPATH: Dict[str, Any] = {
        'hub': {
            'previous_page': (
                '/html/body/div[@id="main-container"]'
                '/div[@id="action-bar-container"]'
                '/div[@class="action-bar"]'
                '/div[@class="btn-group btn-group-paging"]'
                '/a[2]/@href'
            ),
            'root': (
                '/html/body/div[@id="main-container"]'
                '/div[@class="r-list-container action-bar-margin bbs-screen"]'
                '//div[@class="r-ent"]'
            ),
            'url': (
                './div[@class="title"]'
                '/a/@href'
            ),
            'push': (
                './div[@class="nrec"]'
                '/span'
                '/text()'
            ),
        },
        'post': {
            'root': (
                '/html/body/div[@id="main-container"]'
                '/div[@id="main-content"]'
            ),
            'author': (
                './div[@class="article-metaline"][1]'
                '/span[2]'
                '/text()'
            ),
            'title': (
                './div[@class="article-metaline"][2]'
                '/span[2]'
                '/text()'
            ),
            'datetime': (
                './div[@class="article-metaline"][last()]'
                '/span[2]'
                '/text()'
            ),
            'content': (
                './/text()[normalize-space()]'
            ),
        },
        'push': {
            'root': (
                '/html/body/div[@id="main-container"]'
                '/div[@id="main-content"]'
                '//div[@class="push"]'
            ),
            'push_tag': './span[1]/text()',
            'pusher': './span[2]/text()',
            'push_content': './span[3]/text()',
            'push_datetime': './span[4]/text()',
        }
    }

    def parse(self, response: scrapy.http.Response):
        # get all posts infos.
        post_infos: List[PostInfo] = self.parse_hub(response=response)

        # extract all info from post.
        for post_info in post_infos:

            yield scrapy.Request(
                url=post_info.url,
                callback=self.parse_post,
                cb_kwargs={'post_info': post_info},
            )

        # crawle previous page.
        previous_page_url = response.xpath(
            self.XPATH['hub']['previous_page']).get()

        # parse next page.
        if previous_page_url:
            self.log(f"crawle next page url: {previous_page_url}", 20)
            yield response.follow(previous_page_url, callback=self.parse)

    def parse_hub(self, response: scrapy.http.Response) -> List[PostInfo]:

        # get all posts selector in hub.
        posts: List[scrapy.Selector] = response.xpath(
            self.XPATH['hub']['root']
        )

        post_infos = defaultdict(list)

        for post in posts:
            # handle the schema value for `url`.
            target = 'url'
            xpath = self.XPATH['hub'][target]
            extracted = post.xpath(xpath).get()
            post_infos[target].append(response.urljoin(extracted))

            # handle the None value for `push` value.
            target = 'push'
            xpath = self.XPATH['hub'][target]
            extracted = post.xpath(xpath).get() or '0'
            post_infos[target].append(extracted)

        self.log(f"prase hub [{post_infos}]: {response.url}", 30)

        return PostInfo.from_dict(post_infos)

    def parse_post(self, response: scrapy.http.Response, post_info: PostInfo):

        # anker to post.
        post: scrapy.Selector = response.xpath(self.XPATH['post']['root'])

        # get datetime and content.
        post_info.update(
            self.xpath_parse(post, self.XPATH['post']))

        # get all pushs.
        pushes = self.parse_pushs(response)
        pushes = [push.to_dict() for push in pushes]
        post_info.pushes = pushes

        self.log(f"prase post [{len(post_info.pushes)}]: {response.url}", 30)

        yield PostItem(**post_info.to_dict())

    def parse_pushs(self, response: scrapy.http.Response) -> List[PushInfo]:
        # anker to push.
        pushes = response.xpath(self.XPATH['push']['root'])

        # get all push info and instant to PushInfos.
        return PushInfo.from_dict(self.xpath_parse(pushes, self.XPATH['push']))

    @staticmethod
    def xpath_parse(root: List[scrapy.Selector], xpath_dict: Dict[str, Any], *skip_targets) -> Dict[str, List[str]]:
        skip_targets = *skip_targets, 'root'
        infos = {}

        for target, xpath in xpath_dict.items():
            # skip specific targets.
            if target in skip_targets:
                continue

            # assert the xpath is in string type.
            assert isinstance(xpath, str), \
                TypeError(f'xpath_parse: xpath type error: {xpath}')

            infos.update({target: root.xpath(xpath).extract()})

        return infos
