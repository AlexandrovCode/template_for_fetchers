import requests
import re
import base64
from lxml import etree

class Handler():
    API_BASE_URL = ""
    base_url = "https://prod.ceidg.gov.pl"
    NICK_NAME = "prod.ceidg.gov.pl"
    FETCH_TYPE = ""
    TAG_RE = re.compile(r'<[^>]+>')

    search_url = base_url + '/CEIDG/CEIDG.Public.UI/Search.aspx'

    session = requests.Session()
    browser_header = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7'
    }

    def Execute(self, searchquery, fetch_type, action, API_BASE_URL):
        self.FETCH_TYPE = fetch_type
        self.API_BASE_URL = API_BASE_URL

        if fetch_type is None or fetch_type == '':
            pages = self.get_pages(searchquery)
            if pages is not None:
                data = self.parse_pages(pages)
            else:
                data = []
            dataset = data
        else:
            data = self.fetchByField(searchquery)
            dataset = [data]
        return dataset


    def get_pages(self, searchquery):
        r = self.session.get(self.search_url, headers=self.browser_header)


        links = []
        for i in range(0, 10):
            try:
                link = tree.xpath(f'//*[@id="MainContent_DataListEntities_hrefDetails_{i}"]')[0].get('href')
                rlink = self.base_url + '/CEIDG/CEIDG.Public.UI/' + link
                links.append(rlink)
            except:
                break
        return links

    def parse_pages(self, pages):
        rlist = []
        for link in pages:
            res = self.parse(link)
            if res is not None:
                rlist.append(res)
                if len(rlist) == 10:
                    break
        return rlist

    def links(self, link):
        data = {}
        base_url = self.NICK_NAME
        link2 = base64.b64encode(link.encode('utf-8'))
        link2 = (link2.decode('utf-8'))
        data['overview'] = {"method": "GET",
                            "url": self.API_BASE_URL + "?source=" + base_url + "&url=" + link2 + "&fields=overview"}
        return data

    def fetchByField(self, link):
        link_list = base64.b64decode(link).decode('utf-8')
        link = link_list.split('?reg_no=')[0]
        res = self.parse(link)
        return res

    def parse(self, link):
        r = self.session.get(link)
        tree = etree.HTML(r.content)
        edd = {}

        if self.FETCH_TYPE == 'overview' or self.FETCH_TYPE == '':
            company = {}
            edd['overview'] = company


        link = link + '?reg_no=' + id
        edd['_links'] = self.links(link)
        return edd

    def extract_from_tree(self, tree, expression, return_many=False):
        try:
            el = tree.xpath(expression)
            if return_many:
                return el
            else:
                return el[0]
        except:
            return None




