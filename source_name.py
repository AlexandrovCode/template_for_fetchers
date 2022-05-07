import datetime
import re
import math
import pycountry
import json

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://www.value.today'
    NICK_NAME = base_url.split('//')[-1]
    fields = ['overview',
              'officership',
              # 'graph:shareholders',
              'Financial_Information']
    overview = {}
    tree = None
    api = None

    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9;application/json;application/json;odata=verbose',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    def getpages(self, searchquery):
        result = []
        link_1 = 'https://www.value.today/'
        self.setWorkingTreeApi(link_1, 'tree')
        link_2 = 'https://www.value.today/views/ajax?_wrapper_format=drupal_ajax'
        # '[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")'
        link_new = f'https://www.value.today/?title={searchquery}&field_company_category_primary_target_id=&field_headquarters_of_company_target_id=All&field_company_website_uri=&field_market_value_jan072022_value='
        self.setWorkingTreeApi(link_new, 'tree')
        result = self.getByXpath('//h2/a/@href')
        result = [self.base_url + i for i in result]

        return result

    def setWorkingTreeApi(self, link_name, type, method='GET', data=None): # reduce arguments
        if type == 'tree':
            if data:
                self.tree = self.get_tree(link_name,
                                          headers=self.header, method=method, data=data)
            else:
                self.tree = self.get_tree(link_name,
                                          headers=self.header, method=method)
        if type == 'api':
            if data:
                # self.api = self.get_content(link_name,
                #                             headers=self.header, method=method, data=json.dumps(data))
                # print(self.api)
                self.api = self.get_content(link_name,
                                            headers=self.header, method=method, data=data)
                # print(self.api)
            else:
                self.api = self.get_content(link_name,
                                            headers=self.header, method=method)
            # print(self.api.content)
            self.api = self.api.content
            # self.api = json.loads(self.api.content)

    def getByXpath(self, xpath):
        try:
            el = self.tree.xpath(xpath)
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

    def getByApi(self, key):
        try:
            el = self.api[key]
            return el
        except:
            return None

    def getHiddenValuesASP(self):
        names = self.getByXpath('//input[@type="hidden"]/@name')
        temp = {}
        for name in names:
            value = self.getByXpath(f'//input[@type="hidden"]/@name[contains(., "{name}")]/../@value')
            temp[name] = value[0] if value else ''
        return temp

    def checkTree(self):
        print(self.tree.xpath('//text()'))



    def get_overview(self, link):
        self.overview = {}
        self.setWorkingTreeApi(link, 'tree')

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
        self.extractData(requiredFieldsMap, hardCodedFields)
        return self.overview


    def extractData(self, requiredFields, hardCodedFields):
        for k, v in requiredFields.items():
            self.fillField(k, v)

        for k, v in hardCodedFields.items():
            self.overview[k] = v

    def fillField(self, fieldName, dataPath=None, reformatDate=None, el=None):
        dataType = self.getPathType(dataPath)
        if dataType == 'xpath':
            el = self.getByXpath(dataPath)
        if dataType == 'key':
            el = self.getByApi(dataPath)
        if dataType == 'defaultFill':
            el = dataPath
        if el:
            if len(el) == 1:
                el = el[0]
            el = self.reformatDate(el, reformatDate) if reformatDate else el

            if fieldName == 'isDomiciledIn':
                country = pycountry.countries.search_fuzzy(el)
                if country:
                    self.overview[fieldName] = country[0].alpha_2
                else:
                    self.overview[fieldName] = el

            elif fieldName == 'Service':
                if type(el) == list:
                    el = ', '.join(el)
                self.overview[fieldName] = {'serviceType': el}

            elif fieldName == 'vcard:organization-tradename':
                self.overview[fieldName] = el.split('\n')[0].strip()

            elif fieldName == 'bst:aka':
                names = el.split(' D/B/A ')
                if len(names) > 1:
                    names = [i.strip() for i in names]
                    self.overview[fieldName] = names
                else:
                    self.overview[fieldName] = names

            elif fieldName == 'lei:legalForm':
                self.overview[fieldName] = {
                    'code': '',
                    'label': el}

            elif fieldName == 'map':
                self.overview[fieldName] = el[0] if type(el) == list else el

            elif fieldName == 'previous_names':
                el = el.strip()
                el = el.split('\n')
                if len(el) < 1:
                    self.overview[fieldName] = {'name': [el[0].strip()]}
                else:
                    el = [i.strip() for i in el]
                    res = []
                    for i in el:
                        temp = {
                            'name': i
                        }
                        res.append(temp)
                    self.overview[fieldName] = res

            elif fieldName == 'bst:description':
                if type(el) == list:
                    el = ', '.join(el)
                self.overview[fieldName] = el

            elif fieldName == 'hasURL' and el != 'http://':
                if 'www' in el:
                    el = el.split(', ')[-1]
                if 'http:' not in el:
                    el = 'http://' + el.strip()
                if 'www' in el:
                    self.overview[fieldName] = el

            elif fieldName == 'tr-org:hasRegisteredPhoneNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

            elif fieldName =='bst:stock_info':
                if type(el) == list:
                    el = el[0]
                self.overview[fieldName] = {
                    'main_exchange': el
                }
            elif fieldName == 'agent':
                self.overview[fieldName] = {
                    'name': el.split('\n')[0],
                    'mdaas:RegisteredAddress': self.getAddress(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                                                               zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d')
                }

            elif fieldName == 'logo':
                self.overview['logo'] = self.base_url + el

            elif fieldName == 'hasRegisteredFaxNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

            else:
                self.overview[fieldName] = el

    def makeDictFromString(self, link_dict):
        link_dict = link_dict.replace("'", '"').replace("None", '"None"').replace('""', '"')
        return json.loads(link_dict)

    def reformatDate(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def getPathType(self, dataPath):
        if dataPath[:2] == '//':
            return 'xpath'
        elif dataPath == 'defaultFill':
            return 'defaultFill'
        else:
            return 'key'


    def getAddress(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.getByXpath(xpath)
        if key:
            addr = self.getByApi(key)
        if addr:
            if type(addr) == list:
                splittedAddr = addr
                addr = ', '.join(addr)

            addr = addr.replace('\n', ' ')
            addr = addr[0] if type(addr) == list else addr
            temp = {
                # 'fullAddress': addr,
                'country': splittedAddr[-2]
            }
            if zipPattern:
                zip = re.findall(zipPattern, addr)
                if zip:
                    temp['zip'] = zip[0]

            try:
                temp['zip'] = splittedAddr[-1]
            except:
                pass
            try:
                temp['city'] = splittedAddr[-3]
            except:
                pass
            try:
                temp['streetAddress'] = ' '.join(splittedAddr[:-3])
            except:
                pass
            try:
                temp['fullAddress'] = ' '.join(splittedAddr)
            except:
                pass
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            # try:
            #     street = addr.split('Street')
            #     # print(street)
            #     if len(street) == 2:
            #         temp['streetAddress'] = street[0] + 'Street'
            #     else:
            #         temp['streetAddress'] = ''.join(addr.split(',')[0:2])
            #
            #     # if temp['streetAddress']:
            #     #     temp['streetAddress'] = splitted_addr[0]
            # except:
            #     pass
            # try:
            #     # city = addr.replace(temp['zip'], '')
            #     # city = city.replace(temp['streetAddress'], '')
            #     # city = city.replace(',', '').strip()
            #     # city = re.findall('[A-Z][a-z]+', city)
            #     temp['city'] = addr.split(', ')[-1].replace('.', '')
            #     # temp['fullAddress'] += f", {temp['city']}"
            # except:
            #     pass
            # temp['fullAddress'] += f', {temp["country"]}'
            # temp['country'] = 'Nigeria'

            # temp['fullAddress'] = temp['fullAddress'].replace('.,', ',')
            if returnAddress:
                return temp
            self.overview['mdaas:RegisteredAddress'] = temp

    def getOperationalAddress(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.getByXpath(xpath)
        if key:
            addr = self.getByApi(key)
        if addr:
            if type(addr) == list:
                splittedAddr = addr
                addr = ', '.join(addr)

            addr = addr.replace('\n', ' ')
            addr = addr[0] if type(addr) == list else addr
            temp = {
                # 'fullAddress': addr,
                'country': splittedAddr[-2]
            }
            if zipPattern:
                zip = re.findall(zipPattern, addr)
                if zip:
                    temp['zip'] = zip[0]

            try:
                temp['zip'] = splittedAddr[-1]
            except:
                pass
            try:
                temp['city'] = splittedAddr[-3]
            except:
                pass
            try:
                temp['streetAddress'] = ' '.join(splittedAddr[:-3])
            except:
                pass
            try:
                temp['fullAddress'] = ' '.join(splittedAddr)
            except:
                pass
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            # try:
            #     street = addr.split('Street')
            #     # print(street)
            #     if len(street) == 2:
            #         temp['streetAddress'] = street[0] + 'Street'
            #     else:
            #         temp['streetAddress'] = ''.join(addr.split(',')[0:2])
            #
            #     # if temp['streetAddress']:
            #     #     temp['streetAddress'] = splitted_addr[0]
            # except:
            #     pass
            # try:
            #     # city = addr.replace(temp['zip'], '')
            #     # city = city.replace(temp['streetAddress'], '')
            #     # city = city.replace(',', '').strip()
            #     # city = re.findall('[A-Z][a-z]+', city)
            #     temp['city'] = addr.split(', ')[-1].replace('.', '')
            #     # temp['fullAddress'] += f", {temp['city']}"
            # except:
            #     pass
            # temp['fullAddress'] += f', {temp["country"]}'
            # temp['country'] = 'Nigeria'

            # temp['fullAddress'] = temp['fullAddress'].replace('.,', ',')
            if returnAddress:
                return temp
            self.overview['mdaas:OperationalAddress'] = temp

    def getPostAddr(self, tree):
        addr = self.getByXpath(tree, '//span[@id="lblMailingAddress"]/..//text()', return_list=True)
        if addr:
            addr = [i for i in addr if
                    i != '' and i != 'Mailing Address:' and i != 'Inactive' and i != 'Registered Office outside NL:']
            if addr[0] == 'No address on file':
                return None
            if addr[0] == 'Same as Registered Office' or addr[0] == 'Same as Registered Office in NL':
                return 'Same'
            fullAddr = ', '.join(addr)
            temp = {
                'fullAddress': fullAddr if 'Canada' in fullAddr else (fullAddr + ' Canada'),
                'country': 'Canada',

            }
            replace = re.findall('[A-Z]{2},\sCanada,', temp['fullAddress'])
            if not replace:
                replace = re.findall('[A-Z]{2},\sCanada', temp['fullAddress'])
            if replace:
                torepl = replace[0].replace(',', '')
                temp['fullAddress'] = temp['fullAddress'].replace(replace[0], torepl)
            try:
                zip = re.findall('[A-Z]\d[A-Z]\s\d[A-Z]\d', fullAddr)
                if zip:
                    temp['zip'] = zip[0]
            except:
                pass
        # print(addr)
        # print(len(addr))
        if len(addr) == 4:
            temp['city'] = addr[-3]
            temp['streetAddress'] = addr[0]
        if len(addr) == 5:
            temp['city'] = addr[-4]
            temp['streetAddress'] = addr[0]
        if len(addr) == 6:
            temp['city'] = addr[-4]
            temp['streetAddress'] = ', '.join(addr[:2])

        return temp

    def fillRegulatorAddress(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.getByXpath(xpath)[1:-2]
        if key:
            addr = self.getByApi(key)
        if addr:
            if type(addr) == list:
                addr = ', '.join(addr)
            if '\n' in addr:
                splitted_addr = addr.split('\n')
            if ', ' in addr:
                splitted_addr = addr.split(', ')

            addr = addr.replace('\n', ' ')
            addr = addr[0] if type(addr) == list else addr
            temp = {
                'fullAddress': addr,
                'country': 'USA'
            }
            if zipPattern:
                zip = re.findall(zipPattern, addr)
                if zip:
                    temp['zip'] = zip[0]
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            try:
                street = addr.split('Street')
                if len(street) == 2:
                    temp['streetAddress'] = street[0] + 'Street'
                temp['streetAddress'] = addr.split(',')[0]

                # if temp['streetAddress']:
                #     temp['streetAddress'] = splitted_addr[0]
            except:
                pass
            try:
                # city = addr.replace(temp['zip'], '')
                # city = city.replace(temp['streetAddress'], '')
                # city = city.replace(',', '').strip()
                # city = re.findall('[A-Z][a-z]+', city)
                temp['city'] = addr.split(', ')[-2].replace('.', '')
                # temp['fullAddress'] += f", {temp['city']}"
            except:
                pass
            temp['fullAddress'] += f', {temp["country"]}'
            temp['fullAddress'] = temp['fullAddress'].replace('.,', ',')
            if returnAddress:
                return temp
            self.overview['regulatorAddress'] = temp


    def getPrevNames(self, tree):
        prev = []
        names = self.getByXpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[1]/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[1]/text()',
                                return_list=True)
        dates = self.getByXpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[2]/span/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[2]/span/text()',
                                return_list=True)
        print(names)
        if names:
            names = [i for i in names if i != '']
        if names and dates:
            for name, date in zip(names, dates):
                temp = {
                    'name': name,
                    'valid_to': date
                }
                prev.append(temp)
        return prev

    def fillOverviewIdentifiers(self, xpathTradeRegistry=None, xpathOtherCompanyId=None,
                                xpathInternationalSecurIdentifier=None, xpathLegalEntityIdentifier=None):
        try:
            temp = self.overview['identifiers']
        except:
            temp = {}

        if xpathTradeRegistry:
            trade = self.getByXpath(xpathTradeRegistry)
            if trade:
                temp['trade_register_number'] = re.findall('HR.*', trade[0])[0]
        if xpathOtherCompanyId:
            other = self.getByXpath(xpathOtherCompanyId)
            if other:
                temp['other_company_id_number'] = other[0]
        if xpathInternationalSecurIdentifier:
            el = self.getByXpath(xpathInternationalSecurIdentifier)
            temp['international_securities_identifier'] = el[0]
        if xpathLegalEntityIdentifier:
            el = self.getByXpath(xpathLegalEntityIdentifier)
            temp['legal_entity_identifier'] = el[0]

        if temp:
            self.overview['identifiers'] = temp

    def fillBusinessClassifier(self, xpathCodes=None, xpathDesc=None, xpathLabels=None, api=False):
        res = []
        length = None
        codes, desc, labels = None, None, None

        if xpathCodes:
            codes = self.getByXpath(xpathCodes) if not api else [self.getByApi(xpathCodes)]
            if codes:
                length = len(codes)
        if xpathDesc:
            desc = self.getByXpath(xpathDesc) if not api else [self.getByApi(xpathDesc)]
            if desc:
                length = len(desc)
        if xpathLabels:
            labels = self.getByXpath(xpathLabels) if not api else [self.getByApi(xpathLabels)]
            if labels:
                length = len(labels)

        if length:
            for i in range(length):
                temp = {
                    'code': codes[i] if codes else '',
                    'description': desc[i] if desc else '',
                    'label': labels[i] if labels else ''
                }
                res.append(temp)
        if res:
            self.overview['bst:businessClassifier'] = res


    def fillRatingSummary(self, xpathRatingGroup=None, xpathRatings=None):
        temp = {}
        if xpathRatingGroup:
            group = self.getByXpath(xpathRatingGroup)
            if group:
                temp['rating_group'] = group[0]
        if xpathRatings:
            rating = self.getByXpath(xpathRatings)
            if rating:
                temp['ratings'] = rating[0].split(' ')[0]
        if temp:
            self.overview['rating_summary'] = temp

    def fillAgregateRating(self, xpathReview=None, xpathRatingValue=None):
        temp = {}
        if xpathReview:
            review = self.getByXpath(xpathReview)
            if review:
                temp['reviewCount'] = review[0].split(' ')[0]
        if xpathRatingValue:
            value = self.getByXpath(xpathRatingValue)
            if value:
                temp['ratingValue'] = ''.join(value)

        if temp:
            temp['@type'] = 'aggregateRating'
            self.overview['aggregateRating'] = temp

    def fillReviews(self, xpathReviews=None, xpathRatingValue=None, xpathDate=None, xpathDesc=None):
        res = []
        try:
            reviews = self.tree.xpath(xpathReviews)
            for i in range(len(reviews)):
                temp = {}
                if xpathRatingValue:
                    ratingsValues = len(self.tree.xpath(f'//async-list//review[{i + 1}]' + xpathRatingValue))
                    if ratingsValues:
                        temp['ratingValue'] = ratingsValues
                if xpathDate:
                    date = self.tree.xpath(f'//async-list//review[{i + 1}]' + xpathDate)
                    if date:
                        temp['datePublished'] = date[0].split('T')[0]

                if xpathDesc:
                    desc = self.tree.xpath(f'//async-list//review[{i + 1}]' + xpathDesc)
                    if desc:
                        temp['description'] = desc[0]
                if temp:
                    res.append(temp)
        except:
            pass
        if res:
            self.overview['review'] = res



    def get_officership(self, link):
        off = []
        self.setWorkingTreeApi(link, 'tree')
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
        ceo = self.getByXpath(
            '//text()[contains(., "CEO:")]/../following-sibling::div[1]//text()')
        founders = self.getByXpath(
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

    def getOfficerFromPage(self, link, officerType):
        self.setWorkingTreeApi(link, 'tree')
        temp = {}
        temp['name'] = self.getByXpath('//div[@class="form-group"]//strong[2]/text()')[0]

        temp['type'] = officerType
        addr = ','.join(self.getByXpath('//div[@class="MasterBorder"]//div[2]//div/text()')[:-1])
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
            self.getByXpath('//td//text()[contains(., "License Status")]/../../following-sibling::td//text()')[0]

        temp['information_source'] = self.base_url
        temp['information_provider'] = 'Idaho department of Insurance'
        return temp if temp['status'] == 'Active' else None



    def get_financial_information(self, link):
        self.setWorkingTreeApi(link, 'tree')
        total_assets = self.getByXpath('//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[2]/text()')
        revenue = self.getByXpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]/../../following-sibling::table[1]//tr[3]//td[2]/text()')
        date = self.getByXpath('//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[1]/text()')
        market_capitalization = self.getByXpath('//text()[contains(., "Market Cap ")]/../following-sibling::div[1]//text()')
        total_liabilities = self.getByXpath('//text()[contains(., "Balance Sheet Summary - in ")]/../../following-sibling::table[1]//tr[3]//td[3]/text()')
        profit = self.getByXpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]/../../following-sibling::table[1]//tr[3]//td[4]/text()')
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
            name = self.getByXpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]')
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
            name = self.getByXpath('//text()[contains(., "Annual\xa0Results - Revenue and Net Profit")]')
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
