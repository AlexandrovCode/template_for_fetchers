from src.bstsouecepkg.extract import GetPages
from abc import ABC


class BaseFetcher(ABC, GetPages):
    extractedData = None

    def __init__(self, fetcherConfig):
        super().__init__()
        self.link = fetcherConfig.get('link')
        self.header = fetcherConfig.get('header')
        self.method = fetcherConfig.get('method')
        self.data = fetcherConfig.get('data')
        self.extract_data()

    def extract_data(self, link=None):
        if not link:
            link = self.link

        self.extractedData = self.get_content(link, headers=self.header, method=self.method, data=self.data)

    def transform_data(self):
        pass
