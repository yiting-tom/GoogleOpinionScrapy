# How to scrapy?

## Environment setup

1. `pipenv install`
2. `pipenv shell`

## Generate a new spider

1. go into the crawler-system directory by `cd crawler-system`
2. using scrapy build-in tools: `scrapy genspider <spiderName> <targetUrl>` to generate a spider template.

## Configurations setup

1. go into the <spiderName> directory there is a `settings.py` script file.
2. you can turn on/off the **logging**, **database**, **pipelines**, **middlewares**, and other components in it (_ref: pttCrawlerSystem/setting.py_).

## Develop a spider

1. go to **main.py** script file and add new line with `cmdline.execute("scrapy crawl <spiderName>".split())`, and comment other line with **cmdline.execute(...)** for testing your spider.
2. learn [scrapy official docs](https://docs.scrapy.org/en/latest/index.html).
