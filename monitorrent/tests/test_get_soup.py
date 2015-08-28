import sys
from monitorrent.tests import TestCase
from monitorrent.utils.soup import get_soup
# noinspection PyProtectedMember
from bs4.builder._htmlparser import HTMLParserTreeBuilder
# noinspection PyProtectedMember
from bs4.builder._lxml import LXMLTreeBuilder
# noinspection PyProtectedMember
from bs4.builder._html5lib import HTML5TreeBuilder


class GetSoupTest(TestCase):
    CONTENT = """
    <HTML>
    <HEAD>
        <title>The Title</title>
    </HEAD>
    <BODY>
        <ul>
            <li>Value 1
            <li>Value 2
            <li>Value 3
        </ul>
    </BODY>
    </HTML>
    """

    def test_default_not_lxml_parser(self):
        lxml_module = sys.modules.get('lxml', None)
        if 'lxml' in sys.modules:
            del sys.modules['lxml']

        try:
            soup = get_soup(self.CONTENT)

            self.assertIsNotNone(soup)
            self.assertTrue(isinstance(soup.builder, HTMLParserTreeBuilder))
        finally:
            if lxml_module:
                sys.modules['lxml'] = lxml_module

    def test_default_lxml_parser(self):
        soup = get_soup(self.CONTENT)

        self.assertIsNotNone(soup)
        self.assertTrue(isinstance(soup.builder, LXMLTreeBuilder))

    def test_direct_html5lib_parser(self):
        soup = get_soup(self.CONTENT, 'html5lib')

        self.assertIsNotNone(soup)
        self.assertTrue(isinstance(soup.builder, HTML5TreeBuilder))

    def test_direct_lxml_parser(self):
        soup = get_soup(self.CONTENT, 'lxml')

        self.assertIsNotNone(soup)
        self.assertTrue(isinstance(soup.builder, LXMLTreeBuilder))
