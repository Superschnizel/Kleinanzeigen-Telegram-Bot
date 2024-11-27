from io import BytesIO
import certifi
import pycurl
import re
from bs4 import BeautifulSoup

DEFAULT_HEADERS = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"]

TEST_URL = "https://www.kleinanzeigen.de/s-wohnung-mieten/berlin/preis::1000/c203l3331+wohnung_mieten.verfuegbarm_i:10%2C+wohnung_mieten.verfuegbary_i:2023%2C"


class KleinanzeigenItem:

    def __init__(self, article) -> None:
        self.url = article["data-href"]
        self.id = self.url.split("/")[-1]

        main = article.find("div", {"class": "aditem-main"})
        if main is None:
            print("main object of article could not be found")
            return
        location = main.find("div", {"class": "aditem-main--top--left"}).text
        price = main.find("p", {"class": "aditem-main--middle--price-shipping--price"}).text

        self.title = main.find("h2", {"class": "text-module-begin"}).text
        self.location = location.replace("\n", "") if location is not None else "location unknown"
        self.price = price.replace("\n", "").replace(" ", "") if price is not None else "? €"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, KleinanzeigenItem) and self.url == __value.url

    def __str__(self) -> str:
        out_str = self.url + "\n"
        out_str += self.title + "\n"
        out_str += self.price + " - "
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
    """
    Bot that querries a specified link and returns new articles if found
    """

    def __init__(self, url: str, name: str) -> None:
        self.name = name
        self.url = url

        data = self.get_site_curl()

        self.mainSet = set()

        for article in data.find_all("article"):
            # self.mainSet.add(article.a['href'])
            self.mainSet.add(KleinanzeigenItem(article))

        self.invalid_link_flag = len(self.mainSet) <= 0

    def get_new_articles(self) -> set[KleinanzeigenItem]:
        data = self.get_site_curl()

        newSet = set()
        for article in data.find_all("article"):
            # newSet.add(article.a['href'])
            newSet.add(KleinanzeigenItem(article))

        newArticles = newSet.difference(self.mainSet)
        self.mainSet = self.mainSet.union(newArticles)

        return newArticles

    def get_site_curl(self) -> BeautifulSoup:
        """
        Get the site contents using curl and return the parsed html.

        :return: the parsed DOM tree
        """
        buffer = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, self.url)
        curl.setopt(pycurl.WRITEDATA, buffer)
        curl.setopt(pycurl.HTTPHEADER, DEFAULT_HEADERS)
        curl.setopt(pycurl.CAINFO, certifi.where())  # to be able to use HTTPS

        curl.perform()
        curl.close()

        body = buffer.getvalue().decode()

        return BeautifulSoup(body, "html.parser")

    def show_articles(self) -> None:
        for item in self.mainSet:
            print(item)

    def num_items(self):
        return len(self.mainSet)


if __name__ == "__main__":
    bot = KleinanzeigenBot(TEST_URL, "test")

    bot.show_articles()
