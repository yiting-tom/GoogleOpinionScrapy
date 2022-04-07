from collections import defaultdict
import logging
from typing import Any, Dict, List
import scrapy

from ..items import PostItem
from ..model import PostInfo, PushInfo

class GamertwSpider(scrapy.Spider):
    name = 'gamertw'
    allowed_domains = ['forum.gamer.com.tw']
    start_urls = ['http://forum.gamer.com.tw/B.php?bsn=60559']

    XPATH: Dict[str, Any] = {
        'hub': {
            'next_page': (
                '/html/body/div[@id="BH-background"]'
                '//div/div[@id="BH-master"]'
                '/div[@class="b-pager pager"]'
                '/div/a[@class="next"]'
                '/@href'
            ),
            'root': (
                '/html/body/div[@id="BH-background"]'
                '//div/div[@id="BH-master"]'
                '/form/div[contains (@class, "b-list-wrap")]'
                '//table'
                '//tr[contains (@class, "b-list__row") and not(contains (@class, "is-del"))]'
            ),
            'url': (
                './td[@class="b-list__main"]'
                '//p[@class="b-list__main__title"]'
                '/@href'
            ),
            'push': (
                './td[@class="b-list__summary"]'
                '/span'
                '/text()'
            ),
        },
        'post': {
            'root': (
                '(/html/body/div[@id="BH-background"]'
                '/div[@id="BH-wrapper"]'
                '/div[@id="BH-master"]'
                '//div[contains(concat(" ",normalize-space(@class)," ")," c-post ")])[1]'
            ),
            'author': (
                './/div[@class="c-post__header"]'
                '/div[@class="c-post__header__author"]'
                '/a[@class="username"]'
                '/text()'
            ),
            'title': (
                './/div[@class="c-post__header"]'
                '/h1[contains (@class, "c-post__header__title")]'
                '/text()'
            ),
            'datetime': (
                './/div[@class="c-post__header"]'
                '/div[@class="c-post__header__info"]'
                '/a[contains (@class, "edittime")]'
                '/@data-mtime'
            ),
            'content': (
                './/div[@class="c-post__body"]'
                '//div[@class="c-article__content"]'
                '//text()[normalize-space()]'
            ),
            # 'next_page': (
            #     '/html/body/div[@id="BH-background"]'
            #     '/div[@id="BH-wrapper"]'
            #     '/div[@id="BH-master"]'
            #     '//div[@id="BH-pagebtn"]'
            #     '/a[@class="next"]'
            #     '/@href'
            # ),
        },
        'push': {
            'root': (
                '/html/body/div[@id="BH-background"]'
                '/div[@id="BH-wrapper"]'
                '/div[@id="BH-master"]'
                '//div[contains(concat(" ",normalize-space(@class)," ")," c-post ") and not(.//h1)]'
            ),
            # 'push_tag': '/',
            'pusher': (
                './div[@class="c-post__header"]'
                '/div[@class="c-post__header__author"]'
                '/a[@class="username"]'
                '/text()'
            ),
            'push_datetime': (
                './div[@class="c-post__header"]'
                '/div[@class="c-post__header__info"]'
                '/a[contains (@class, "edittime")]'
                '/@data-mtime'
            ),
            'push_content': (
                './/div[@class="c-article__content"]'
                '//text()[normalize-space()]'
            ),
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
        # get next page.
        next_page_url = response.xpath(
            self.XPATH['hub']['next_page']).get()
        # parse next page.
        if next_page_url:
            self.log(f"next page url: {next_page_url}", 20)
            yield response.follow(next_page_url, callback=self.parse)

    def parse_hub(self, response: scrapy.http.Response) -> List[PostInfo]:
        # get all posts selector in hub.
        posts: List[scrapy.Selector] = response.xpath(
            self.XPATH['hub']['root']
        )
        post_infos = defaultdict(list)
        for post in posts:
            # handle the schema value for `url`.
            xpath = self.XPATH['hub']['url']
            extracted = post.xpath(xpath).get()
            post_infos['url'].append(response.urljoin(extracted))
            # handle the None value for `push` value.
            xpath = self.XPATH['hub']['push']
            extracted = post.xpath(xpath).get() or '0'
            post_infos['push'].append(extracted)

        self.log(f"prase hub [{post_infos}]: {response.url}", 30)
        return PostInfo.from_dict(post_infos)

    def parse_post(self, response: scrapy.http.Response, post_info: PostInfo):
        # anker to post.
        post: scrapy.Selector = response.xpath(self.XPATH['post']['root'])
        # get datetime and content.
        post_info.update(self.xpath_parse(post, self.XPATH['post']))
        # get all pushs.
        pushes = self.parse_pushs(response)
        pushes = [push.to_dict() for push in pushes]
        post_info.pushes = pushes

        # only digest 1st page, TODO: handle multiple pages
        #
        # next_page_url = response.xpath(
        #     self.XPATH['post']['next_page']).get()
        # if next_page_url:
        #     self.log(f"post next page url: {next_page_url}", 20)
        #     yield response.follow(
        #         next_page_url,
        #         callback=self.parse_post,
        #         cb_kwargs={'post_info': post_info}
        #     )

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
