# How to scrapy?

## Environment setup

1. `pipenv install`
2. `pipenv shell`

## Generate a new spider

1. go into the crawler-system directory by `cd crawler-system`
2. using scrapy build-in tools: `scrapy genspider <spiderName> <targetUrl>` to generate a spider template.

## Configurations setup

1. go into the <spiderName> directory there is a `settings.py` script file.
2. you can turn on/off the _pipelines_, _middlewares_, and other components in it.
