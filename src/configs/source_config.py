class Config:
    base_url = 'https://www.value.today'

    fields = ['overview',
              'officership',
              # 'graph:shareholders',
              # 'documents'
              'Financial_Information']

    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
            'q=0.8,application/signed-exchange;v=b3;q=0.9;application/json;application/json;odata=verbose',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    NICK_NAME = base_url.split('//')[-1]
