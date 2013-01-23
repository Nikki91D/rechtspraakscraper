from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter


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
        self.exporter = CsvItemExporter(f, delimiter=';')
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        f = self.files.pop(spider)
        f.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
