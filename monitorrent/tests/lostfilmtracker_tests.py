# coding=utf-8
from monitorrent.plugins.trackers.lostfilm import LostFilmTVTracker, LostFilmTVLoginFailedException
from unittest import TestCase, skip
from monitorrent.tests import test_vcr
from StringIO import StringIO
import vcr
import random
import gzip
import Cookie
import urllib

# for real test set real values
REAL_LOGIN = 'fakelogin'
REAL_EMAIL = 'fakelogin@example.com'
REAL_PASSWORD = 'p@$$w0rd'
# this are 4 random strings
REAL_UID = '821271'
REAL_BOGI_UID = '348671'
REAL_PASS = 'b189ecfa2b46a93ad6565c5de0cf93fa'
REAL_USESS = '07f8cb40ff3839303cff18c105111a26'
# will be replaced when created casset to this values
FAKE_UID = '821271'
FAKE_BOGI_UID = '348671'
FAKE_PASS = 'b189ecfa2b46a93ad6565c5de0cf93fa'
FAKE_USESS = '07f8cb40ff3839303cff18c105111a26'

lostfilm_vcr = vcr.VCR(
    cassette_library_dir=test_vcr.cassette_library_dir,
    record_mode=test_vcr.record_mode
)

use_vcr = lostfilm_vcr.use_cassette


