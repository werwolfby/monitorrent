from bs4 import BeautifulSoup
import sys


def get_soup(url, parser=None):
    if parser:
        return BeautifulSoup(url, parser)
    else:
        if 'lxml' in sys.modules:              # pragma: no cover
            return BeautifulSoup(url, 'lxml')
        else:
            return BeautifulSoup(url, 'html.parser')
