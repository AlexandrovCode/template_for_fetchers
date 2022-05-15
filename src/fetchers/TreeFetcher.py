from lxml import etree

from src.fetchers.BaseFetcher import BaseFetcher


class TreeFetcher(BaseFetcher):
    def extract_data(self, link=None):
        try:
            super().extract_data(link)
            content = self.extractedData
        except Exception as e:
            print(e)
            pass

        self.extractedData = etree.HTML(content.content)

    def get_by_xpath(self, xpath):
        try:
            el = self.extractedData.xpath(xpath)
        except Exception as e:
            print(e)
            return None
        if el:
            if type(el) == str or type(el) == list:
                el = [i.strip() for i in el]
                el = [i for i in el if i != '']
            if len(el) > 1 and type(el) == list:
                el = list(dict.fromkeys(el))
            return el
        else:
            return None

    def get_hidden_values_ASP(self):
        names = self.get_by_xpath('//input[@type="hidden"]/@name')
        temp = {}
        for name in names:
            value = self.get_by_xpath(f'//input[@type="hidden"]/@name[contains(., "{name}")]/../@value')
            temp[name] = value[0] if value else ''
        return temp
