# coding=utf-8
import falcon
from ddt import ddt, data
from mock import patch, mock_open, MagicMock
from monitorrent.rest.static_file import StaticFiles
from monitorrent.tests import RestTestBase


@ddt
class TestStaticFiles(RestTestBase):
    @data(u'<HTML></HTML>', u'<HTML>Other text</HTML>')
    def test_static_index(self, index_text):
        # with not ascii chars in index_text test fails on travis-ci
        m = mock_open(read_data=index_text)
        getsize = MagicMock(return_value=len(index_text))
        with patch("monitorrent.rest.static_file.open", m, create=True), \
             patch("monitorrent.rest.static_file.os.path.getsize", getsize, create=True):
            s = StaticFiles('folder', 'index.html', False)
            self.api.add_route('/index.html', s)

            body = self.simulate_request('/index.html')
            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertEqual('text/html', self.srmock.headers_dict['content-type'])
            self.assertEqual(str(len(index_text)), self.srmock.headers_dict['content-length'])
            self.assertEqual(unicode(body.next()), index_text)

    def test_redirect_to_login(self):
        index_text = '<HTML></HTML>'
        m = mock_open(read_data=index_text)
        getsize = MagicMock(return_value=len(index_text))
        with patch("monitorrent.rest.static_file.open", m, create=True), \
             patch("monitorrent.rest.static_file.os.path.getsize", getsize, create=True):
            s = StaticFiles('folder', 'index.html')
            self.api.add_route('/index.html', s)

            self.simulate_request('/index.html')
            self.assertEqual(self.srmock.status, falcon.HTTP_FOUND)
            self.assertEqual('/login', self.srmock.headers_dict['location'])
