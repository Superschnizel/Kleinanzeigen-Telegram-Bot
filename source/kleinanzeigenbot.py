import requests
import re
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

class KleinanzeigenItem:

    def __init__(self, article) -> None:
        self.url = article['data-href']
        self.id = self.url.split('/')[-1]
        main = article.find('div', {'class' : 'aditem-main'})
        self.title = main.a.string
        self.location = main.find('div', {'class' : "aditem-main--top--left"}).text.replace('\n', '')
        self.price = main.find('p', {'class' : "aditem-main--middle--price-shipping--price"}).string.replace('\n', '').replace(' ', '')

    def __eq__(self, __value: object) -> bool:
        return self.url == __value.url
    
    def __str__(self) -> str:
        out_str = self.url + '\n' 
        out_str += self.title + '\n' 
        out_str += self.price + ' - ' 
        out_str += self.location
        return out_str
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def check_filters(self, filters):
        for pattern in filters:
            # Use re.search with IGNORECASE flag to check if the pattern matches self.url case-insensitively
            if re.search(pattern, self.url, re.IGNORECASE):
                return False  # Return False if a match is found
        
        return True

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
            # self.mainSet.add(article.a['href'])
            self.mainSet.add(KleinanzeigenItem(article))

        self.invalid_link_flag = len(self.mainSet) <= 0

    def get_new_articles(self) -> set[KleinanzeigenItem]:
        response = requests.get(
            self.url,
            headers=self.headers,
            timeout=5,
            allow_redirects=False
        )
        data = BeautifulSoup(response.text, 'html.parser')

        newSet = set()
        for article in data.find_all('article'):
            # newSet.add(article.a['href'])
            newSet.add(KleinanzeigenItem(article))
        
        newArticles = newSet.difference(self.mainSet)
        self.mainSet = self.mainSet.union(newArticles)

        return newArticles
    
    def show_articles(self) -> None:
        for item in self.mainSet:
            print(item)
    
    def num_items(self):
        return len(self.mainSet)

    

        


if __name__ == '__main__':
    bot = KleinanzeigenBot(TEST_URL, 'test')

    bot.show_articles()


