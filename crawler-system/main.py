from scrapy import cmdline


def main():
    cmdline.execute("scrapy crawl mobileComm".split())


if __name__ == '__main__':
    main()
