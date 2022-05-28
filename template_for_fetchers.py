import datetime
import json
import re
import math
import urllib

import pycountry
from lxml import etree

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://kemenperin.go.id/'

    fields = ['overview',
              # 'officership',
              # 'graph:shareholders',
              # 'documents'
              # 'Financial_Information'
              ]

    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
            'q=0.8,application/signed-exchange;v=b3;q=0.9;application/json;application/json;odata=verbose',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    NICK_NAME = base_url.split('//')[-1][:-1]
    method = 'GET'
    data = None
    returnType = 'tree'

    overview = {}

    extractedData = None
    companyData = None

    fieldsConfig = {
        'vcard:organization-name': str,
        'bst:sourceLinks': list,
        'bst:registryURI': str,
        'isDomiciledIn': str,
        'hasActivityStatus': str,
        'previous_names': list,
        'bst:businessClassifier': str,
        'mdaas:RegisteredAddressAddress': str,
        'mdaas:RegisteredAddressCountry': str,
        'identifiersRegNum': str,
        'isIncorporatedIn': str,
        'lei:legalForm': str,
        'bst:registrationId': str,
        'hasURL': str,
        'mdaas:RegisteredAddressAddressEntity': dict,
        'identifiersBic': str,
        'sourceDate': str
    }

    forbiddenValues = [
        'NULL',
        'None Supplied',
        'Telp.'
    ]

    badSymbols = ['\\u00', '\\u00e9', '\\u00e0', '\\u00e8']

    complicatedFields = ['bst:businessClassifier', 'lei:legalForm', 'identifiers', 'previous_names',
                         'mdaas:RegisteredAddress']

    def getpages(self, searchquery):
        self.get_initial_page(searchquery)
        companies = self.get_result_list_by_path('//div[@class="row"]//table//tr/td[2]//b[1]//text()')
        return companies

    def get_initial_page(self, searchquery):
        searchquery = self.formatSearchQuery(searchquery)
        link = f'https://kemenperin.go.id/direktori-perusahaan?what={searchquery}'
        requestOptions = {
            'url': link,
            'method': 'GET',
            # 'headers': '',
            # 'data': data,
            # 'returnType': 'api'
        }
        self.getDataFromPage(requestOptions)

    def formatSearchQuery(self, searchquery):

        return  urllib.parse.quote_plus(searchquery)

    def getDataFromPage(self, requestOptions):
        def getUrl(self, requestOptions):
            url = requestOptions.get('url')
            if not url:
                url = self.base_url
            return url

        def getMethod(self, requestOptions):
            method = requestOptions.get('method')
            if not method:
                method = self.method
            return method

        def getHeaders(self, requestOptions):
            headers = requestOptions.get('headers')
            if not headers:
                headers = self.header
            return headers

        def getReturnType(self, requestOptions):
            returnType = requestOptions.get('returnType')
            if not returnType:
                returnType = self.returnType
            return returnType

        def getData(self, requestOptions):
            data = requestOptions.get('data')
            if not data:
                data = self.data
            return data

        url = getUrl(self, requestOptions)
        method = getMethod(self, requestOptions)
        headers = getHeaders(self, requestOptions)
        returnType = getReturnType(self, requestOptions)
        data = getData(self, requestOptions)

        content = self.get_content(url, headers, data, method).content

        if returnType == 'tree':
            self.extractedData = etree.HTML(content)
        if returnType == 'api':
            self.extractedData = json.loads(content)
        return self.extractedData

    def get_result_list_by_path(self, pathToResultList):
        outputType = self.define_output_type(pathToResultList)
        if outputType == 'api':
            return self.get_dict_value_by_path(pathToResultList, self.extractedData)
        if outputType == 'tree':
            return self.get_by_xpath(pathToResultList)

    def define_output_type(self, path):
        if path[:2] == '//':
            return 'tree'
        return 'api'

    def get_dict_value_by_path(self, path, dictData):
        resultValue = dict(dictData)
        path = path.split('/')
        if path == ['']:
            return [self.extractedRawDict]
        for i in path:
            if type(resultValue) == list:
                resultValue = resultValue[0]
            try:
                resultValue = resultValue[i]
            except Exception as e:
                # print(e)
                return None
        return resultValue

    def get_companies_value(self, linkPath, listData):
        companyLinks = []
        for company in listData:
            x = self.get_dict_value_by_path(linkPath, company)
            if x:
                companyLinks.append(x)
        return companyLinks

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

    def get_overview(self, link):
        path = f"//div[@class='row']//table//tr/td[2]//b[1]//text()[contains(., '{link}')]/../../.."
        companyInformation = self.find_company_on_the_page(path)

        link = 'https://aleph.occrp.org/api/2/entities/' + link

        def extraHandlingCode(code):
            return code.split(' - ')[0]

        def extraHandlingDescription(description):
            return description.split(' - ')[-1]

        def extraHandlingLabel(description):
            return description

        def extraHandlingLeiLabel(label):
            if label == '':
                return 'Sole'
            return label[2:]

        def extraHandlingIsIncorporatedIn(date):
            return date.split('T')[0]

        def extraHandlingPhone(phone):
            phone = phone.split('Telp.')[-1]
            if phone:
                return phone[1:]

        def extraHandlingCountry(country):
            if country == '':
                return 'Indonesia'

        def extraHandlingStreetAddress(addr):
            add = addr.split(', ')
            if add:
                return add[0]
            else:
                return ''

        def extraHandlingCity(addr):
            add = addr.split(', ')
            if add:
                return add[-1]
            else:
                return ''

        def extraHandlingFullAddress(fullAddress):
            return fullAddress + ', Indonesia'


        fetchedFields = {
            'vcard:organization-name': './td[2]//b[1]//text()',
            'tr-org:hasRegisteredPhoneNumber': ['./td[2]//text()[2]', extraHandlingPhone, None, None],
            # 'isDomiciledIn': 'properties/jurisdiction',
            # 'bst:sourceLinks': 'links/self',
            # 'hasActivityStatus': './td[2]/text()',
            # 'previous_names': [{'name': 'properties/previousName',
            #                            },
            #                            [None],
            #                            'list',
            #                            'notShowEmpty'],
            # 'hasURL': 'properties/website',
            # 'bst:businessClassifier': [{'code': 'properties/classification',
            #                            'description': 'properties/classification',
            #                            'label': '',
            #                            },
            #                            [extraHandlingCode, extraHandlingDescription, extraHandlingLabel],
            #                            'list',
            #                            'showEmpty'],
            'mdaas:RegisteredAddress': [{
                'country': '',
                'streetAddress': './td[2]/b/following-sibling::text()[1]',
                'city': './td[2]/b/following-sibling::text()[1]',
                'fullAddress': './td[2]/b/following-sibling::text()[1]'
                # 'entityAddress': 'properties/addressEntity/properties',
                # 'fullAddress': './span/u/text()[contains(., "Forme juridique")]/../following-sibling::text()[2]'
            },
                [
                 extraHandlingCountry,
                 extraHandlingStreetAddress,
                 extraHandlingCity,
                 extraHandlingFullAddress,
                ],
                '',
                'notShowEmpty'],
            # 'mdaas:RegisteredAddressCountry': 'properties/country',
            # 'mdaas:RegisteredAddressAddress': 'properties/address',
            # 'mdaas:RegisteredAddressAddressEntity': 'properties/addressEntity/properties',
            # 'identifiers': [{
            #     # 'swift_code': 'properties/swiftBic',
            #     'other_company_id_number': './td[3]/text()',
            # }, [
            #     # None,
            #     None], '', 'notShowEmpy'],
            # 'isIncorporatedIn': ['./td[5]/span/@content', extraHandlingIsIncorporatedIn, None, None],
            # 'lei:legalForm': [{'code': '',
            #                            # 'description': 'properties/classification',
            #                            'label': './span/u/text()[contains(., "Forme juridique")]/../following-sibling::text()[1]',
            #                            }, [None, extraHandlingLeiLabel], '', 'showEmpty'],
            # 'bst:registryURI': 'links/self',
            # 'bst:registrationId': 'properties/registrationNumber',
            # 'sourceDate': 'properties/modifiedAt'
        }
        # print(companyInformation.xpath('./td[2]/b/following-sibling::text()[1]'))
        # exit()
        hardcodedFields = {
            '@source-id': self.base_url,
            'isDomiciledIn': 'ID',
            'regulator_name': 'Kementerian Perindustrian REPUBLIK INDONESIA',
            'regulator_url': self.base_url,
            'RegulationStatus': 'Authorised',
            'regulatorAddress': {
                'fullAddress': 'Jl. Gatot Subroto Kav. 52-53 Jakarta Selatan 12950, Indonesia',
                'city': 'Jakarta',
                'country': 'Indonesia'
            }
            # 'bst:sourceLinks': ['http://www.gufebenin.org/index.php/entreprises'],
        }

        self.extract_data(fetchedFields, hardcodedFields, companyInformation)

        return self.overview

    def find_company_on_the_page(self, path):
        elementWithInfo = self.extractedData.xpath(path)
        if elementWithInfo:
            return self.extractedData.xpath(path)[0]
        else:
            return None

    def extract_data(self, fetchedFields, hardCodedFields, companyInformation):
        self.extractedData = companyInformation
        for k, v in fetchedFields.items():
            self.fill_field(k, v)

        for k, v in hardCodedFields.items():
            self.overview[k] = v

    def fill_field(self, fieldName, data=None, reformatDate=None, el=None):
        if type(data) == str:
            handlingFunctions = None
            dataPath = data
        if type(data) == list:
            dataPath = data[0]
            handlingFunctions = data[1]
            returnType = data[2]
            showEmpty = data[3]

        dataType = self.get_path_type(dataPath)

        if fieldName in self.complicatedFields:
            self.fill_dictionary_field(dataPath, handlingFunctions, fieldName, returnType, showEmpty, dataType)
            return

        elif dataType == 'tree':
            el = self.get_by_xpath(dataPath)
        elif dataType == 'key':
            el = self.get_dict_value_by_path(dataPath, self.extractedData)
        else:
            el = dataPath
        el = self.getCleanValues(el)
        if el:
            if len(el) == 1 and type(el) == list:
                el = el[0]
            el = self.reformat_date(el, reformatDate) if reformatDate else el
            el = handlingFunctions(el) if handlingFunctions else el


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
                self.overview[fieldName] = self.get_formatted_previous_names(el)

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

            elif fieldName == 'bst:stock_info':
                if type(el) == list:
                    el = el[0]
                self.overview[fieldName] = {
                    'main_exchange': el
                }
            elif fieldName == 'agent':
                self.overview[fieldName] = {
                    'name': el.split('\n')[0],
                    'mdaas:RegisteredAddress': self.get_address(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                                                                zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d')
                }

            elif fieldName == 'logo':
                self.overview['logo'] = self.sourceConfig.base_url + el

            elif fieldName == 'hasRegisteredFaxNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

            elif fieldName == 'bst:sourceLinks':
                self.overview[fieldName] = [el]

            elif fieldName == 'bst:businessClassifier':
                self.overview[fieldName] = [el]

            else:
                self.overview[fieldName] = el

    def formatFields(self, fieldsData):
        cleanFormattedResult = {}
        for field, fieldValue in fieldsData.items():
            # print('FORMAT FIELDS', field, fieldValue)
            if self.config[field] == str and type(fieldValue) == list:
                cleanFormattedResult[field] = fieldValue[0]
            elif self.config[field] == list and type(fieldValue) == str:
                cleanFormattedResult[field] = [fieldValue]
            else:
                cleanFormattedResult[field] = fieldValue

            if field == 'previous_names':
                cleanFormattedResult[field] = self.get_formatted_previous_names(fieldValue)
            if field == 'lei:legalForm':
                cleanFormattedResult[field] = self.get_formatted_lei(cleanFormattedResult[field])
            if field == 'bst:businessClassifier':
                cleanFormattedResult[field] = self.get_formatted_busClassifier(cleanFormattedResult[field])
            if field == 'mdaas:RegisteredAddressCountry':
                cleanFormattedResult[field] = cleanFormattedResult[field].upper()

            if field == 'mdaas:RegisteredAddressAddress':
                cleanFormattedResult['mdaas:RegisteredAddress'] = self.get_formatted_address(
                    cleanFormattedResult[field], cleanFormattedResult['mdaas:RegisteredAddressCountry'])

            if field == 'mdaas:RegisteredAddressAddressEntity':
                cleanFormattedResult['mdaas:RegisteredAddress'] = self.get_address_from_entity(
                    cleanFormattedResult[field])

            if field == 'identifiersBic':
                try:
                    cleanFormattedResult['identifiers'] = self.get_formatted_identifiers(cleanFormattedResult[field],
                                                                                         cleanFormattedResult[
                                                                                             'bst:registrationId'])
                except:
                    cleanFormattedResult['identifiers'] = self.get_formatted_identifiers(cleanFormattedResult[field])

        # print(fieldsData)
        return cleanFormattedResult

    def get_formatted_address(self, address=None, country=None, addrEntity=None):

        if address:
            address = address[0]
            country = country[0]
            temp = {}
            try:
                temp = {'country': self.get_country_name_by_iso_code(country)}
                zip = re.findall('[A-Z\d]{4} \d[A-Z]{2}', address)
                temp['zip'] = zip[0]
            except:
                pass

            try:
                city = address.split(', ')[-2]
                temp['city'] = city
            except:
                pass

            try:
                streetAddress = address.split(city)[0]
                temp['streetAddress'] = streetAddress[:-2]
            except:
                pass

            try:
                temp['fullAddress'] = address + ', ' + country
            except:
                pass
            return temp
        if addrEntity:
            return self.get_address_from_entity(addrEntity)
        return {}

    def get_address_from_entity(self, entityAddress):
        try:
            temp = {
                'city': entityAddress['city'][0],
                'country': self.get_country_name_by_iso_code(entityAddress['country'][0]),
                'streetAddress': entityAddress['street'][0],
                'fullAddress': entityAddress['full'][0],
            }
        except:
            pass
        return temp

    def get_country_name_by_iso_code(self, isoCode):
        countryName = pycountry.countries.get(alpha_2=isoCode)
        return countryName.name

    def make_dict_from_string(self, link_dict):
        link_dict = link_dict.replace("'", '"').replace("None", '"None"').replace('""', '"')
        return json.loads(link_dict)

    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def get_path_type(self, dataPath):
        if type(dataPath) == list:
            dataPath = dataPath[0]
        if type(dataPath) == dict:
            dataPath = list(dataPath.values())
            dataPath = [i for i in dataPath if i != '']
            if dataPath:
                dataPath = dataPath[0]
        if '/' in dataPath[:2]:
            return 'tree'
        elif not dataPath:
            return 'rawElement'
        else:
            return 'api'

    def get_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.get_by_xpath(xpath)
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
            self.overview['mdaas:RegisteredAddress'] = temp

    def get_operational_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.get_by_xpath(xpath)
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
            self.overview['mdaas:OperationalAddress'] = temp

    def get_post_addr(self, tree):
        addr = self.get_by_xpath(tree, '//span[@id="lblMailingAddress"]/..//text()', return_list=True)
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
            addr = self.get_by_xpath(xpath)[1:-2]
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
            self.overview['regulatorAddress'] = temp

    def get_prev_names(self, tree):
        prev = []
        names = self.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[1]/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[1]/text()',
                                  return_list=True)
        dates = self.get_by_xpath(tree,
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
            temp = self.overview['identifiers']
        except:
            temp = {}

        if xpathTradeRegistry:
            trade = self.get_by_xpath(xpathTradeRegistry)
            if trade:
                temp['trade_register_number'] = re.findall('HR.*', trade[0])[0]
        if xpathOtherCompanyId:
            other = self.get_by_xpath(xpathOtherCompanyId)
            if other:
                temp['other_company_id_number'] = other[0]
        if xpathInternationalSecurIdentifier:
            el = self.get_by_xpath(xpathInternationalSecurIdentifier)
            temp['international_securities_identifier'] = el[0]
        if xpathLegalEntityIdentifier:
            el = self.get_by_xpath(xpathLegalEntityIdentifier)
            temp['legal_entity_identifier'] = el[0]

        if temp:
            self.overview['identifiers'] = temp

    def fill_dictionary_field(self, dataPaths, handlingFunctions, fieldName, returnType=None, showEmpty=None,
                              dataType=None):
        dictKeys = list(dataPaths.keys())
        paths = []
        for key in dictKeys:
            dataType = self.get_path_type(dataPaths.get(key))
            if dataPaths.get(key):
                paths.append(dataPaths.get(key))
            elif dataType == 'rawElement':
                paths.append(dataPaths.get(key))
            else:
                paths.append(None)

        res = []
        length = None

        results = []

        for path in paths:
            if path is not None:
                dataType = self.get_path_type(path)
                if dataType == 'tree':
                    element = self.get_by_xpath(path)
                elif dataType == 'rawElement':
                    element = ['']
                    length = 1
                else:
                    element = self.get_dict_value_by_path(path, self.extractedData)
                element = self.getCleanValues(element)
                results.append(element)
                if element:
                    length = len(element)
            else:
                results.append(None)
        if length:
            for i in range(length):
                temp = {}
                for subFieldIndex in range(len(dictKeys)):
                    if handlingFunctions[subFieldIndex] is not None:
                        finalRes = handlingFunctions[subFieldIndex](results[subFieldIndex][i]) if results[
                            subFieldIndex] is not None else ''
                    else:
                        finalRes = results[subFieldIndex][i] if results[subFieldIndex] else ''

                    if showEmpty == 'showEmpty' or finalRes is not None:
                        temp[dictKeys[subFieldIndex]] = finalRes
                res.append(temp)
        if res:
            if returnType == 'list':
                self.overview[fieldName] = res
            else:
                self.overview[fieldName] = res[0]

    def fill_leiLegalForm(self, dataPaths, api=False):
        pass

    def fill_rating_summary(self, xpathRatingGroup=None, xpathRatings=None):
        temp = {}
        if xpathRatingGroup:
            group = self.get_by_xpath(xpathRatingGroup)
            if group:
                temp['rating_group'] = group[0]
        if xpathRatings:
            rating = self.get_by_xpath(xpathRatings)
            if rating:
                temp['ratings'] = rating[0].split(' ')[0]
        if temp:
            self.overview['rating_summary'] = temp

    def fill_agregate_rating(self, xpathReview=None, xpathRatingValue=None):
        temp = {}
        if xpathReview:
            review = self.get_by_xpath(xpathReview)
            if review:
                temp['reviewCount'] = review[0].split(' ')[0]
        if xpathRatingValue:
            value = self.get_by_xpath(xpathRatingValue)
            if value:
                temp['ratingValue'] = ''.join(value)

        if temp:
            temp['@type'] = 'aggregateRating'
            self.overview['aggregateRating'] = temp

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
            self.overview['review'] = res

    def get_mapped_required_data(self, config, dictionary=None):
        mappedResults = {}
        if dictionary:
            for k, v in config.items():
                x = self.get_dict_value_by_path(v, dictionary)
                if x:
                    # print(k, v, x,)
                    mappedResults[k] = x
            return mappedResults
        for company in self.companiesData:
            for k, v in config.items():
                x = self.get_dict_value_by_path(v, company)
                if x:
                    # print(k, v, x,)
                    mappedResults[k] = x
        return mappedResults

    def get_company_value(self, linkPath):
        companyLinks = []
        for company in self.companiesData:
            x = self.get_dict_value_by_path(linkPath, company)
            if x:
                companyLinks.append(x)
        return companyLinks

    def get_officership(self, link):
        off = []
        link = 'https://aleph.occrp.org/api/2/entities/' + link
        expandedLink = link + '/expand'
        self.apiFetcher.extract_data(expandedLink)
        self.apiFetcher.transfer_to_json()
        y = self.apiFetcher.get_companies_list_by_path('results')
        for i in y:
            if i['property'] == 'ownershipAsset':
                entities = i['entities']
                for ent in entities:
                    if ent['schema'] == 'LegalEntity':
                        owner = ent['properties']['name']
                        off.append({'name': owner[0],
                                    'type': 'individual',
                                    'officer_role': 'owner',
                                    'status': 'Active',
                                    'occupation': 'owner',
                                    # 'information_source': self.base_url,
                                    # 'information_provider': 'Value Today'
                                    })
        return off

    def get_documents(self, link):
        docs = []
        link2 = f'https://aleph.occrp.org/api/2/entities?filter%3Aproperties.resolved={link}&filter%3Aschemata=Mention&limit=30'
        self.apiFetcher.extract_data(link2)
        self.apiFetcher.transfer_to_json()
        y = self.apiFetcher.get_companies_list_by_path('results')
        for doc in y:
            name = doc['properties']['document'][0]['properties']['fileName']
            link = doc['properties']['document'][0]['id']
            link = self.base_url + '/entities/' + link
            docs.append({
                'description': name[0],
                'url': link
            })

        return docs

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

    def getCleanValues(self, values):
        cleanValues = []
        if type(values) == list:
            for value in values:
                if not self.isForbiddenValue(value):
                    value = self.removeBadSymbols(value)
                    cleanValues.append(value)
        else:
            if not self.isForbiddenValue(values):
                value = self.removeBadSymbols(values)
                return value
        return cleanValues

    def isForbiddenValue(self, value):
        return value in self.forbiddenValues

    def removeBadSymbols(self, value):
        string_encode = value.encode("ascii", "ignore")
        string_decode = string_encode.decode()
        return string_decode
