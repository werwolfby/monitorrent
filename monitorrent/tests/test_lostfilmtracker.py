# coding=utf-8
import httpretty
from ddt import ddt, data, unpack
from monitorrent.plugins.trackers.lostfilm import LostFilmTVTracker, LostFilmTVLoginFailedException
from unittest import TestCase
from monitorrent.tests import use_vcr, ReadContentMixin
from monitorrent.tests.lostfilmtracker_helper import LostFilmTrackerHelper

# For real testing you can create LostFilmTrackerHelper over login method,
# and remove all corresponding cassettes.
# ex.: helper = LostFilmTrackerHelper.login("login", "password")
helper = LostFilmTrackerHelper()


@ddt
class LostFilmTrackerTest(ReadContentMixin, TestCase):
    @helper.use_vcr()
    def test_login(self):
        tracker = LostFilmTVTracker()
        tracker.login(helper.real_login, helper.real_password)
        self.assertTrue(tracker.c_uid == helper.real_uid)
        self.assertTrue(tracker.c_pass == helper.real_pass)
        self.assertTrue(tracker.c_usess == helper.real_usess)

    @use_vcr()
    def test_fail_login(self):
        tracker = LostFilmTVTracker()
        with self.assertRaises(LostFilmTVLoginFailedException) as cm:
            tracker.login("admin", "FAKE_PASSWORD")
        self.assertEqual(cm.exception.code, 6)
        self.assertEqual(cm.exception.text, u'incorrect login/password')
        self.assertEqual(cm.exception.message, u'Не удалось войти. Возможно не правильный логин/пароль')

    @helper.use_vcr()
    def test_verify(self):
        tracker = LostFilmTVTracker(helper.real_uid, helper.real_pass, helper.real_usess)
        self.assertTrue(tracker.verify())

    def test_verify_false(self):
        tracker = LostFilmTVTracker()
        self.assertFalse(tracker.verify())

    @use_vcr()
    def test_verify_fail(self):
        tracker = LostFilmTVTracker("457686", '1'*32, '2'*32)
        self.assertFalse(tracker.verify())

    def test_parse_correct_title(self):
        title = LostFilmTVTracker._parse_title(u'Род человеческий (Extant)')
        self.assertEqual(u'Род человеческий', title['name'])
        self.assertEqual(u'Extant', title['original_name'])

    def test_parse_correct_title_strange(self):
        title = LostFilmTVTracker._parse_title(u'Род человеческий')
        self.assertEqual(u'Род человеческий', title['original_name'])

    @data(('http://www.lostfilm.tv/browse.php?cat=236', True),
          ('http://www.lostfilm.tv/my.php', False))
    @unpack
    def test_can_parse_url(self, url, value):
        tracker = LostFilmTVTracker()
        self.assertEqual(value, tracker.can_parse_url(url))

    @use_vcr()
    def test_parse_correct_url(self):
        tracker = LostFilmTVTracker()
        title = tracker.parse_url('http://www.lostfilm.tv/browse.php?cat=236')
        self.assertEqual(u'12 обезьян', title['name'])
        self.assertEqual(u'12 Monkeys', title['original_name'])

    @use_vcr()
    def test_parse_correct_url_issue_22_1(self):
        tracker = LostFilmTVTracker()
        title = tracker.parse_url('http://www.lostfilm.tv/browse.php?cat=114')
        self.assertEqual(u'Дневники вампира', title['name'])
        self.assertEqual(u'The Vampire Diaries', title['original_name'])

    @use_vcr()
    def test_parse_correct_url_issue_22_2(self):
        tracker = LostFilmTVTracker()
        title = tracker.parse_url('http://www.lostfilm.tv/browse.php?cat=160')
        self.assertEqual(u'Гримм', title['name'])
        self.assertEqual(u'Grimm', title['original_name'])

    @use_vcr()
    def test_parse_incorrect_url_1(self):
        url = 'http://www.lostfilm.tv/browse_wrong.php?cat=236'
        tracker = LostFilmTVTracker()
        self.assertIsNone(tracker.parse_url(url))

    @use_vcr()
    def test_parse_incorrect_url_2(self):
        url = 'http://www.lostfilm.tv/browse.php?cat=2'
        tracker = LostFilmTVTracker()
        self.assertIsNone(tracker.parse_url(url))

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

    @data(u'Мистер Робот (Mr. Robot. уя3вим0сти.wmv (3xpl0its.wmv). (S01E05)',
          u'Мистер Робот (Mr. Robot). уя3вим0сти.wmv (3xpl0its.wmv). (S01E)')
    def test_parse_incorrent_rss_title1(self, title):
        self.assertIsNone(LostFilmTVTracker.parse_rss_title(title))

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

    def test_parse_special_rss_title4(self):
        t1 = u'Люди (Humans). Эпизод 8 [WEBRip]. (S01E08)'
        parsed = LostFilmTVTracker.parse_rss_title(t1)
        self.assertEqual(u'Люди', parsed['name'])
        self.assertEqual(u'Humans', parsed['original_name'])
        self.assertEqual(u'Эпизод 8', parsed['title'])
        self.assertIsNone(parsed['original_title'])
        self.assertEqual(u'unknown', parsed['quality'])
        self.assertEqual(u'S01E08', parsed['episode_info'])
        self.assertEqual(1, parsed['season'])
        self.assertEqual(8, parsed['episode'])

    @httpretty.activate
    def test_httpretty_login_success(self):
        uid = '151548'
        pass_ = 'dd770c2445d297ed0aa192c153e5424c'
        usess = 'e76e71e0f32e65c2470e42016dbb785e'

        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(httpretty.POST,
                               'https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F',
                               body=self.read_httpretty_content('test_lostfilmtracker.1.login1.bogi.ru.html'))

        # hack for pass multiple cookies
        httpretty.register_uri(httpretty.POST,
                               'http://www.lostfilm.tv/blg.php?ref=random',
                               body='', status=302,
                               set_cookie="uid={0}\r\n"
                                          "Set-Cookie: pass={1}".format(uid, pass_),
                               location='/')
        httpretty.register_uri(httpretty.GET, 'http://www.lostfilm.tv/my.php',
                               body='(usess={})'.format(usess))

        tracker = LostFilmTVTracker()
        tracker.login('fakelogin', 'p@$$w0rd')

        self.assertEqual(tracker.c_uid, uid)
        self.assertEqual(tracker.c_pass, pass_)
        self.assertEqual(tracker.c_usess, usess)

    @httpretty.activate
    def test_httpretty_unknown_login_failed(self):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(httpretty.POST,
                               'https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F',
                               body=self.read_httpretty_content('test_lostfilmtracker.1.login1.bogi.ru.html'))

        # hack for pass multiple cookies
        httpretty.register_uri(httpretty.POST,
                               'http://www.lostfilm.tv/blg.php?ref=random',
                               body='Internal server error', status=500)

        tracker = LostFilmTVTracker()
        with self.assertRaises(LostFilmTVLoginFailedException) as cm:
            tracker.login('fakelogin', 'p@$$w0rd')
        self.assertEqual(cm.exception.code, -2)
        self.assertIsNone(cm.exception.text)
        self.assertIsNone(cm.exception.message)

    @httpretty.activate
    def test_httpretty_unknown_login_failed_2(self):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(httpretty.POST,
                               'https://login1.bogi.ru/login.php?referer=https%3A%2F%2Fwww.lostfilm.tv%2F',
                               body='', status=302,
                               location='http://some-error.url/error.php')
        httpretty.register_uri(httpretty.GET,
                               'http://some-error.url/error.php',
                               body='', status=200)

        tracker = LostFilmTVTracker()
        with self.assertRaises(LostFilmTVLoginFailedException) as cm:
            tracker.login('fakelogin', 'p@$$w0rd')
        self.assertEqual(cm.exception.code, -1)
        self.assertIsNone(cm.exception.text)
        self.assertIsNone(cm.exception.message)
