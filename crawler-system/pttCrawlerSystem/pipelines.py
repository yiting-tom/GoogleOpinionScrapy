# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import abc
import re
from typing import Tuple

import pymongo
import scrapy
from pymongo import collection
from scrapy import exceptions

from pttCrawlerSystem import items, settings


class PostPipeline:

    def process_item(self, item: items.PostItem, spider: scrapy.Spider):
        # get id by hashing url.
        item['id'] = hash(item['url'])

        # drop item if without any pushes.
        if not item['pushes']:
            raise exceptions.DropItem('without any pushes')
        # transform from list to string.
        self.__get_first(item, 'title', 'author', 'datetime')
        # handle the title process logics.
        self.__handle_title(item)
        # handle the content process logics.
        self.__handle_content(item)

        spider.log(f"save: {item['title']}[{len(item['pushes'])}]", 30)
        return item

    def __get_first(self, item: items.PostItem, *keys: Tuple[str]):
        for key in keys:
            try:
                item[key] = item[key][0]
            except IndexError:
                pass

    def __handle_title(self, item: items.PostItem) -> None:
        try:
            is_announcement = re.match(
                pattern=r'\[公告\]',
                string=item['title']
            )
        # can't get title.
        except IndexError:
            raise exceptions.DropItem('without any title')

        # title match with `[公告]`
        else:
            if is_announcement:
                raise exceptions.DropItem('title with [公告]')

    def __handle_content(self, item: items.PostItem) -> None:
        # transform from list to string.
        item['content'] = ' '.join(item['content'][8:-1])

        # drop specific characters.
        item['content'] = re.sub(
            pattern=(
                r'\n*|'              # empty line.
                r'(  )+|'           # multiple spaces.
                r'--(.*\n*)*$'      # -- to the end of the content.
            ),
            repl='',
            string=item['content']
        )

    @abc.abstractmethod
    def to_mongodb(self, item: items.PostItem, spider: scrapy.Spider):
        ...


class MobileCommPipeline(PostPipeline):
    def __init__(self):
        host: str = settings.MONGODB_HOST
        port: int = settings.MONGODB_PORT
        dbname: str = settings.MONGODB_DBNAME
        collection_name: str = 'mobileComm'

        client = pymongo.MongoClient(host=host, port=port)
        db = client[dbname]

        self.collection: collection.Collection = db[collection_name]

    def to_mongodb(self, item: items.PostItem, spider: scrapy.Spider):
        self.collection.insert_one(dict(item))

        return item

    def process_item(self, item: items.PostItem, spider: scrapy.Spider):
        item = super().process_item(item, spider)

        self.to_mongodb(item, spider)
        return item


class RedditPixelCommPipeline(PostPipeline):
    def __init__(self):
        host: str = settings.MONGODB_HOST
        port: int = settings.MONGODB_PORT
        dbname: str = settings.MONGODB_DBNAME
        collection_name: str = 'redditPixelComm'

        client = pymongo.MongoClient(host=host, port=port)
        db = client[dbname]

        self.collection: collection.Collection = db[collection_name]

    def process_item(self, item: items.PostItem, spider: scrapy.Spider):
        item['id'] = hash(item['url'])
        self.to_mongodb(item, spider)

        spider.log(f'save: {item["title"]}[{len(item["comments"])}]', 30)

        return item

    def to_mongodb(self, item: items.PostItem, spider: scrapy.Spider):
        self.collection.insert_one(dict(item))

        return item


class RedditGooglePixelPipeline(PostPipeline):
    def __init__(self):
        host: str = settings.MONGODB_HOST
        port: int = settings.MONGODB_PORT
        dbname: str = settings.MONGODB_DBNAME
        collection_name: str = 'redditGooglePixel'

        client = pymongo.MongoClient(host=host, port=port)
        db = client[dbname]

        self.collection: collection.Collection = db[collection_name]

    def process_item(self, item: items.PostItem, spider: scrapy.Spider):
        item['id'] = hash(item['url'])
        self.to_mongodb(item, spider)

        spider.log(f'save: {item["title"]}[{len(item["comments"])}]', 30)

        return item

    def to_mongodb(self, item: items.PostItem, spider: scrapy.Spider):
        self.collection.insert_one(dict(item))

        return item
