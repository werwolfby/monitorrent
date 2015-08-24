from bs4 import BeautifulSoup
import sys


def get_soup(url, settings=None):
    if settings and settings.html_parser:
        return BeautifulSoup(url, settings.html_parser)
    else:
        if 'lxml' in sys.modules:
            return BeautifulSoup(url, 'lxml')
        else:
            return BeautifulSoup(url, 'html.parser')
