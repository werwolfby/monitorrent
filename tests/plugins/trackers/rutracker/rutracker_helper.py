# coding=utf-8
import cgi
import codecs
import functools
import gzip
import inspect
import http.cookies
from builtins import object
from io import BytesIO

import brotli
import six
from vcr.cassette import Cassette
from tests import use_vcr


class RutrackerHelper(object):
    # real values
    real_login = None
    real_password = None
    real_uid = None
    real_bb_data = None
    # fake values
    fake_login = 'fakelogin'
    fake_password = 'p@$$w0rd'
    fake_uid = '15564713'
    fake_bb_data = '1-15564713-ELKc8t23nmllV4gydkNx-634753855-1440364056-1440408614-2609875527-0'

    def __init__(self, login=None, password=None, uid=None, bb_data=None):
        self.real_login = login or self.fake_login
        self.real_password = password or self.fake_password
        self.real_uid = uid or self.fake_uid
        self.real_bb_data = bb_data or self.fake_bb_data

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
        def wrapped(func_self, *args, **wkwargs):
            cassette = args[0]
            args = args[1:]

            if inject_cassette:
                func(func_self, cassette, *args, **wkwargs)
            else:
                func(func_self, *args, **wkwargs)
            self.hide_sensitive_data(cassette)
        return wrapped

    def hide_sensitive_data(self, cassette: Cassette):
        for data in cassette.data:
            request, response = data
            self._hide_request_sensitive_data(request)
            self._hide_response_sensitive_data(response)

    def _hide_request_sensitive_data(self, request):
        if 'Cookie' in request.headers:
            cookie_string = request.headers['Cookie']
            cookie = http.cookies.SimpleCookie()
            cookie.load(str(cookie_string))
            cookies = [c.output(header='').strip() for c in list(cookie.values())]
            request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies))

        if request.body:
            body = codecs.decode(request.body, 'utf-8')
            body = self._replace_sensitive_data(body)
            request.body = codecs.encode(body, 'utf-8')
        request.uri = request.uri.replace(self.real_uid, self.fake_uid)

    def _filter_cookies(self, cookies):
        filter_lambda = lambda c: not c.startswith("bb_session=deleted") and c.startswith('bb_session')
        replace_lambda = lambda c: self._replace_sensitive_data(c)

        cookies = list(filter(filter_lambda, cookies))
        cookies = list(map(replace_lambda, cookies))
        return cookies

    def _hide_response_sensitive_data(self, response):
        if 'Set-Cookie' in response['headers']:
            response['headers']['Set-Cookie'] = self._filter_cookies(response['headers']['Set-Cookie'])

        charset = None
        if 'Content-Type' in response['headers']:
            content_types = response['headers']['Content-Type']
            if not any([t.find('text') >= 0 for t in content_types]):
                return
            content_type = content_types[0]
            _, params = cgi.parse_header(content_type)
            charset = params['charset']

        body = response['body']['string']
        compression = None
        if 'Content-Encoding' in response['headers']:
            content_encoding = response['headers']['Content-Encoding']
            if 'gzip' in content_encoding:
                compression = 'gzip'
            elif 'br' in content_encoding:
                compression = 'br'
        if compression == 'gzip':
            body = self._decompress_gzip(body)
        elif compression == 'br':
            body = self._decompress_brotli(body)
        if type(body) is bytes:
            body = codecs.decode(body, charset)
        body = self._replace_sensitive_data(body)
        body = codecs.encode(body, charset)
        if compression == 'gzip':
            body = self._compress_gzip(body)
        elif compression == 'br':
            body = self._compress_brotli(body)
        response['body']['string'] = body

    def _replace_sensitive_data(self, value: str):
        if not value:
            return value
        value = value \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_password, self.fake_password) \
            .replace(self.real_bb_data, self.fake_bb_data) \
            .replace(self.real_uid, self.fake_uid)
        return value

    @staticmethod
    def _decompress_gzip(body):
        url_file_handle = BytesIO(body)
        with gzip.GzipFile(fileobj=url_file_handle) as g:
            decompressed = g.read()
        url_file_handle.close()
        return decompressed

    @staticmethod
    def _compress_gzip(body):
        url_file_handle = BytesIO()
        with gzip.GzipFile(fileobj=url_file_handle, mode="wb") as g:
            g.write(body)
        compressed = url_file_handle.getvalue()
        url_file_handle.close()
        return compressed

    @staticmethod
    def _decompress_brotli(body):
        return brotli.decompress(body)

    @staticmethod
    def _compress_brotli(body):
        return brotli.compress(body)
