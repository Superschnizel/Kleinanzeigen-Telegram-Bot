import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from time import sleep

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

TEST_URL = "https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten?price=-700.0&exclusioncriteria=swapflat&pricetype=rentpermonth&sorting=2&enteredFrom=result_list"

COOKIES = { 'reese84' :	"3:JNtZd7C2oJH0fcNG8zkFaQ==:WxRagEbEQmMv6NsC9qGv8gHk3SKNB1Yu8pm6ePM3kRbdeADxpNufmc0YkPpKlYXg7Y1wNvHOgel9t2al5TMzR7TQWU1kMUs7hCHAz7JfcX1Ai3npvhIlpQOH+dF3oelOtEyHfJX12o77HOdgPJvgZx8QrAJF8DPR46U0H+sp5OHPNMbUQsHb3YPkUFlX/1+4bfcidfPf3iA/mhBaSwaNBNkt8eOpSL9Gm3Q5Dbz6/C8yX1hDSE3kWw/1TfXXe/Xa3Yf6dZSVY1O9UpRC47IPy3hl91aGq9IIYLfANPj87le5zoNSUVd+o5Hv7S/XUQYJFkhXXtuLomfc11z8gb/0CGZhVlgUMaoC8PKGQDLGm6Jy3NqnfT8uAErr40yFb+vZL3vGXS1sBCMAgecsT7027gtN1pbnGTZd3tQxhbSKpjI7gCKx3F0ASkQ7+LZUcgQLWS50bMtI6pO9K/jk7GgF5A+H1ls+fzRppiRiX2wFsM6g6H9f4myqTyq7BvyEWUFo5IiOd+7ipbjwKcfgLHTvsw==:lQME6mUdkH4ovgaCqlcSnJt37lBsdfreJ61XcSSf6Co="}

class ImmoscoutBot:

    def __init__(self, url: str, name: str) -> None:
        self.name = name
        self.url = url
        self.headers = DEFAULT_HEADERS

        response = requests.get(
                self.url,
                headers=self.headers,
                timeout=5,
                cookies= COOKIES,
                allow_redirects=False
            )
        data = BeautifulSoup(response.text, 'html.parser')

        # print(data.prettify())

        self.mainSet = set()

        for article in data.find_all('article'):
            print(article['id'])

        self.invalid_link_flag = len(self.mainSet) <= 0


def TestConnection():
    i = 0
    while True:
        response = requests.get(
                TEST_URL,
                headers=DEFAULT_HEADERS,
                timeout=5,
                cookies= COOKIES,
                allow_redirects=False
            )
        data = BeautifulSoup(response.text, 'html.parser')

        if len(data.find_all('article')) <= 0:
            print(f'Failed to get items after {i} successes')
            return
        
        i += 1
        print(f'succes, number {i}')

        sleep(120)

        




if __name__ == '__main__':
    # bot = ImmoscoutBot(TEST_URL, 'test')
    
    TestConnection()

    # driver = uc.Chrome(headless=True, use_subprocess=False, no_sandbox=False)

    # driver.get(TEST_URL)

    # print(driver.page_source)