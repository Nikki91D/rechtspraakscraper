from scrapy.item import Item, Field


class Function(Item):
    name = Field()
    gender = Field()
    function = Field()
    function_type = Field()
    institution = Field()
    start_date = Field()
    end_date = Field()
    place = Field()
    institution_category = Field()
