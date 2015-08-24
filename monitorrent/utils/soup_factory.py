from bs4 import BeautifulSoup
import sys


class SoupFactory(object):
    def __init__(self, settings=None):
        self.settings = settings

    def get_soup(self, url):
        if self.settings and self.settings.html_parser:
            return BeautifulSoup(url, self.settings.html_parser)
        else:
            if 'lxml' in sys.modules:
                return BeautifulSoup(url, 'lxml')
            else:
                return BeautifulSoup(url, 'html.parser')
