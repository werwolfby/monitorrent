# coding=utf-8
from StringIO import StringIO
from vcr.cassette import Cassette
from requests import Session
from bs4 import BeautifulSoup
import inspect
import functools
import re
import gzip
import Cookie
import urllib
from monitorrent.tests import use_vcr
from monitorrent.utils.soup_factory import SoupFactory


class LostFilmTrackerHelper(object):
    # real values
    real_login = None
    real_email = None
    real_password = None
    real_uid = None
    real_bogi_uid = None
    real_pass = None
    real_usess = None
    # fake values
    fake_login = 'fakelogin'
    fake_email = 'fakelogin@example.com'
    fake_password = 'p@$$w0rd'
    fake_uid = '821271'
    fake_bogi_uid = '348671'
    fake_pass = 'b189ecfa2b46a93ad6565c5de0cf93fa'
    fake_usess = '07f8cb40ff3839303cff18c105111a26'

    def __init__(self, login=None, email=None, password=None, uid=None, bogi_uid=None, _pass=None, usess=None):
        super(LostFilmTrackerHelper, self).__init__()
        self.real_login = login or self.fake_login
        self.real_email = email or self.fake_email
        self.real_password = password or self.fake_password
        self.real_uid = uid or self.fake_uid
        self.real_bogi_uid = bogi_uid or self.fake_bogi_uid
        self.real_pass = _pass or self.fake_pass
        self.real_usess = usess or self.fake_usess

    @classmethod
    def login(cls, username, password):
        login_url = "https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F"
        profile_url = 'http://www.lostfilm.tv/my.php'
        search_usess_re = re.compile(ur'\(usess=([a-f0-9]{32})\)', re.IGNORECASE)

        cls_params = {'login': username, 'password': password}

        s = Session()
        # login over bogi.ru
        params = {"login": username, "password": password}
        r1 = s.post(login_url, params, verify=False)
        # in case of failed login, bogi redirects to:
        # http://www.lostfilm.tv/blg.php?code=6&text=incorrect%20login/password
        if r1.request.url != login_url:
            raise Exception('Can\'t login into lostfilm.tv')

        soup = SoupFactory().get_soup(r1.text)
        inputs = soup.findAll("input")
        action = soup.find("form")['action']
        cparams = dict([(i['name'], i['value']) for i in inputs if 'value' in i.attrs])
        cls_params['bogi_uid'] = cparams['uid']
        cls_params['email'] = cparams['email']
        s.post(action, cparams, verify=False, allow_redirects=False)
        r3 = s.get(profile_url)
        cls_params['uid'] = s.cookies['uid']
        cls_params['_pass'] = s.cookies['pass']
        cls_params['usess'] = search_usess_re.findall(r3.text)[0]

        return cls(**cls_params)

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
            cookie = Cookie.SimpleCookie()
            cookie.load(str(cookie_string))
            cookies = map(lambda c: c.output(header='').strip(), cookie.values())
            request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies))

    def _hide_response_sensitive_data(self, response):
        if 'content-type' in response['headers']:
            content_types = response['headers']['content-type']
            if not any([t.find('text') >= 0 for t in content_types]):
                return

        if 'set-cookie' in response['headers']:
            response['headers']['set-cookie'] = self._filter_cookies(response['headers']['set-cookie'])

        body = response['body']['string']
        if 'content-encoding' in response['headers']:
            content_encoding = response['headers']['content-encoding']
            is_compressed = 'gzip' in content_encoding
        else:
            is_compressed = False
        if is_compressed:
            body = self._decompress_gzip(body)
        body = self._replace_sensitive_data(body)
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

    def _hide_sensitive_data_in_bogi_login(self, request, response):
        request.body = self._replace_sensitive_data(request.body)
        response['body']['string'] = self._replace_sensitive_data(response['body']['string'])

    def _hide_sensitive_data_in_bogi_login_result(self, request, response):
        request.body = request.body \
            .replace(self.real_uid, self.fake_uid) \
            .replace(self.real_bogi_uid, self.fake_bogi_uid) \
            .replace(self.real_pass, self.fake_pass) \
            .replace(self.real_login, self.fake_login) \
            .replace(urllib.quote(self.real_email), urllib.quote(self.fake_email))
        cookies = response['headers']['set-cookie']
        cookies = self._filter_cookies(cookies)
        response['headers']['set-cookie'] = cookies
        return cookies

    def _hide_sensitive_data_in_lostfilm_response(self, request, response):
        cookie_string = request.headers['Cookie']
        cookie = Cookie.SimpleCookie()
        cookie.load(cookie_string)
        cookies = map(lambda c: c.output(header='').strip(), cookie.values())
        request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies))
        profile_page_body = response['body']['string']
        profile_page_body_decompressed = self._decompress_gzip(profile_page_body)
        profile_page_body_decompressed = profile_page_body_decompressed \
            .replace(self.real_uid, self.fake_uid) \
            .replace(self.real_bogi_uid, self.fake_bogi_uid) \
            .replace(self.real_pass, self.fake_pass) \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_email, self.fake_email) \
            .replace(self.real_usess, self.fake_usess)
        # remove avatar link
        my_avatar_index = profile_page_body_decompressed.index('id="my_avatar"')
        value_index = profile_page_body_decompressed.index('value=', my_avatar_index)
        value_len = 6
        end_index = profile_page_body_decompressed.index('"', value_index + value_len + 1)
        profile_page_body_decompressed = profile_page_body_decompressed[:value_index + value_len + 1] + \
                                         profile_page_body_decompressed[end_index:]
        profile_page_body = self._compress_gzip(profile_page_body_decompressed)
        response['body']['string'] = profile_page_body

    def _filter_cookies(self, cookies):
        filter_lambda = lambda c: c.startswith('uid') or c.startswith('pass')
        replace_lambda = lambda c: self._replace_sensitive_data(c)

        cookies = filter(filter_lambda, cookies)
        cookies = map(replace_lambda, cookies)
        return cookies

    def _replace_sensitive_data(self, value):
        if not value:
            return value
        return value \
            .replace(self.real_uid, self.fake_uid) \
            .replace(self.real_bogi_uid, self.fake_bogi_uid) \
            .replace(self.real_pass, self.fake_pass) \
            .replace(self.real_login, self.fake_login) \
            .replace(self.real_password, self.fake_password) \
            .replace(self.real_email, self.fake_email) \
            .replace(self.real_usess, self.fake_usess) \
            .replace(urllib.quote(self.real_email), urllib.quote(self.fake_email))

    @staticmethod
    def _decompress_gzip(body):
        url_file_handle = StringIO(body)
        with gzip.GzipFile(fileobj=url_file_handle) as g:
            decompressed = g.read().decode('windows-1251')
        url_file_handle.close()
        return decompressed

    @staticmethod
    def _compress_gzip(body):
        url_file_handle = StringIO()
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
            module = func.__module__.split('tests.')[-1]
            class_name = inspect.stack()[1][3]
            cassette_name = '.'.join([module, class_name, func.__name__])
            kwargs.setdefault('path', cassette_name)

        @use_vcr(**kwargs)
        def wrapped(func_self, cassette, *args, **wkwargs):
            if inject_cassette:
                func(func_self, cassette, *args, **wkwargs)
            else:
                func(func_self, *args, **wkwargs)
            self.hide_sensitive_data(cassette)
        return wrapped