class LostFilmTrackerTest(TestCase):
    def test_login(self):
        with use_vcr("test_login") as v:
            tracker = LostFilmTVTracker()
            tracker.login(REAL_LOGIN, REAL_PASSWORD)
            self.assertTrue(tracker.c_uid == REAL_UID)
            self.assertTrue(tracker.c_pass == REAL_PASS)
            self.assertTrue(tracker.c_usess == REAL_USESS)
            self._hide_sensitive_data(v)

    @use_vcr()
    def test_fail_login(self):
        tracker = LostFilmTVTracker()
        with self.assertRaises(LostFilmTVLoginFailedException) as cm:
            tracker.login(REAL_LOGIN, "FAKE_PASSWORD")
        self.assertEqual(cm.exception.code, 6)
        self.assertEqual(cm.exception.text, 'incorrect login/password')
        self.assertEqual(cm.exception.message, u'Не удалось войти. Возможно не правильный логин/пароль')

    @use_vcr()
    @skip("Skip until I find the way to impersonate login/password data into cassetes")
    def test_verify(self):
        tracker = LostFilmTVTracker(REAL_UID, REAL_PASS, REAL_USESS)
        self.assertTrue(tracker.verify())

    @use_vcr()
    def test_verify_fail(self):
        tracker = LostFilmTVTracker("457686", '1'*32, '2'*32)
        self.assertFalse(tracker.verify())

    def test_parse_correct_title(self):
        title = LostFilmTVTracker._parse_title(u'Род человеческий (Extant)')
        self.assertEqual(u'Род человеческий', title['name'])
        self.assertEqual(u'Extant', title['original_name'])

    @use_vcr()
    def test_parse_correct_url(self):
        tracker = LostFilmTVTracker("457686", '1'*32, '2'*32)
        title = tracker.parse_url('http://www.lostfilm.tv/browse.php?cat=236')
        self.assertEqual(u'12 обезьян', title['name'])
        self.assertEqual(u'12 Monkeys', title['original_name'])

    def test_parse_corrent_rss_title0(self):
        t1 = u'Мистер Робот (Mr. Robot). уя3вим0сти.wmv (3xpl0its.wmv) [MP4]. (S01E05)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Мистер Робот', parsed['name'])
        self.assertEqual(u'Mr. Robot', parsed['original_name'])
        self.assertEqual(u'уя3вим0сти.wmv', parsed['title'])
        self.assertEqual(u'3xpl0its.wmv', parsed['original_title'])
        self.assertEqual(u'720p', parsed['quality'])
        self.assertEqual(u'S01E05', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(5, parsed['episode'])

    def test_parse_corrent_rss_title1(self):
        t1 = u'Мистер Робот (Mr. Robot). уя3вим0сти.wmv (3xpl0its.wmv). (S01E05)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Мистер Робот', parsed['name'])
        self.assertEqual(u'Mr. Robot', parsed['original_name'])
        self.assertEqual(u'уя3вим0сти.wmv', parsed['title'])
        self.assertEqual(u'3xpl0its.wmv', parsed['original_title'])
        self.assertEqual(u'SD', parsed['quality'])
        self.assertEqual(u'S01E05', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(5, parsed['episode'])

    def test_parse_special_rss_title(self):
        t1 = u'Под куполом (Under the Dome). Идите дальше/А я останусь (Move On/But I\'m Not) [1080p]. (S03E01E02)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Под куполом', parsed['name'])
        self.assertEqual(u'Under the Dome', parsed['original_name'])
        self.assertEqual(u'Идите дальше/А я останусь', parsed['title'])
        self.assertEqual(u'Move On/But I\'m Not', parsed['original_title'])
        self.assertEqual(u'1080p', parsed['quality'])
        self.assertEqual(u'S03E01E02', parsed['episode_info'])
        self.assertEqual(3, parsed['season'])
        self.assertEqual(2, parsed['episode'])

    def test_parse_special_rss_title2(self):
        t1 = u'Люди (Humans). Эпизод 8 [MP4]. (S01E08)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Люди', parsed['name'])
        self.assertEqual(u'Humans', parsed['original_name'])
        self.assertEqual(u'Эпизод 8', parsed['title'])
        self.assertIsNone(parsed['original_title'])
        self.assertEqual(u'720p', parsed['quality'])
        self.assertEqual(u'S01E08', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(8, parsed['episode'])

    def test_parse_special_rss_title3(self):
        t1 = u'Люди (Humans). Эпизод 8. (S01E08)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Люди', parsed['name'])
        self.assertEqual(u'Humans', parsed['original_name'])
        self.assertEqual(u'Эпизод 8', parsed['title'])
        self.assertIsNone(parsed['original_title'])
        self.assertEqual(u'SD', parsed['quality'])
        self.assertEqual(u'S01E08', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(8, parsed['episode'])

    def _hide_sensitive_data(self, cassette):
        self._hide_sensitive_data_in_bogi_login(*(cassette.data[0]))
        self._hide_sensitive_data_in_bogi_login_result(*(cassette.data[1]))
        self._hide_sensitive_data_in_lostfilm_response(*(cassette.data[2]))

    def _hide_sensitive_data_in_bogi_login(self, request, response):
        request.body = ''
        body = response['body']['string']
        body = body \
            .replace(REAL_UID, FAKE_UID) \
            .replace(REAL_BOGI_UID, FAKE_BOGI_UID) \
            .replace(REAL_PASS, FAKE_PASS) \
            .replace(REAL_LOGIN, 'fakelogin') \
            .replace(REAL_EMAIL, 'fakelogin@example.com')
        response['body']['string'] = body

    def _hide_sensitive_data_in_bogi_login_result(self, request, response):
        request.body = request.body \
            .replace(REAL_UID, FAKE_UID) \
            .replace(REAL_BOGI_UID, FAKE_BOGI_UID) \
            .replace(REAL_PASS, FAKE_PASS) \
            .replace(REAL_LOGIN, 'fakelogin') \
            .replace(urllib.quote(REAL_EMAIL), urllib.quote('fakelogin@example.com'))
        cookies = response['headers']['set-cookie']
        cookies = self._filter_cookies(cookies, FAKE_UID, FAKE_PASS)
        response['headers']['set-cookie'] = cookies
        return cookies

    def _hide_sensitive_data_in_lostfilm_response(self, request, response):
        cookie_string = request.headers['Cookie']
        cookie = Cookie.SimpleCookie()
        cookie.load(cookie_string)
        cookies = map(lambda c: c.output(header='').strip(), cookie.values())
        request.headers['Cookie'] = "; ".join(self._filter_cookies(cookies, FAKE_UID, FAKE_PASS))
        profile_page_body = response['body']['string']
        url_file_handle = StringIO(profile_page_body)
        with gzip.GzipFile(fileobj=url_file_handle) as g:
            profile_page_body_decompressed = g.read().decode('windows-1251')
        url_file_handle.close()
        profile_page_body_decompressed = profile_page_body_decompressed\
            .replace(REAL_UID, FAKE_UID) \
            .replace(REAL_BOGI_UID, FAKE_BOGI_UID) \
            .replace(REAL_PASS, FAKE_PASS) \
            .replace(REAL_LOGIN, 'fakelogin') \
            .replace(REAL_EMAIL, 'fakelogin@example.com') \
            .replace(REAL_USESS, FAKE_USESS)
        # remove avatar link
        my_avatar_index = profile_page_body_decompressed.index('id="my_avatar"')
        value_index = profile_page_body_decompressed.index('value=', my_avatar_index)
        value_len = 6
        end_index = profile_page_body_decompressed.index('"', value_index + value_len + 1)
        profile_page_body_decompressed = profile_page_body_decompressed[:value_index + value_len + 1] + \
            profile_page_body_decompressed[end_index:]
        url_file_handle = StringIO()
        with gzip.GzipFile(fileobj=url_file_handle, mode="wb") as g:
            g.write(profile_page_body_decompressed.encode('windows-1251'))
        profile_page_body = url_file_handle.getvalue()
        url_file_handle.close()
        response['body']['string'] = profile_page_body

    def _filter_cookies(self, cookies, fake_uid, fake_pass):
        cookies = filter(lambda c: c.startswith('uid') or c.startswith('pass'), cookies)
        cookies = map(lambda c: c.replace(REAL_UID, fake_uid).replace(REAL_PASS, fake_pass), cookies)
        return cookies

    @staticmethod
    def _random_str(length, ishex):
        random_str = '0123456789abcdef' if ishex else '0123456789'
        return ''.join(random.choice(random_str) for _ in xrange(length))
