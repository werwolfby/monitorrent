from bs4 import BeautifulSoup
import sys


def get_soup(url, html_parser=None):
    if html_parser:
        return BeautifulSoup(url, html_parser)
    else:
        if 'lxml' in sys.modules:
            return BeautifulSoup(url, 'lxml')
        else:
            return BeautifulSoup(url, 'html.parser')
