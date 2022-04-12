import os
import re
from datetime import datetime
from typing import Union, List

import scrapy
import praw

from ..items import RedditPostItem


class RedditpixelcommSpider(scrapy.Spider):
    name = 'redditPixelComm'
    allowed_domains = ['www.reddit.com']
    start_urls = ['https://www.reddit.com/user/PixelCommunity/']

    sub_maximum = 100
    comm_maximum = 100
    comment_maximum = 1000

    def parse(self, response: scrapy.http.Response, **kwargs):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='reddit_google_opinion/1.0'
        )

        pixelcomm_redditor = self.reddit.redditor('PixelCommunity')
        subs = pixelcomm_redditor.submissions.new(limit=self.sub_maximum)  # PixelCommunity
        for sub in subs:
            yield scrapy.Request(f'https://www.reddit.com{sub.url}' if sub.url.startswith('/r') else sub.url,
                                 self._parse_content, meta={'title': sub.title, 'url': sub.url})

        # comments = pixelcomm_redditor.comments.hot(limit=self.comm_maximum)
        # for comm in comments:
        #     yield self._parse_comment(comm)

    def _parse_content(self, response: scrapy.http.Response):
        title = response.meta['title']
        url = response.meta['url']
        content = response.css('div._3xX726aBn29LDbsDtzr_6E ::text').getall()

        sub_id = re.split('/|commets', url)[-3]
        sub = self.reddit.submission(id=sub_id)
        sub.comments.replace_more(limit=self.comment_maximum)
        comments = self._parse_replies(sub.comments.list())

        author = sub.author.name
        posted_date = datetime.fromtimestamp(sub.created)
        posted_date = posted_date.strftime('%m/%d/%Y')

        hot_post = RedditPostItem(title=title, url=url, content=''.join(content), comments=comments,
                                  author=author, datetime=posted_date)
        yield hot_post

    def _parse_replies(self, comments: List[Union['praw.models.Comment', 'praw.models.MoreComments']]):
        if not len(comments):
            return []

        comment_list = []
        for comment in comments:
            if comment.body in ('\'[removed]\'', '\'[deleted]\'', '[removed]', '[deleted]'):
                continue

            comment_list.append(comment.body)

            # comment_list.append({
            #     'comment': comment.body,
            #     'replies': self._parse_replies(comment.replies.list())
            # })

        return comment_list

    def _parse_comment(self, comment):
        title = comment.link_title
        url = comment.link_url
        content = comment.body

        author = comment.author.name
        posted_date = datetime.fromtimestamp(comment.created)
        posted_date = posted_date.strftime('%m/%d/%Y')

        sub = comment.submission
        sub.comments.replace_more(self.comment_maximum)
        comments = [com for com in sub.comments.list() if com.id == comment.id]
        comments = self._parse_replies(comments[0].replies.list())

        hot_post = RedditPostItem(title=title, url=url, content=content, comments=comments,
                                  author=author, datetime=posted_date)
        return hot_post
