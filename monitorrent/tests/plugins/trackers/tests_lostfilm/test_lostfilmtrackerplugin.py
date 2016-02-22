# coding=utf-8
import re
import httpretty
from ddt import ddt, data, unpack
from mock import Mock, patch
import pytz
from monitorrent.plugins.trackers.lostfilm import LostFilmPlugin, LostFilmTVTracker, LostFilmTVLoginFailedException, \
    LostFilmTVSeries
from monitorrent.plugins.trackers import LoginResult
from monitorrent.tests import use_vcr, DbTestCase, ReadContentMixin
from monitorrent.tests.plugins.trackers.tests_lostfilm.lostfilmtracker_helper import LostFilmTrackerHelper
from monitorrent.engine import Logger
from monitorrent.db import DBSession
import datetime

helper = LostFilmTrackerHelper()


class EngineMock(object):
    log = Logger()

    def add_torrent(self, filename, torrent, old_hash):
        return datetime.datetime.now(pytz.utc)


@ddt
class LostFilmTrackerPluginTest(ReadContentMixin, DbTestCase):
    @use_vcr()
    def test_prepare_add_topic(self):
        plugin = LostFilmPlugin()
        settings = plugin.prepare_add_topic('http://www.lostfilm.tv/browse.php?cat=236')
        self.assertEqual(u'12 обезьян / 12 Monkeys', settings['display_name'])
        self.assertEqual(u'SD', settings['quality'])

    @use_vcr()
    def test_add_topic(self):
        plugin = LostFilmPlugin()
        params = {
            'display_name': u'12 обезьян / 12 Monkeys',
            'quality': '720p'
        }
        self.assertTrue(plugin.add_topic('http://www.lostfilm.tv/browse.php?cat=236', params))
        topic = plugin.get_topic(1)
        self.assertIsNotNone(topic)
        self.assertEqual('http://www.lostfilm.tv/browse.php?cat=236', topic['url'])
        self.assertEqual(params['display_name'], topic['display_name'])
        self.assertEqual(params['quality'], topic['quality'])
        self.assertIsNone(topic['season'])
        self.assertIsNone(topic['episode'])

    @helper.use_vcr()
    def test_login_verify(self):
        plugin = LostFilmPlugin()
        self.assertFalse(plugin.verify())

        self.assertEqual(LoginResult.CredentialsNotSpecified, plugin.login())

        plugin.update_credentials({'username': '', 'password': ''})

        self.assertEqual(LoginResult.CredentialsNotSpecified, plugin.login())

        plugin.update_credentials({'username': 'admin', 'password': 'admin'})

        self.assertEqual(LoginResult.IncorrentLoginPassword, plugin.login())

        credentials = {
            'username': helper.real_login,
            'password': helper.real_password
        }

        plugin.update_credentials(credentials)
        self.assertFalse(plugin.verify())

        self.assertEqual(LoginResult.Ok, plugin.login())

        self.assertTrue(plugin.verify())

    def test_login_success(self):
        mock_tracker = LostFilmTVTracker()
        mock_tracker.c_uid = '123456'
        mock_tracker.c_pass = 'c3cdf2d2784e81097cda167b8f0674bd'
        mock_tracker.c_uid = 'e9853fcd82cd46a5294349151700643e'
        login_mock = Mock()
        mock_tracker.login = login_mock
        plugin = LostFilmPlugin()
        plugin.tracker = mock_tracker
        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        self.assertEqual(plugin.login(), LoginResult.Ok)

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_incorrect_login_password(self):
        mock_tracker = LostFilmTVTracker()
        login_mock = Mock(side_effect=LostFilmTVLoginFailedException(6, 'incorrect login/password', ''))
        mock_tracker.login = login_mock
        plugin = LostFilmPlugin()
        plugin.tracker = mock_tracker
        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        self.assertEqual(plugin.login(), LoginResult.IncorrentLoginPassword)

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_unknown_1(self):
        mock_tracker = LostFilmTVTracker()
        login_mock = Mock(side_effect=LostFilmTVLoginFailedException(1, 'temp_code', 'temp_message'))
        mock_tracker.login = login_mock
        plugin = LostFilmPlugin()
        plugin.tracker = mock_tracker
        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        self.assertEqual(plugin.login(), LoginResult.Unknown)

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_unknown_2(self):
        mock_tracker = LostFilmTVTracker()
        login_mock = Mock(side_effect=Exception)
        mock_tracker.login = login_mock
        plugin = LostFilmPlugin()
        plugin.tracker = mock_tracker
        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        self.assertEqual(plugin.login(), LoginResult.Unknown)

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    @data(('http://www.lostfilm.tv/browse.php?cat=236', True),
          ('http://www.lostfilm.tv/my.php', False))
    @unpack
    def test_can_parse_url(self, url, value):
        plugin = LostFilmPlugin()
        self.assertEqual(value, plugin.can_parse_url(url))

    @use_vcr
    def test_prepare_add_topic_success(self):
        plugin = LostFilmPlugin()
        result = plugin.prepare_add_topic('http://www.lostfilm.tv/browse.php?cat=236')

        self.assertEqual({'display_name': u'12 обезьян / 12 Monkeys', 'quality': 'SD'}, result)

    @data('SD', '720p', '1080p')
    @use_vcr
    def test_prepare_add_topic_success_2(self, quality):
        plugin = LostFilmPlugin()
        plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent', 'default_quality': quality})
        result = plugin.prepare_add_topic('http://www.lostfilm.tv/browse.php?cat=236')

        self.assertEqual({'display_name': u'12 обезьян / 12 Monkeys', 'quality': quality}, result)

    @use_vcr
    def test_prepare_add_topic_fail(self):
        plugin = LostFilmPlugin()
        self.assertIsNone(plugin.prepare_add_topic('http://www.lostfilm.tv/browse.php?cat=2'))

    @httpretty.activate
    def test_execute(self):
        httpretty.HTTPretty.allow_net_connect = False
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')
        # Mr. Robot series
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=245')),
                               body=self.read_httpretty_content('browse.php_cat-245(Mr. Robot).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=245&s=1&e=09')),
                               body=self.read_httpretty_content('nrd.php_c=245&s=1&e=09.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=245&s=1&e=10')),
                               body=self.read_httpretty_content('nrd.php_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=245&s=1&e=09') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=245&s=1&e=09.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=245&s=1&e=10') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)

        # Scream series
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=251')),
                               body=self.read_httpretty_content('browse.php_cat-251(Scream).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=251&s=1&e=10')),
                               body=self.read_httpretty_content('nrd.php_c=251&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=251&s=1&e=10') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=251&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)

        # tracktor.in download all files
        httpretty.register_uri(httpretty.GET, 'http://tracktor.in/td.php', body=torrent_body,
                               adding_headers={'content-disposition': 'attachment; filename=' + file_name})

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=245", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', '720p', 1, 8)
        self._add_topic("http://www.lostfilm.tv/browse.php?cat=251", u'Крик / Scream',
                        'Scream', '720p', 1, 9)

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)
        topic2 = plugin.get_topic(2)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 10)

        self.assertEqual(topic2['season'], 1)
        self.assertEqual(topic2['episode'], 10)

        self.assertTrue(httpretty.has_request())

    @httpretty.activate
    def test_execute_2(self):
        httpretty.HTTPretty.allow_net_connect = False
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')
        # Mr. Robot series
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=245')),
                               body=self.read_httpretty_content('browse.php_cat-245(Mr. Robot).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=245&s=1&e=09')),
                               body=self.read_httpretty_content('nrd.php_c=245&s=1&e=09.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=245&s=1&e=10')),
                               body=self.read_httpretty_content('nrd.php_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=245&s=1&e=09') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=245&s=1&e=09.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=245&s=1&e=10') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)

        # Scream series
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=251')),
                               body=self.read_httpretty_content('browse.php_cat-251(Scream).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=251&s=1&e=10')),
                               body=self.read_httpretty_content('nrd.php_c=251&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=251&s=1&e=10') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=251&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)

        # with filename
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://tracktor.in/td.php?s=nZHT84nwJy')),
                               body=torrent_body, match_querystring=True,
                               adding_headers={'content-disposition': 'attachment; filename=' + file_name})
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://tracktor.in/td.php?s=NaCZsdihSJ')),
                               body="Not Found", match_querystring=True, status=404)
        # without filename
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://tracktor.in/td.php?s=iQvMNdfmPE')),
                               body=torrent_body, match_querystring=True)

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=245", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', '720p', 1, 8)
        self._add_topic("http://www.lostfilm.tv/browse.php?cat=251", u'Крик / Scream',
                        'Scream', '720p', 1, 9)

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)
        topic2 = plugin.get_topic(2)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 9)

        self.assertEqual(topic2['season'], 1)
        self.assertEqual(topic2['episode'], 10)

        self.assertTrue(httpretty.has_request())

    @httpretty.activate
    def test_execute_3(self):
        httpretty.HTTPretty.allow_net_connect = False

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=245", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', '720p', 1, 8)

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 8)

    @httpretty.activate
    def test_execute_4(self):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=245')),
                               body=self.read_httpretty_content('browse.php_cat-245(Mr. Robot).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=251')),
                               body=self.read_httpretty_content('browse.php_cat-251(Scream).html', encoding='utf-8'),
                               match_querystring=True)

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=245", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', '720p', 1, 10)
        self._add_topic("http://www.lostfilm.tv/browse.php?cat=251", u'Крик / Scream',
                        'Scream', '720p', 1, 10)

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)
        topic2 = plugin.get_topic(2)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 10)

        self.assertEqual(topic2['season'], 1)
        self.assertEqual(topic2['episode'], 10)

        self.assertTrue(httpretty.has_request())

    @httpretty.activate
    def test_execute_5(self):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=58')),
                               body=self.read_httpretty_content('browse.php_cat-58(Miracles).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=58&s=1&e=13')),
                               body=self.read_httpretty_content('nrd.php_c=58&s=1&e=13.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=58&s=1&e=13') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=58&s=1&e=13.html', encoding='utf-8'),
                               match_querystring=True)

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=58", u'Святой Дозо / Miracles',
                        'Miracles', '720p', 1, 12)

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 12)

        self.assertTrue(httpretty.has_request())

    @httpretty.activate
    def test_execute_download_latest_one_only(self):
        httpretty.HTTPretty.allow_net_connect = False
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')

        plugin = LostFilmPlugin()
        plugin.tracker.setup(helper.real_uid, helper.real_pass, helper.real_usess)
        plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/browse.php?cat=245", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', '720p')
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/browse.php?cat=245')),
                               body=self.read_httpretty_content('browse.php_cat-245(Mr. Robot).html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://www.lostfilm.tv/nrdr2.php?c=245&s=1&e=10')),
                               body=self.read_httpretty_content('nrd.php_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, re.compile(re.escape('http://retre.org/?c=245&s=1&e=10') +
                                                         ur"&u=\d+&h=[a-z0-9]+"),
                               body=self.read_httpretty_content('reTre.org_c=245&s=1&e=10.html', encoding='utf-8'),
                               match_querystring=True)
        httpretty.register_uri(httpretty.GET, 'http://tracktor.in/td.php', body=torrent_body,
                               adding_headers={'content-disposition': 'attachment; filename=' + file_name})

        # noinspection PyTypeChecker
        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 10)

        self.assertEqual(len(httpretty.httpretty.latest_requests), 4)

    def test_execute_login_failed(self):
        plugin = LostFilmPlugin()
        execute_login_mock = Mock(return_value=False)
        plugin._execute_login = execute_login_mock
        engine_mock = EngineMock()
        # noinspection PyTypeChecker
        plugin.execute(None, engine_mock)

        execute_login_mock.assert_called_with(engine_mock)

    @data((1, 10, 'S01E10'),
          (10, 9, 'S10E09'),
          (1, None, 'S01'),
          (11, None, 'S11'),
          (None, None, None))
    @unpack
    def test_get_topic_info(self, season, episode, expected):
        plugin = LostFilmPlugin()
        topic = LostFilmTVSeries(season=season, episode=episode)
        info = plugin.get_topic_info(topic)
        self.assertEqual(info, expected)

    @data(({'name': u'Русский', 'original_name': 'Russian'}, u'Русский / Russian'),
          ({'original_name': u'Not Parsed'}, u'Not Parsed'))
    @unpack
    def test_get_display_name(self, parsed_url, expected):
        plugin = LostFilmPlugin()
        # noinspection PyProtectedMember
        display_name = plugin._get_display_name(parsed_url)
        self.assertEqual(expected, display_name)

    def _add_topic(self, url, display_name, search_name, quality, season=None, episode=None):
        with DBSession() as db:
            topic = LostFilmTVSeries()
            topic.url = url
            topic.display_name = display_name
            topic.search_name = search_name
            topic.season = season
            topic.episode = episode
            topic.quality = quality
            db.add(topic)
            db.commit()
            return topic.id
