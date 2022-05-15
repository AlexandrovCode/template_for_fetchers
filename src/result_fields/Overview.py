import json
import re
from datetime import datetime

import pycountry

from src.configs.source_config import Config


class Overview:
    def __init__(self, fieldsMaps, treeFetcher):
        self.treeFetcher = treeFetcher
        self.requiredFieldsMap = fieldsMaps.get('requiredFieldsMap')
        self.hardCodedFields = fieldsMaps.get('hardCodedFields')
        self.sourceConfig = Config()

    resultData = {}

    def get_result(self):
        self.extract_data()
        return self.resultData

    def extract_data(self):
        for k, v in self.requiredFieldsMap.items():
            self.fill_field(k, v)

        for k, v in self.hardCodedFields.items():
            self.resultData[k] = v

    def fill_field(self, fieldName, dataPath=None, reformatDate=None, el=None):
        dataType = self.get_path_type(dataPath)
        if dataType == 'xpath':
            el = self.treeFetcher.get_by_xpath(dataPath)
        if dataType == 'key':
            el = self.get_by_api(dataPath)
        if dataType == 'defaultFill':
            el = dataPath
        if el:
            if len(el) == 1:
                el = el[0]
            el = self.reformat_date(el, reformatDate) if reformatDate else el

            if fieldName == 'isDomiciledIn':
                country = pycountry.countries.search_fuzzy(el)
                if country:
                    self.resultData[fieldName] = country[0].alpha_2
                else:
                    self.resultData[fieldName] = el

            elif fieldName == 'Service':
                if type(el) == list:
                    el = ', '.join(el)
                self.resultData[fieldName] = {'serviceType': el}

            elif fieldName == 'vcard:organization-tradename':
                self.resultData[fieldName] = el.split('\n')[0].strip()

            elif fieldName == 'bst:aka':
                names = el.split(' D/B/A ')
                if len(names) > 1:
                    names = [i.strip() for i in names]
                    self.resultData[fieldName] = names
                else:
                    self.resultData[fieldName] = names

            elif fieldName == 'lei:legalForm':
                self.resultData[fieldName] = {
                    'code': '',
                    'label': el}

            elif fieldName == 'map':
                self.resultData[fieldName] = el[0] if type(el) == list else el

            elif fieldName == 'previous_names':
                el = el.strip()
                el = el.split('\n')
                if len(el) < 1:
                    self.resultData[fieldName] = {'name': [el[0].strip()]}
                else:
                    el = [i.strip() for i in el]
                    res = []
                    for i in el:
                        temp = {
                            'name': i
                        }
                        res.append(temp)
                    self.resultData[fieldName] = res

            elif fieldName == 'bst:description':
                if type(el) == list:
                    el = ', '.join(el)
                self.resultData[fieldName] = el

            elif fieldName == 'hasURL' and el != 'http://':
                if 'www' in el:
                    el = el.split(', ')[-1]
                if 'http:' not in el:
                    el = 'http://' + el.strip()
                if 'www' in el:
                    self.resultData[fieldName] = el

            elif fieldName == 'tr-org:hasRegisteredPhoneNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.resultData[fieldName] = el

            elif fieldName == 'bst:stock_info':
                if type(el) == list:
                    el = el[0]
                self.resultData[fieldName] = {
                    'main_exchange': el
                }
            elif fieldName == 'agent':
                self.resultData[fieldName] = {
                    'name': el.split('\n')[0],
                    'mdaas:RegisteredAddress': self.get_address(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                                                                zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d')
                }

            elif fieldName == 'logo':
                self.resultData['logo'] = self.sourceConfig.base_url + el

            elif fieldName == 'hasRegisteredFaxNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.resultData[fieldName] = el

            else:
                self.resultData[fieldName] = el

    def make_dict_from_string(self, link_dict):
        link_dict = link_dict.replace("'", '"').replace("None", '"None"').replace('""', '"')
        return json.loads(link_dict)

    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def get_path_type(self, dataPath):
        if dataPath[:2] == '//':
            return 'xpath'
        elif dataPath == 'defaultFill':
            return 'defaultFill'
        else:
            return 'key'

    def get_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.treeFetcher.get_by_xpath(xpath)
        if key:
            addr = self.get_by_api(key)
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
            self.resultData['mdaas:RegisteredAddress'] = temp

    def get_operational_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.treeFetcher.get_by_xpath(xpath)
        if key:
            addr = self.get_by_api(key)
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
            self.resultData['mdaas:OperationalAddress'] = temp

    def get_post_addr(self, tree):
        addr = self.treeFetcher.get_by_xpath(tree, '//span[@id="lblMailingAddress"]/..//text()', return_list=True)
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

    def fill_regulator_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.treeFetcher.get_by_xpath(xpath)[1:-2]
        if key:
            addr = self.get_by_api(key)
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
            self.resultData['regulatorAddress'] = temp

    def get_prev_names(self, tree):
        prev = []
        names = self.treeFetcher.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[1]/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[1]/text()',
                                  return_list=True)
        dates = self.treeFetcher.get_by_xpath(tree,
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

    def fill_overview_identifiers(self, xpathTradeRegistry=None, xpathOtherCompanyId=None,
                                  xpathInternationalSecurIdentifier=None, xpathLegalEntityIdentifier=None):
        try:
            temp = self.resultData['identifiers']
        except:
            temp = {}

        if xpathTradeRegistry:
            trade = self.treeFetcher.get_by_xpath(xpathTradeRegistry)
            if trade:
                temp['trade_register_number'] = re.findall('HR.*', trade[0])[0]
        if xpathOtherCompanyId:
            other = self.treeFetcher.get_by_xpath(xpathOtherCompanyId)
            if other:
                temp['other_company_id_number'] = other[0]
        if xpathInternationalSecurIdentifier:
            el = self.treeFetcher.get_by_xpath(xpathInternationalSecurIdentifier)
            temp['international_securities_identifier'] = el[0]
        if xpathLegalEntityIdentifier:
            el = self.treeFetcher.get_by_xpath(xpathLegalEntityIdentifier)
            temp['legal_entity_identifier'] = el[0]

        if temp:
            self.resultData['identifiers'] = temp

    def fill_business_classifier(self, xpathCodes=None, xpathDesc=None, xpathLabels=None, api=False):
        res = []
        length = None
        codes, desc, labels = None, None, None

        if xpathCodes:
            codes = self.treeFetcher.get_by_xpath(xpathCodes) if not api else [self.get_by_api(xpathCodes)]
            if codes:
                length = len(codes)
        if xpathDesc:
            desc = self.treeFetcher.get_by_xpath(xpathDesc) if not api else [self.get_by_api(xpathDesc)]
            if desc:
                length = len(desc)
        if xpathLabels:
            labels = self.treeFetcher.get_by_xpath(xpathLabels) if not api else [self.get_by_api(xpathLabels)]
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
            self.resultData['bst:businessClassifier'] = res

    def fill_rating_summary(self, xpathRatingGroup=None, xpathRatings=None):
        temp = {}
        if xpathRatingGroup:
            group = self.treeFetcher.get_by_xpath(xpathRatingGroup)
            if group:
                temp['rating_group'] = group[0]
        if xpathRatings:
            rating = self.treeFetcher.get_by_xpath(xpathRatings)
            if rating:
                temp['ratings'] = rating[0].split(' ')[0]
        if temp:
            self.resultData['rating_summary'] = temp

    def fill_agregate_rating(self, xpathReview=None, xpathRatingValue=None):
        temp = {}
        if xpathReview:
            review = self.treeFetcher.get_by_xpath(xpathReview)
            if review:
                temp['reviewCount'] = review[0].split(' ')[0]
        if xpathRatingValue:
            value = self.treeFetcher.get_by_xpath(xpathRatingValue)
            if value:
                temp['ratingValue'] = ''.join(value)

        if temp:
            temp['@type'] = 'aggregateRating'
            self.resultData['aggregateRating'] = temp

    def fill_reviews(self, xpathReviews=None, xpathRatingValue=None, xpathDate=None, xpathDesc=None):
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
            self.resultData['review'] = res

