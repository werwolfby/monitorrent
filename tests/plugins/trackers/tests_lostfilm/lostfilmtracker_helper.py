import six
# coding=utf-8
from io import BytesIO, StringIO
from vcr.cassette import Cassette
from bs4 import BeautifulSoup
import requests
import inspect
import functools
import re
import gzip
import http.cookies
from six.moves.urllib import parse, error

from monitorrent.plugins.trackers import CloudflareCookiesExtractor
from tests import use_vcr
from monitorrent.utils.soup import get_soup


class LostFilmTrackerHelper(object):
    # real values
    real_login = None
    real_email = None
    real_password = None
    real_session = None
    real_uid = None
    real_headers = None
    real_cookies = None
    # fake values
    fake_login = 'fakelogin'
    fake_email = 'fakelogin@example.com'
    fake_password = 'p@$$w0rd'
    fake_session = '1234567890abcdefghjklmnopqrstvwxyz'
    fake_uid = '123456'
    fake_headers = {'User-Agent': 'Mozilla'}
    fake_cookies = {'cf_clearance': 'abcdef0123456789'}

    def __init__(self, login=None, email=None, password=None, session=None, uid=None, headers=None, cookies=None,):
        super(LostFilmTrackerHelper, self).__init__()
        self.real_login = login or self.fake_login
        self.real_email = email or self.fake_email
        self.real_password = password or self.fake_password
        self.real_session = session or self.fake_session
        self.real_uid = uid or self.fake_uid
        self.real_headers = headers or self.fake_headers
        self.real_cookies = cookies or self.fake_cookies

    @classmethod
    def login(cls, email, password):
        credentials_extractor = CloudflareCookiesExtractor("https://www.lostfilm.tv")
        headers, cookies = credentials_extractor.extract_credentials({}, {})

        params = {"act": "users", "type": "login", "mail": email, "pass": password, "rem": 1}
        response = requests.post("https://www.lostfilm.tv/ajaxik.php", params, verify=False, headers=headers, cookies=cookies)

        result = response.json()
        if 'error' in result and result['error'] == 3:
            raise Exception("Unknown user name or password")

        if 'need_captcha' in result:
            raise Exception("Need captcha")

        lf_session = response.cookies['lf_session']
        cookies.update({'lf_session': lf_session})

        my_settings = requests.get("https://www.lostfilm.tv/my_settings", headers=headers, cookies=cookies)
        soup = BeautifulSoup(my_settings.text)
        uid = soup.find('input', {"name": "myid"}).attrs['value']

        return cls(login=result['name'], email=params['mail'], password=params['pass'], session=lf_session, uid=uid,
                   headers=headers, cookies=cookies)

    def hide_sensitive_data(self, cassette, session):
        """

        :type cassette: Cassette
        :return:
        """
        self.real_session = session or self.real_session
        hashes = list()
        for data in cassette.data:
            request = data[0]
            if request.uri.startswith('http://retre.org/'):
                query = dict(request.query)
                hashes.append(query['h'])

        for data in cassette.data:
            request, response = data
            self._hide_request_sensitive_data(request, hashes)
            self._hide_response_sensitive_data(response, hashes)

    def _hide_request_sensitive_data(self, request, hashes):
        request.body = self._replace_sensitive_data(request.body, hashes)

        if 'Cookie' in request.headers:
            cookie_string = request.headers['Cookie']
            cookie = http.cookies.SimpleCookie()
            cookie.load(str(cookie_string))
            cookies = [c.output(header='').strip() for c in list(cookie.values())]
            request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies, hashes))

        request.uri = request.uri.replace(self.real_uid, self.fake_uid)
        request.uri = self._replace_hashes(request.uri, hashes)
        request.uri = self._replace_tracktorin(request.uri)

    def _hide_response_sensitive_data(self, response, hashes):
        if 'Content-Type' in response['headers']:
            content_types = response['headers']['Content-Type']
            if not any([t.find('text') >= 0 for t in content_types]):
                return

        if 'Set-Cookie' in response['headers']:
            response['headers']['Set-Cookie'] = self._filter_cookies(response['headers']['Set-Cookie'], hashes)

        body = response['body']['string']
        if 'Content-Encoding' in response['headers']:
            content_encoding = response['headers']['Content-Encoding']
            is_compressed = 'gzip' in content_encoding
        else:
            is_compressed = False
        if is_compressed:
            body = self._decompress_gzip(body)
        if type(body) is not six.text_type:
            body = six.text_type(body, 'utf-8')
        body = self._replace_sensitive_data(body, hashes)
        body = self._hide_avatar_url(body)
        if is_compressed:
            body = self._compress_gzip(body)
        response['body']['string'] = body

    @staticmethod
    def _hide_avatar_url(body):
        my_avatar_index = body.find('id="my_avatar"')
        if my_avatar_index == -1:
            return body
        value_index = body.index('value=', my_avatar_index)
        value_len = 6
        end_index = body.index('"', value_index + value_len + 1)
        return body[:value_index + value_len + 1] + body[end_index:]

    def _hide_sensitive_data_in_bogi_login(self, request, response, hashes):
        request.body = self._replace_sensitive_data(request.body, hashes)
        response['body']['string'] = self._replace_sensitive_data(response['body']['string'], hashes)

    def _hide_sensitive_data_in_bogi_login_result(self, request, response, hashes):
        request.body = request.body \
            .replace(self.real_login, self.fake_login) \
            .replace(parse.quote(self.real_email), parse.quote(self.fake_email))
        cookies = response['headers']['Set-Cookie']
        cookies = self._filter_cookies(cookies, hashes)
        response['headers']['Set-C1ookie'] = cookies
        return cookies

    def _hide_sensitive_data_in_lostfilm_response(self, request, response, hashes):
        cookie_string = request.headers['Cookie']
        cookie = http.cookies.SimpleCookie()
        cookie.load(cookie_string)
        cookies = [c.output(header='').strip() for c in list(cookie.values())]
        request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies, hashes))
        profile_page_body = response['body']['string']
        profile_page_body_decompressed = self._decompress_gzip(profile_page_body)
        profile_page_body_decompressed = profile_page_body_decompressed \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_email, self.fake_email) \
        # remove avatar link
        my_avatar_index = profile_page_body_decompressed.index('id="my_avatar"')
        value_index = profile_page_body_decompressed.index('value=', my_avatar_index)
        value_len = 6
        end_index = profile_page_body_decompressed.index('"', value_index + value_len + 1)
        profile_page_body_decompressed = profile_page_body_decompressed[:value_index + value_len + 1] + \
                                         profile_page_body_decompressed[end_index:]
        profile_page_body = self._compress_gzip(profile_page_body_decompressed)
        response['body']['string'] = profile_page_body

    def _filter_cookies(self, cookies, hashes):
        filter_lambda = lambda c: not c.startswith("lf_session=deleted") and c.startswith('lf_session')
        replace_lambda = lambda c: self._replace_sensitive_data(c, hashes)

        cookies = list(filter(filter_lambda, cookies))
        cookies = list(map(replace_lambda, cookies))
        return cookies

    def _replace_sensitive_data(self, value, hashes):
        if not value:
            return value
        value = six.text_type(value)
        value = value \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_password, self.fake_password) \
            .replace(self.real_email, self.fake_email) \
            .replace(self.real_session, self.fake_session) \
            .replace(self.real_uid, self.fake_uid) \
            .replace(parse.quote(self.real_email), parse.quote(self.fake_email))
        value = self._replace_hashes(value, hashes)
        return self._replace_tracktorin(value)

    @staticmethod
    def _replace_tracktorin(value):
        def repl(match):
            return match.group(0)[0:-50] + '-' * 50

        return re.sub(u'http://tracktor.in/td.php\?s=([a-zA-Z0-9]|(%[0-9A-F]{2}))+',
                      repl,
                      value)

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

    @staticmethod
    def _replace_hashes(value, hashes):
        for h in hashes:
            value = value.replace(h, 'some_hash_value')
        return value

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
            # when real_session aquired by helper.login, but test do login itself,
            # we have to re-read current casssete session from test itself
            if hasattr(func_self, 'tracker'):
                session = func_self.tracker.session
            elif hasattr(func_self, 'plugin'):
                session = func_self.plugin.tracker.session
            else:
                session = None
            self.hide_sensitive_data(cassette, session)
        return wrapped
