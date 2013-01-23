from datetime import datetime

from scrapy.conf import settings
from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
from scrapy.selector import HtmlXPathSelector

from rechtspraak_nl.items import Function


class RechtSpraakNlSpider(BaseSpider):
    name = 'namenlijst.rechtspraak.nl'
    url = 'http://namenlijst.rechtspraak.nl'

    def start_requests(self):
        return [Request(self.url, self.parse_search_page)]

    def parse_search_page(self, response):
        # Parses initial search page for all input elements
        hxs = HtmlXPathSelector(response)

        # Find all input values
        institutions = hxs.select('//fieldset[@id="instanties"]//input')

        if not institutions:
            return

        for institution in institutions:
            formdata = {
                'ctl00$ContentPlaceHolder1$ddlFunctions': 'alle functies',
                'ctl00$ContentPlaceHolder1$hiddenFieldSelectedFunction':
                    'alle functies',
                'ctl00$ContentPlaceHolder1$txtSearchKenmerken': '',
                'ctl00$ContentPlaceHolder1$btnSearch': 'Zoeken'
            }

            name = institution.select('@name').extract()[0]
            value = institution.select('@value').extract()[0]
            formdata[name] = value

            institution_name = institution.select('../label/text()')\
                                .extract()[0]

            # For Courts of Appeal and Courts, an additional string
            # parameter is required, for some reason
            if 'chklCourtsOfAppeal' in name:
                formdata['gerechtshoven'] = 'gerechtshoven'
                institution_name = 'Gerechtshof %s' % (institution_name)

            elif 'chklCourts' in name:
                formdata['rechtbanken'] = 'rechtbanken'
                institution_name = 'Rechtbank %s' % (institution_name)

            request = FormRequest.from_response(response,
                                        formdata=formdata,
                                        dont_click=True,
                                        callback=self.parse_search_results)

            request.meta['institution_name'] = institution_name

            yield request

    def parse_search_results(self, response):
        hxs = HtmlXPathSelector(response)

        results = hxs.select('//table[@id="resultaat"]/tbody//tr//input')

        institution = response.meta['institution_name']

        for result in results:
            name = result.select('@value').extract()[0]
            formdata = {
                result.select('@name').extract()[0]: name
            }
            request = FormRequest.from_response(response,
                                        formdata=formdata,
                                        dont_click=True,
                                        callback=self.parse_result_page)
            request.meta['name'] = name
            request.meta['institution'] = institution
            if 'mw.' in name:
                request.meta['gender'] = 'female'
            elif 'dhr.' in name:
                request.meta['gender'] = 'male'
            else:
                request.meta['gender'] = 'unknown'

            yield request

        # Handle pagination
        next = hxs.select('//input[@class="next"]')
        if next:
            formdata = {
                next.select('@name').extract()[0]:
                next.select('@value').extract()[0]
            }
            request = FormRequest.from_response(response,
                                        formdata=formdata,
                                        dont_click=True,
                                        callback=self.parse_search_results)

            request.meta['institution_name'] = institution

            yield request

    def parse_result_page(self, response):
        hxs = HtmlXPathSelector(response)

        def dls_between(node1, node2):
            # This enormous XPath expression selects all dl siblings between
            # node1 and node 2. We need this because the data of different job
            # categories are not nested properly
            return '//div[@class="details"]/%(start_node)s/following-'\
                   'sibling::%(end_node)s[1]/preceding-sibling::dl[preceding-'\
                   'sibling::%(start_node)s]'\
                    % {'start_node': node1, 'end_node': node2}

        print response.meta['name']

        current_functions = hxs.select(dls_between(
                        'h2[text()="Beroepsgegevens"]',
                        'h2[text()="Nevenbetrekkingen"]'
                    ))

        additional_functions = hxs.select(dls_between(
                        'h2[text()="Nevenbetrekkingen"]',
                        'h2[text()="Voorgaande betrekkingen"]'
                    ))

        previous_functions = hxs.select(dls_between(
                        'h2[text()="Voorgaande betrekkingen"]',
                        'p[@class="textoptimalwidth"]'
                    ))

        functions = []

        for current_function in current_functions:
            try:
                data = current_function.select('.//dd/text()').extract()
                date = datetime.strptime(data[2].strip(), '%d-%m-%Y')\
                    .strftime('%Y-%m-%d')
                functions.append(
                    Function(
                        name=response.meta['name'],
                        gender=response.meta['gender'],
                        function=data[0].strip(),
                        institution=data[1].strip(),
                        start_date=date,
                        function_type='current'
                    )
                )
            except:
                # Something weird happened. TODO: decide what happens
                pass

        for additional_function in additional_functions:
            try:
                data = additional_function.select('.//dd/text()').extract()
                date = datetime.strptime(data[3].strip(), '%d-%m-%Y')\
                    .strftime('%Y-%m-%d')
                f = {
                    'name': response.meta['name'],
                    'gender': response.meta['gender'],
                    'function': data[0].strip(),
                    'institution': data[1].strip(),
                    'place': data[2].strip(),
                    'start_date': date,
                    'function_type': 'additional'
                }

                if len(data) == 5:
                    f['institution_category'] = data[4]
                else:
                    f['end_date'] = datetime.strptime(data[4].strip(),\
                        '%d-%m-%Y').strftime('%Y-%m-%d')
                    f['institution_category'] = data[5]

                functions.append(Function(f))
            except:
                # Something weird happened. TODO: decide what happens
                pass

        for previous_function in previous_functions:
            try:
                data = previous_function.select('.//dd/text()').extract()
                sdate = datetime.strptime(data[-2].strip(), '%d-%m-%Y')\
                    .strftime('%Y-%m-%d')
                edate = datetime.strptime(data[-1].strip(), '%d-%m-%Y')\
                    .strftime('%Y-%m-%d')
                f = {
                    'name': response.meta['name'],
                    'gender': response.meta['gender'],
                    'function_type': 'previous',
                    'function': data[0].strip(),
                    'institution': data[1].strip(),
                    'start_date': sdate,
                    'end_date': edate
                }
                functions.append(Function(f))
            except:
                # Something weird happened. TODO: decide what happens
                pass

        return functions
