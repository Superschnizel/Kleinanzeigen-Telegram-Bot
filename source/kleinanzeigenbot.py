import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

TEST_URL = 'https://www.kleinanzeigen.de/s-wohnung-mieten/berlin/preis::1000/c203l3331+wohnung_mieten.verfuegbarm_i:10%2C+wohnung_mieten.verfuegbary_i:2023%2C'

class KleinanzeigenBot:

    def __init__(self, url: str, name :str) -> None:
        self.name = name
        self.url = url
        self.headers = DEFAULT_HEADERS

        response = requests.get(
            self.url,
            headers=self.headers,
            timeout=5,
            allow_redirects=False
        )
        data = BeautifulSoup(response.text, 'html.parser')

        self.mainSet = set()

        for article in data.find_all('article'):
            self.mainSet.add(article.a['href'])

        self.invalid_link_flag = len(self.mainSet) <= 0

    def get_new_articles(self) -> set:
        response = requests.get(
            self.url,
            headers=self.headers,
            timeout=5,
            allow_redirects=False
        )
        data = BeautifulSoup(response.text, 'html.parser')

        newSet = set()
        for article in data.find_all('article'):
            newSet.add(article.a['href'])
        
        newArticles = newSet.difference(self.mainSet)
        self.mainSet = newSet

        return newArticles
