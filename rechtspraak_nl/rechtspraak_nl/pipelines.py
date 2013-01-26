# -*- coding: utf-8 -*-
import csv

from scrapy import signals


class RechtspraakNlPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        f = open('%s.csv' % spider.name.replace('.', '-'), 'wb')
        self.files[spider] = f
        self.csvwriter = csv.DictWriter(f, ['name', 'gender', 'function',
            'function_type', 'institution', 'start_date', 'end_date', 'place',
            'institution_category',
        ], extrasaction='ignore', delimiter=';')
        self.csvwriter.writeheader()

    def spider_closed(self, spider):
        f = self.files.pop(spider)
        f.close()

    def process_item(self, item, spider):
        self.csvwriter.writerow(item)
        return item
