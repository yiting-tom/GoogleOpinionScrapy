import os
import re
from datetime import datetime
from typing import Union, List

import scrapy
import praw

from ..items import RedditPostItem


class RedditgooglepixelSpider(scrapy.Spider):
    name = 'redditGooglePixel'
    allowed_domains = ['www.reddit.com']
    start_urls = ['https://www.reddit.com/r/GooglePixel/']

    sub_maximum = 500
    comment_maximum = 1000

    def parse(self, response: scrapy.http.Response, **kwargs):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='reddit_google_opinion/1.0'
        )

        subs = self.reddit.subreddit('GooglePixel').hot(limit=self.sub_maximum)  # GooglePixel subreddit
        for sub in subs:
            yield scrapy.Request(f'https://www.reddit.com{sub.url}' if sub.url.startswith('/r') else sub.url,
                                 self._parse_content, meta={'title': sub.title, 'url': sub.url})

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
