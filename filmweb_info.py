#!/usr/bin/python3

import beeprint
import json
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import time

from bs4 import BeautifulSoup

class MovieInfo:
    def __init__(self):
        self.id = None
        self.url = None
        self.title = None
        self.search_title = None
        self.orig_title = None
        self.year = None
        self.rating = None
        self.desc = None
        self.director = None
        self.genres = []
        self.countries = []

def get_info(film_id):
    url = f'http://www.filmweb.pl/Film?id={film_id}'
    print('  processing: ' + url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    m = MovieInfo()
    m.id = film_id
    m.url = url

    try:
        m.title = soup.find(
                        "h1", attrs={"class":"filmCoverSection__title"}).text
    except:
        print('  FAILED: title')
        m.title = None

    try:
        m.orig_title = soup.find(
                "div", attrs={"class":"filmCoverSection__originalTitle"}).text
    except:
        print('  FAILED: orig_title')
        m.orig_title = None

    try:
        m.year = soup.find("div", attrs={"class":"filmCoverSection__year"}).text
    except:
        print('  FAILED: year')
        m.year = None

    try:
        m.rating = soup.find("span", attrs={"class":"filmRating__rateValue"}).text
    except:
        print('  FAILED: rating')
        m.rating = None

    try:
        m.desc = soup.find("div", attrs={"class":"filmPosterSection__plot"})\
                .find("span", itemprop="description")\
                .text
    except:
        print('  FAILED: desc')
        m.desc = None

    try:
        m.director = soup.find("div", attrs={"data-type":"directing-info"})\
                .find("span", itemprop="name")\
                .text
    except:
        print('  FAILED: director')
        m.director = None

    try:
        m.genres = [e.find("span").text for e in soup.find(
                "div", attrs={"class":"filmInfo__info", "itemprop":"genre"})\
                        .find_all("a")]
    except:
        print('  FAILED: genres')
        m.genres = None

    try:
        m.countries = [e.text for e in soup.find(
                "span", attrs={"data-i18n":"film:label.production_country"})\
                .find_all_next("span",
                      attrs={"data-i18n":re.compile("entity@country")})]
    except:
        print('  FAILED: countries')
        m.countries = None

    return m

class MovieFinder:
    def get_id(self, title):
        url = f'https://www.filmweb.pl/search#/?query={title}'

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        self.browser = webdriver.Firefox(options=options)

        try:
            self.browser.get(url)

            timeout_in_seconds = 10
            WebDriverWait(self.browser, timeout_in_seconds)\
                    .until(EC.element_to_be_clickable((By.CLASS_NAME,
                                                           'searchApp__results')))
            time.sleep(1)  # just in case, sometimes too fast
            soup = BeautifulSoup(self.browser.page_source, features='html.parser')
        finally:
            self.browser.quit()

        lst = soup.find("div", attrs={"class":"searchApp__results"})\
                .find_all("div", attrs={"class":"ribbon",
                                        "data-entity-name":"film", "data-id":re.compile("[0-9]+")})
        return [e.get('data-id') for e in lst]


if __name__ == '__main__':
    finder = MovieFinder()
    data = []
    
    # Read from STDIN
    for title in sys.stdin:
        title = title.strip()
        print(f'Searching for: "{title}"')
        ids = finder.get_id(title)
        print('  ' + ', '.join(ids))

        for id in ids:
            try:
                m = get_info(id)
            except:
                print('FAILED')
                m = MovieInfo()
                raise
            m.search_title = title
            data.append(m.__dict__)

    with open("database.json", "w") as outfile:
        outfile.write(json.dumps(data, indent=4))

