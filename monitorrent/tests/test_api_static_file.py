# coding=utf-8
import os
import time
from collections import namedtuple
import falcon
from ddt import ddt, data
from mock import patch, mock_open, MagicMock, Mock
from monitorrent.rest.static_file import StaticFiles
from monitorrent.tests import RestTestBase


@ddt
class TestStaticFiles(RestTestBase):
    @data(u'<HTML></HTML>', u'<HTML>Other text</HTML>')
    def test_static_index(self, index_text):
        # with not ascii chars in index_text test fails on travis-ci
        stat_class = namedtuple('stat_class', ['st_mtime'])
        time_time = 1105022732.0
        stat = stat_class(st_mtime=time_time)
        with patch("monitorrent.rest.static_file.open", mock_open(read_data=index_text), create=True), \
                patch("monitorrent.rest.static_file.os.path.isfile", Mock(return_value=True), create=True), \
                patch("monitorrent.rest.static_file.os.stat", Mock(return_value=stat), create=True), \
                patch("monitorrent.rest.static_file.mimetypes.guess_type", Mock(return_value=('text/html', 'utf-8')),
                      create=True), \
                patch("monitorrent.rest.static_file.os.path.getsize", MagicMock(return_value=len(index_text)),
                      create=True):
            s = StaticFiles('folder', 'index.html', False)
            self.api.add_route('/index.html', s)

            body = self.simulate_request('/index.html')
            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertEqual('text/html', self.srmock.headers_dict['content-type'])
            self.assertEqual(str(len(index_text)), self.srmock.headers_dict['content-length'])
            self.assertEqual('Thu, 06 Jan 2005 14:45:32 GMT', self.srmock.headers_dict['last-modified'])
            self.assertEqual('1105022732.0', self.srmock.headers_dict['etag'])
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

    def test_not_found(self):
        if_file_mock = MagicMock(return_value=False)
        with patch("monitorrent.rest.static_file.os.path.isfile", if_file_mock, create=True):
            s = StaticFiles('folder', 'index.html', False)
            self.api.add_route('/index.html', s)

            self.simulate_request('/index.html')
            self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
