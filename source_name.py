import re
import math

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages
from src.fetchers.TreeFetcher import TreeFetcher
from src.result_fields.Overview import Overview


class Handler(Extract, GetPages):
    def __init__(self, source_config):
        super().__init__()
        self.fields = source_config.fields
        self.base_url = source_config.base_url
        self.NICK_NAME = source_config.NICK_NAME
        self.header = source_config.header

        self.fetcherConfig = {
            'link': source_config.base_url,
            'header': self.header,
            'method': 'GET',
            'data': None,
        }

        self.treeFetcher = TreeFetcher(self.fetcherConfig)

    def getpages(self, searchquery):
        link = f'https://www.value.today/?title={searchquery}&field_company_category_primary_target_id=&' \
                   'field_headquarters_of_company_target_id=All&' \
                   'field_company_website_uri=&field_market_value_jan072022_value='

        self.treeFetcher.extract_data(link)

        result = self.treeFetcher.get_by_xpath('//h2/a/@href')
        result = [self.base_url + i for i in result]

        return result

    def get_overview(self, link):
        requiredFieldsMap = {
            'isDomiciledIn': '//text()[contains(., "Headquarters Country")]/../following-sibling::div[1]//text()',
            'vcard:organization-name': '//h1/a/text()',
            'hasLatestOrganizationFoundedDate': '//text()[contains(., "Founded Year")]/../following-sibling::div[1]//text()',
            'logo': '//div[@class="clearfix col-sm-12 field field--name-field-company-logo-lc field--type-image field--label-hidden field--item"]/a/img/@src',
            'hasURL': '//text()[contains(., "Company Website:")]/../following-sibling::div[1]/a/@href',
            'bst:description': '//text()[contains(., "About Company Business:")]/../following-sibling::div[1]//text()',
            'registeredIn': '//text()[contains(., "Headquarters Region")]/../following-sibling::div[1]//text()',
            'bst:stock_info': '//text()[contains(., "Stock Exchange")]/../following-sibling::div[1]//text()',
            'size': '//text()[contains(., "Number of Employees")]/../following-sibling::div[1]//text()',
            'Service': '//div[@class="clearfix group-left"]/div//text()[contains(., "Company Business")]/../following-sibling::div[1]//text()',
        }

        hardCodedFields = {
            'bst:registryURI': link
        }

        overviewFields = {
            'requiredFieldsMap': requiredFieldsMap,
            'hardCodedFields': hardCodedFields
        }

        self.treeFetcher.extract_data(link)

        overview = Overview(overviewFields, self.treeFetcher)
        result = overview.get_result()

        return result

    def get_officership(self, link):
        off = []
        self.set_working_tree_api(link, 'tree')
        #
        #     url = 'https://englishdart.fss.or.kr/dsbc002/main.do'
        #     data = {
        #         'selectKey': link_name.split('?=')[0],
        #         'textCrpNm': link_name.split('?=')[-1]
        #     }
        #     self.get_working_tree_api(url, 'tree', 'POST', data=data)
        #
        #     # link_name = link_name.replace("'",'"').replace("None", '"None"')
        #     # self.api =json.loads(link_name)
        ceo = self.get_by_xpath(
            '//text()[contains(., "CEO:")]/../following-sibling::div[1]//text()')
        founders = self.get_by_xpath(
            '//text()[contains(., "Founders")]/../following-sibling::div[1]//text()')
        #
        try:
            for name in founders:
                off.append(
                    {'name': name,
                     'type': 'individual',
                     'officer_role': 'Founder',
                     'status': 'Active',
                     'occupation': 'Founder',
                     'information_source': self.base_url,
                     'information_provider': 'Value Today'})
        except:
            pass
        try:
            off.append(
                {'name': ceo[0],
                 'type': 'individual',
                 'officer_role': 'CEO',
                 'status': 'Active',
                 'occupation': 'CEO',
                 'information_source': self.base_url,
                 'information_provider': 'Value Today'})
        except:
            pass
        return off

    #
    #     auditor = self.get_by_xpath(
    #         '//label/text()[contains(., "External Auditor")]/../../following-sibling::td[1]/text()')
    #
    #     try:
    #
    #         off.append(
    #             {'name': auditor[0],
    #              'type': 'company',
    #              'officer_role': 'External Auditor',
    #              'status': 'Active',
    #              'occupation': 'External Auditor',
    #              'information_source': self.base_url,
    #              'information_provider': 'Korea ListedCompanies Association (KLCA)'})
    #     except:
    #         pass
    #
    #     # self.get_working_tree_api(link_name, 'tree')
    #
    #     # issueTab = self.get_by_xpath('//a/text()[contains(., "Issuer profile")]/../@href')
    #     # # print(issueTab[0])
    #     # if issueTab:
    #     #     number = re.findall('ctl00\$body\$IFTabsControlDetails\$lb\d', issueTab[0])
    #     #     if number:
    #     #         number = str(number[0][-1])
    #     # data = self.getHiddenValuesASP()
    #     # data[
    #     #     'ctl00$MasterScriptManager'] = f'ctl00$body$IFTabsControlDetails$ctl00|ctl00$body$IFTabsControlDetails$lb{number}'
    #     # data['__EVENTTARGET'] = f'ctl00$body$IFTabsControlDetails$lb{number}'
    #     # data['__ASYNCPOST'] = 'true'
    #     # data['ctl00$body$ctl02$NewsBySymbolControl$chOutVolatility'] = 'on'
    #     # data['ctl00$body$ctl02$NewsBySymbolControl$chOutInsiders'] = 'on'
    #     # data['gv_length'] = '10'
    #     # data['autocomplete-form-mob'] = ''
    #     # self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    #     # self.get_working_tree_api(link_name, 'tree', method='POST', data=data)
    #     #
    #     # try:
    #     #     t1 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[2]/td/text()')[0]
    #     #     n1 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[3]/td/text()')[0]
    #     #     t2 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[6]/td/text()')[0]
    #     #     n2 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[7]/td/text()')[0]
    #     #     off.append(
    #     #             {'name': n1,
    #     #                         'type': 'individual',
    #     #                         'officer_role': t1,
    #     #                         'status': 'Active',
    #     #                         'occupation': t1,
    #     #                         'information_source': self.base_url,
    #     #                         'information_provider': 'Bucharest Stock Exchange'}
    #     #         )
    #     #     if n1 != n2:
    #     #         off.append(
    #     #             {'name': n2,
    #     #              'type': 'individual',
    #     #              'officer_role': t2,
    #     #              'status': 'Active',
    #     #              'occupation': t2,
    #     #              'information_source': self.base_url,
    #     #              'information_provider': 'Bucharest Stock Exchange'}
    #     #         )
    #     # except:
    #     #     pass
    #
    #     # exit()
    #     #
    #     #
    #     #
    #     #
    #     # officership_prod_links = self.get_by_xpath('//div[@id="agentTable"]//td/a/@href')
    #     # officership_insur_links = self.get_by_xpath('//div[@id="companyTable"]//td/a/@href')
    #     # officership_prod_links = [self.base_url+i for i in officership_prod_links]
    #     # officership_insur_links = [self.base_url+i for i in officership_insur_links]
    #     #
    #     # for i in officership_prod_links[:-1]:
    #     #     officer = self.getOfficerFromPage(i, 'individual')
    #     #     if officer:
    #     #         off.append(officer)
    #     # for i in officership_insur_links[:-1]:
    #     #     officer = self.getOfficerFromPage(i, 'company')
    #     #     if officer:
    #     #         off.append(officer)
    #
    #     # names = self.get_by_api('Officer(s)')
    #     # if '\n' in names:
    #     #     names = names.split('\n')
    #     # # roles = self.get_by_xpath(
    #     # #     '//div/text()[contains(., "Right of representation")]/../following-sibling::div//tr/td[3]/text()')
    #     #
    #     # off = []
    #     # names = [names] if type(names) == str else names
    #     # roles = []
    #     # for name in names:
    #     #     roles.append(name.split(' - ')[-1])
    #     # names = [i.split(' - ')[0] for i in names]
    #     #
    #     # # roles = [roles] if type(roles) == str else roles
    #     # for n, r in zip(names, roles):
    #     #     home = {'name': n,
    #     #             'type': 'individual',
    #     #             'officer_role': r,
    #     #             'status': 'Active',
    #     #             'occupation': r,
    #     #             'information_source': self.base_url,
    #     #             'information_provider': 'Prince Edward Island Corporate Registry'}
    #     #     off.append(home)
    #     return off
    #
    # # def get_documents(self, link_name):
    # #     docs = []
    # #
    # #     link_name = link_name.replace("'", '"').replace("None", '"None"')
    # #     self.api = json.loads(link_name)
    # #
    # #     comp = self.api['InternationSecIN']
    # #
    # #     url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=InternationSecIN%20eq%20%27{self.api['InternationSecIN']}%27%20and%20(Type_of_Submission%20eq%20%27Financial%20Statements%27%20or%20Type_of_Submission%20eq%20%27EarningForcast%27)"
    # #
    # #     self.header['Accept'] = 'application/json;odata=verbose'
    # #     self.get_working_tree_api(url, 'api')
    # #     self.api = self.api['d']['results']
    # #
    # #     for doc in self.api[:1]:
    # #         temp = {
    # #             'url': doc['URL']['Url'],
    # #             'description': 'financial statements',
    # #             'date': doc['Modified'].split('T')[0]
    # #         }
    # #         docs.append(temp)
    # #
    # #     url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=InternationSecIN%20eq%20%27{comp}%27%20and%20(Type_of_Submission%20eq%20%27Corporate%20Actions%27%20or%20Type_of_Submission%20eq%20%27Corporate%20Disclosures%27%20or%20substringof(%27Meeting%27%20,Type_of_Submission))"
    # #     self.header['Accept'] = 'application/json;odata=verbose'
    # #     self.get_working_tree_api(url, 'api')
    # #
    # #     self.api = self.api['d']['results']
    # #
    # #     for doc in self.api[:10]:
    # #         temp = {
    # #             'url': doc['URL']['Url'],
    # #             'description': 'corporate disclosure',
    # #             'date': doc['Modified'].split('T')[0]
    # #         }
    # #         docs.append(temp)
    # #
    # #     url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=(InternationSecIN%20eq%20%27{comp}%27%20and%20(Type_of_Submission%20eq%20%27DirectorsDealings%27%20or%20Type_of_Submission%20eq%20%27Directors%20Dealings%27))"
    # #     self.header['Accept'] = 'application/json;odata=verbose'
    # #     self.get_working_tree_api(url, 'api')
    # #
    # #     self.api = self.api['d']['results']
    # #
    # #     for doc in self.api[:10]:
    # #         temp = {
    # #             'url': doc['URL']['Url'],
    # #             'description': 'directors dealing',
    # #             'date': doc['Modified'].split('T')[0]
    # #         }
    # #         docs.append(temp)
    # #
    # #     #
    # #     # issueTab = self.get_by_xpath('//a/text()[contains(., "Issuer profile")]/../@href')
    # #     # # print(issueTab[0])
    # #     # if issueTab:
    # #     #     number = re.findall('ctl00\$body\$IFTabsControlDetails\$lb\d', issueTab[0])
    # #     #     if number:
    # #     #         number = str(number[0][-1])
    # #     # data = self.getHiddenValuesASP()
    # #     # data[
    # #     #     'ctl00$MasterScriptManager'] = f'ctl00$body$IFTabsControlDetails$ctl00|ctl00$body$IFTabsControlDetails$lb{number}'
    # #     # data['__EVENTTARGET'] = f'ctl00$body$IFTabsControlDetails$lb{number}'
    # #     # data['__ASYNCPOST'] = 'true'
    # #     # data['ctl00$body$ctl02$NewsBySymbolControl$chOutVolatility'] = 'on'
    # #     # data['ctl00$body$ctl02$NewsBySymbolControl$chOutInsiders'] = 'on'
    # #     # data['gv_length'] = '10'
    # #     # data['autocomplete-form-mob'] = ''
    # #     # self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    # #     # self.get_working_tree_api(link_name, 'tree', method='POST', data=data)
    # #     #
    # #     #
    # #     # texts = self.tree.xpath('//div/text()[contains(., "Issuer documents")]/following-sibling::div[1]/div//td//text()')
    # #     # texts = [i.strip() for i in texts]
    # #     # texts = [i for i in texts if i]
    # #     #
    # #     # links = self.tree.xpath('//div/text()[contains(., "Issuer documents")]/following-sibling::div[1]/div//td/a/@href')
    # #     # links = [self.base_url+i for i in links]
    # #
    # #     return docs
    #
    # # def get_financial_information(self, link_name):
    # #     # self.get_working_tree_api(link_name, 'tree')
    # #
    # #     link_name = link_name.replace("'", '"').replace("None", '"None"')
    # #     self.api = json.loads(link_name)
    # #     print(self.api)
    # #
    # #     fin = {}
    # #     temp = {
    # #         'stock_id': ''
    # #     }
    # #
    # #     try:
    # #         temp['stock_name'] = ''
    # #     except:
    # #         pass
    # #
    # #     curr = {
    # #         'data_date': datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
    # #     }
    # #     # open = self.get_by_xpath('//td//text()[contains(., "Open price")]/../following-sibling::td//text()')
    # #     if open:
    # #         curr['open_price'] = str(self.api['OpenPrice'])
    # #
    # #     # min = self.get_by_xpath('//td//text()[contains(., "Low price")]/../following-sibling::td//text()')
    # #     # max = self.get_by_xpath('//td//text()[contains(., "High price")]/../following-sibling::td//text()')
    # #     min = self.api['DaysLow']
    # #     max = self.api['DaysHigh']
    # #
    # #     if min and max:
    # #         curr['day_range'] = f'{min}-{max}'
    # #
    # #     # vol = self.get_by_xpath('//td//text()[contains(., "Total no. of shares")]/../following-sibling::td//text()')
    # #     vol = self.api['Volume']
    # #     if vol:
    # #         curr['volume'] = str(vol)
    # #
    # #     # prClose= self.get_by_xpath('//td//text()[contains(., "Last price")]/../following-sibling::td//text()')
    # #     prClose = self.api['PrevClose']
    # #     if prClose:
    # #         curr['prev_close_price'] = str(prClose)
    # #
    # #     # cap = self.get_by_xpath('//td//text()[contains(., "Market cap")]/../following-sibling::td//text()')
    # #     cap = self.api['MarketCap']
    # #     if cap:
    # #         curr['market_capitalization'] = str(cap)
    # #
    # #     curr['exchange_currency'] = 'naira'
    # #
    # #     # min52 = self.get_by_xpath('//td//text()[contains(., "52 weeks low")]/../following-sibling::td//text()')
    # #     # max52 = self.get_by_xpath('//td//text()[contains(., "52 weeks high")]/../following-sibling::td//text()')
    # #     min52 = self.api['LOW52WK_PRICE']
    # #     max52 = self.api['HIGH52WK_PRICE']
    # #     if min52 and max52:
    # #         curr['52_week_range'] = f'{min52}-{max52}'
    # #
    # #     temp['current'] = curr
    # #     fin['stocks_information'] = [temp]
    # #
    # #     # summ = self.get_by_xpath('//div/text()[contains(., "Capital")]/../following-sibling::div//text()')
    # #
    # #     # if summ:
    # #     #     summ = re.findall('\d+', summ[0])
    # #     #     if summ:
    # #     fin['Summary_Financial_data'] = [{
    # #         'summary': {
    # #             'currency': 'naira',
    # #             'balance_sheet': {
    # #                 'market_capitalization': str(self.api['MarketCap'])
    # #             }
    # #         }
    # #     }]
    # #     self.get_working_tree_api(
    # #         f'https://ngxgroup.com/exchange/data/company-profile/?isin={self.api["InternationSecIN"]}&directory=companydirectory',
    # #         'tree')
    # #
    # #     res = []
    # #     dates = self.tree.xpath(
    # #         '//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[1]/text()')[:-1]
    # #     prices = self.tree.xpath(
    # #         '//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[2]/text()')[:-1]
    # #     volumes = self.tree.xpath(
    # #         '//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[3]/text()')[:-1]
    # #     prPrices = prices[1:]
    # #
    # #     for d, p, v, pr in zip(dates, prices, volumes, prPrices):
    # #         res.append(
    # #             {
    # #                 'data_date': datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d'),
    # #                 'open_price': pr,
    # #                 'close_price': p,
    # #                 'volume': v,
    # #                 'day_range': f'{pr}-{p}',
    # #             }
    # #         )
    # #     fin['stocks_information'].append({'historical_prices': res})
    # #
    # #     return fin
    #
    # def get_shareholders(self, link_name):
    #     url = 'https://englishdart.fss.or.kr/dsbc002/main.do'
    #     data = {
    #         'selectKey': link_name.split('?=')[0],
    #         'textCrpNm': link_name.split('?=')[-1]
    #     }
    #     self.get_working_tree_api(url, 'tree', 'POST', data=data)
    #
    #
    #
    #     edd = {}
    #     shareholders = {}
    #     sholdersl1 = {}
    #
    #     company = self.get_overview(link_name)
    #     company_name_hash = hashlib.md5(company['vcard:organization-name'].encode('utf-8')).hexdigest()
    #     # self.get_working_tree_api(link_name, 'api')
    #     # print(self.api)
    #
    #     try:
    #         names = self.get_by_xpath('//div/text()[contains(., "Major Stockholders")]/../following-sibling::div[1]//td/text()')
    #         #print(names)
    #
    #         # if len(re.findall('\d+', names)) > 0:
    #         #     return edd, sholdersl1
    #         # if '\n' in names:
    #         #     names = names.split('\n')
    #
    #         holders = [names] if type(names) == str else names
    #
    #         for i in range(len(holders)):
    #             holder_name_hash = hashlib.md5(holders[i].encode('utf-8')).hexdigest()
    #             shareholders[holder_name_hash] = {
    #                 # "natureOfControl": "SHH",
    #                 "source": 'Korea Listed Companies Association (KLCA)',
    #                 'totalPercentage': holders[i].split('(')[-1].split(')')[0]
    #             }
    #
    #
    #             if 'bank' in holders[i].lower():
    #                 holder_type = 'B'
    #             elif '.co' in holders[i].lower() or 'corporation' in holders[i].lower() or 'service' in holders[i].lower() or 'limited' in holders[i].lower():
    #                 holder_type = 'C'
    #             else:
    #                 holder_type = 'I'
    #
    #
    #             basic_in = {
    #                 "vcard:organization-name": holders[i].split('(')[0],
    #                 'isDomiciledIn': 'KR',
    #                 'entity_type': holder_type
    #             }
    #             sholdersl1[holder_name_hash] = {
    #                 "basic": basic_in,
    #                 "shareholders": {}
    #             }
    #     except:
    #         pass
    #
    #     edd[company_name_hash] = {
    #         "basic": company,
    #         "entity_type": "C",
    #         "shareholders": shareholders
    #     }
    #     # print(sholdersl1)
    #     return edd, sholdersl1
    #

    def get_officer_from_page(self, link, officerType):
        self.set_working_tree_api(link, 'tree')
        temp = {}
        temp['name'] = self.get_by_xpath('//div[@class="form-group"]//strong[2]/text()')[0]

        temp['type'] = officerType
        addr = ','.join(self.get_by_xpath('//div[@class="MasterBorder"]//div[2]//div/text()')[:-1])
        if addr:
            temp['address'] = {
                'address_line_1': addr,
            }
            zip = re.findall('\d\d\d\d\d-\d\d\d\d', addr)[0]
            if zip:
                temp['address']['postal_code'] = zip
                temp['address']['address_line_1'] = addr.split(zip)[0]

        temp['officer_role'] = 'PRODUCER' if officerType == 'individual' else 'COMPANY'

        temp['status'] = \
            self.get_by_xpath('//td//text()[contains(., "License Status")]/../../following-sibling::td//text()')[0]

        temp['information_source'] = self.base_url
        temp['information_provider'] = 'Idaho department of Insurance'
        return temp if temp['status'] == 'Active' else None

    def get_financial_information(self, link):
        self.set_working_tree_api(link, 'tree')
        total_assets = self.get_by_xpath(
            '//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[2]/text()')
        revenue = self.get_by_xpath(
            '//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]/../../following-sibling::table[1]//tr[3]//td[2]/text()')
        date = self.get_by_xpath(
            '//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[1]/text()')
        market_capitalization = self.get_by_xpath(
            '//text()[contains(., "Market Cap ")]/../following-sibling::div[1]//text()')
        total_liabilities = self.get_by_xpath(
            '//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[3]/text()')
        profit = self.get_by_xpath(
            '//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]/../../following-sibling::table[1]//tr[3]//td[4]/text()')
        # period = ''
        # print(total_assets, revenue, date, market_capitalization, total_liabilities, profit)

        income = {}
        balance = {}
        if date:
            balance['date'] = date[0].split('-')[-1]
        res = {}

        try:
            if 'Billion' in market_capitalization[0]:
                balance['market_capitalization'] = str(float(market_capitalization[0].split(' ')[0]) * 1000000000)[:-2]
            if 'Million' in market_capitalization[0]:
                balance['market_capitalization'] = str(float(market_capitalization[0].split(' ')[0]) * 1000000)[:-2]
        except:
            pass

        try:
            # if 'Billion' in tot[0]:
            balance['total_assets'] = total_assets[0]
            # if 'Million' in market_capitalization[0]:
            #         balance['market_capitalization'] = str(float(total_assets) * 1000000)[:-2]
        except:
            pass

        try:
            balance['total_liabilities'] = total_liabilities[0]
        except:
            pass

        temp = {}
        try:
            name = self.get_by_xpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]')
            if 'Billion' in name[0]:
                mult = 1000000000
            else:
                mult = 1000000

            temp['revenue'] = str(float(revenue[0]) * mult)
        except:
            pass
        try:
            date = date.split('-')[-1]
            temp['period'] = f'{date}-01-01-{date}-12-31'

        except:
            pass

        try:
            name = self.get_by_xpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]')
            if 'Billion' in name[0]:
                mult = 1000000000
            else:
                mult = 1000000
            # print(math.ceil(float(profit[0]) * mult))
            temp['profit'] = str(math.ceil(float(profit[0]) * mult))
        except:
            pass

        income = temp

        res['Summary_Financial_data'] = [{
            'source': link,
            'summary': {
                'currency': 'USD',
                'balance_sheet': balance
            }
        }]
        if income:
            res['Summary_Financial_data'][0]['summary']['income_statement'] = income

        return res

    #
    #     periods = len(self.get_by_xpath('//th/text()[contains(., "Net Sales")]/../following-sibling::td/text()'))
    #
    #     tempList = []
    #     for i in range(periods):
    #         period = self.get_by_xpath(
    #             f'//th/text()[contains(., "Account")]/../following-sibling::th[{i+1}]/text()')
    #
    #         net_sales = self.get_by_xpath(
    #             f'//th/text()[contains(., "Net Sales")]/../following-sibling::td[{i+1}]/text()')
    #
    #         operating_inc = self.get_by_xpath(
    #             f'//th/text()[contains(., "Operating Income (Loss)")]/../following-sibling::td[{i+1}]/text()')
    #
    #         assets = [self.get_by_xpath(
    #             f'//th/text()[contains(., "Assets")]/../following-sibling::td[{i+1}]/text()')[0]]
    #
    #         temp = {}
    #         if period and net_sales and operating_inc and assets:
    #             period = period[0].split('.')[0]
    #             period = [f'{period}-01-01-{period}-12-31']
    #             revenue = net_sales
    #
    #             for p, r, prof, sh in zip(period, revenue, operating_inc, assets):
    #                 tempList.append({
    #                     'period': p,
    #                     'revenue': r+ ',000',
    #                     'profit': prof + ',000',
    #                     'authorized_share_capital': sh + ',000',
    #                 })
    #
    #             temp['Summary_Financial_data'] = [{
    #                 'source': 'Korea ListedCompanies Association (KLCA)',
    #                 'summary': {
    #                     'currency': 'KRW',
    #                     'income_statement': tempList[0]
    #                 }
    #             }]
    #
    #             break
    #
    #         # print(temp)
    #     return temp
