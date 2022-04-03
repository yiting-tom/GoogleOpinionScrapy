# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PostItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    push = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    datetime = scrapy.Field()
    content = scrapy.Field()
    pushes = scrapy.Field()
