# coding=utf-8
import functools
import gzip
import inspect

import http.cookies
import six
from builtins import object
from requests import Session
from io import BytesIO

from tests import use_vcr


class AnidubHelper(object):
    # real values
    real_login = None
    real_password = None
    real_dle_uid = None
    real_dle_pwd = None
    # fake values
    fake_login = 'fakelogin'
    fake_password = 'fakepa$$word'
    fake_dle_uid = '1234567890'
    fake_dle_pwd = 'fedcba0987654321'

    def __init__(self, login=None, password=None, dle_uid=None, dle_pwd=None):
        super(AnidubHelper, self).__init__()
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_dle_uid = dle_uid or self.fake_dle_uid
        self.real_dle_pwd = dle_pwd or self.fake_dle_pwd

    @classmethod
    def login(cls, login, password):
        login_url = 'https://tr.anidub.com'
        s = Session()
        data = {"login_name": login, "login_password": password, "login": "submit"}
        login_result = s.post(login_url, data)
        if "index.php?action=logout" not in login_result.text:
            raise Exception("Can't login to Anidub")
        uid = s.cookies['dle_user_id']
        pwd = s.cookies['dle_password']
        helper = cls(login, password, uid, pwd)
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
            request.headers['Cookie'] = '; '.join(self._filter_cookies(cookies))

        request.uri = request.uri.replace(self.real_login, self.fake_login)

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

    def _replace_sensitive_data(self, value):
        if not value:
            return value
        value = six.text_type(value)
        value = value \
            .replace(self.real_password, self.fake_password) \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_dle_pwd, self.fake_dle_pwd) \
            .replace(self.real_dle_uid, self.fake_dle_uid)
        return value

    def _filter_cookies(self, cookies):
        def filter_lambda(c):
            return c.startswith('dle_password') or c.startswith('dle_user_id')

        def replace_lambda(c):
            return self._replace_sensitive_data(c)

        cookies = list(filter(filter_lambda, cookies))
        cookies = list(map(replace_lambda, cookies))
        return cookies

    def _filter_location(self, locations):
        result = list()
        for location in locations:
            value = self._replace_sensitive_data(location)
            result.append(value)
        return result

    @staticmethod
    def _decompress_gzip(body):
        url_file_handle = BytesIO(body)
        with gzip.GzipFile(fileobj=url_file_handle) as g:
            decompressed = g.read().decode('utf-8')
        url_file_handle.close()
        return decompressed

    @staticmethod
    def _compress_gzip(body):
        url_file_handle = BytesIO()
        with gzip.GzipFile(fileobj=url_file_handle, mode="wb") as g:
            g.write(body.encode('utf-8'))
        compressed = url_file_handle.getvalue()
        url_file_handle.close()
        return compressed

    def use_vcr(self, func=None, **kwargs):
        if func is None:
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
