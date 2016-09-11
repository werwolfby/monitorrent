import six
from future import standard_library

standard_library.install_aliases()
from builtins import map
from builtins import filter
from builtins import object
# coding=utf-8
from io import BytesIO, StringIO
from vcr.cassette import Cassette
from requests import Session
import inspect
import functools
import re
import gzip
import http.cookies
import urllib.request, urllib.parse, urllib.error
from tests import use_vcr
from monitorrent.utils.soup import get_soup
from urllib.parse import urlparse, unquote, quote
from phpserialize import loads


class NnmClubTrackerHelper(object):
    # real values
    real_username = None
    real_password = None
    real_user_id = None
    real_sid = None
    # fake values
    fake_username = 'fakelogin@example.com'
    fake_password = 'p@$$w0rd'
    fake_user_id = '9876543'
    fake_sid = '12345678910111213'
    # protected
    _sid_replace = re.compile(u'sid=[a-z0-9]{32}')

    def __init__(self, username=None, password=None, user_id=None, sid=None):
        super(NnmClubTrackerHelper, self).__init__()
        self.real_username = username or self.fake_username
        self.real_password = password or self.fake_password
        self.real_user_id = user_id or self.fake_user_id
        self.real_sid = sid or self.fake_sid

    @classmethod
    def login(cls, username, password):
        login_url = 'http://nnmclub.to/forum/login.php'
        s = Session()
        data = {"username": username, "password": password, "autologin": "on", "login": "%C2%F5%EE%E4"}
        login_result = s.post(login_url, data)
        if login_result.url.startswith(login_url):
            raise Exception("Can't login to NNM Club")
        sid = s.cookies['phpbb2mysql_4_sid']
        data = s.cookies['phpbb2mysql_4_data']
        parsed_data = loads(unquote(data))
        userid = parsed_data['userid']
        helper = cls(username, password, userid, sid)
        helper.fake_user_id = helper.fake_user_id[:len(userid)]
        return helper

    def hide_sensitive_data(self, cassette):
        """

        :type cassette: Cassette
        :return:
        """
        for data in cassette.data:
            request, response = data
            self._hide_request_sensitive_data(request)
            self._hide_response_sensitive_data(response)

    def _hide_request_sensitive_data(self, request):
        request.body = self._replace_sensitive_data(request.body)

        if 'Cookie' in request.headers:
            cookie_string = request.headers['Cookie']
            cookie = http.cookies.SimpleCookie()
            cookie.load(str(cookie_string))
            cookies = [c.output(header='').strip() for c in list(cookie.values())]
            request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies))

        request.uri = request.uri.replace(self.real_user_id, self.fake_user_id) \
            .replace(self.real_sid, self.fake_sid)
        request.uri = self._sid_replace.sub('sid='+self.fake_sid, request.uri)

    def _replace_sensitive_data(self, value):
        if not value:
            return value
        value = six.text_type(value)
        value = value \
            .replace(self.real_username, self.fake_username) \
            .replace(quote(self.real_username), quote(self.fake_username)) \
            .replace(self.real_password, self.fake_password) \
            .replace(self.real_user_id, self.fake_user_id) \
            .replace(self.real_sid, self.fake_sid)
        value = self._sid_replace.sub('sid=' + self.fake_sid, value)
        return value

    def _hide_response_sensitive_data(self, response):
        if 'content-type' in response['headers']:
            content_types = response['headers']['content-type']
            if not any([t.find('text') >= 0 for t in content_types]):
                return

        if 'set-cookie' in response['headers']:
            response['headers']['set-cookie'] = self._filter_cookies(response['headers']['set-cookie'])

        if 'location' in response['headers']:
            response['headers']['location'] = self._filter_location(response['headers']['location'])

        body = response['body']['string']
        if 'content-encoding' in response['headers']:
            content_encoding = response['headers']['content-encoding']
            is_compressed = 'gzip' in content_encoding
        else:
            is_compressed = False
        if is_compressed:
            body = self._decompress_gzip(body)
        if type(body) is not six.text_type:
            body = six.text_type(body, 'utf-8')
        body = self._replace_sensitive_data(body)
        if is_compressed:
            body = self._compress_gzip(body)
        response['body']['string'] = body

    def _filter_cookies(self, cookies):
        def filter_lambda(c):
            return c.startswith('phpbb2mysql_4_sid') or c.startswith('phpbb2mysql_4_data')

        def replace_lambda(c):
            return self._replace_sensitive_data(c)

        cookies = list(filter(filter_lambda, cookies))
        cookies = list(map(replace_lambda, cookies))
        return cookies

    def _filter_location(self, locations):
        result = list()
        for location in locations:
            value = self._sid_replace.sub("sid=" + self.fake_sid, location)
            value = self._replace_sensitive_data(value)
            result.append(value)
        return result

    @staticmethod
    def _decompress_gzip(body):
        url_file_handle = BytesIO(body)
        with gzip.GzipFile(fileobj=url_file_handle) as g:
            decompressed = g.read().decode('windows-1251')
        url_file_handle.close()
        return decompressed

    @staticmethod
    def _compress_gzip(body):
        url_file_handle = BytesIO()
        with gzip.GzipFile(fileobj=url_file_handle, mode="wb") as g:
            g.write(body.encode('windows-1251'))
        compressed = url_file_handle.getvalue()
        url_file_handle.close()
        return compressed

    def use_vcr(self, func=None, **kwargs):
        if func is None:
            # When called with kwargs, e.g. @helper.use_vcr(inject_cassette=True)
            return functools.partial(self.use_vcr, **kwargs)
        inject_cassette = kwargs.get('inject_cassette', False)
        kwargs['inject_cassette'] = True
        if 'path' not in kwargs:
            module = func.__module__.split('tests.')[-1].split('.')[-1]
            class_name = inspect.stack()[1][3]
            cassette_name = '.'.join([module, class_name, func.__name__])
            kwargs.setdefault('path', cassette_name)

        @use_vcr(**kwargs)
        def wrapped(func_self, cassette, *args, **wkwargs):
            try:
                if inject_cassette:
                    func(func_self, cassette, *args, **wkwargs)
                else:
                    func(func_self, *args, **wkwargs)
            finally:
                self.hide_sensitive_data(cassette)

        return wrapped
