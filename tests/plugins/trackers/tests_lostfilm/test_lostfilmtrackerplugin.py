# coding=utf-8
import re
import requests_mock
from ddt import ddt, data, unpack
from mock import Mock, patch
from requests import Response
import pytz
from monitorrent.db import DBSession
from monitorrent.plugins.status import Status
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.lostfilm import LostFilmShow, LostFilmPlugin, LostFilmTVTracker, \
    LostFilmTVLoginFailedException, LostFilmTVSeries
from tests import use_vcr, DbTestCase, ReadContentMixin
from tests.plugins.trackers.tests_lostfilm.lostfilmtracker_helper import LostFilmTrackerHelper
import datetime

helper = LostFilmTrackerHelper()


class EngineMock(object):
    def info(self, message):
        pass

    def failed(self, message):
        pass

    def downloaded(self, message, content):
        pass

    def status_changed(self, old_status, new_status):
        pass

    def start(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add_torrent(self, index, filename, torrent, old_hash, topic_settings):
        return datetime.datetime.now(pytz.utc)


@ddt
class TestLostFilmTrackerPlugin(ReadContentMixin, DbTestCase):
    def setUp(self):
        super(TestLostFilmTrackerPlugin, self).setUp()
        self.tracker_settings = TrackerSettings(10, None)
        self.plugin = LostFilmPlugin()
        self.plugin.init(self.tracker_settings)

    @use_vcr()
    def test_prepare_add_topic(self):
        settings = self.plugin.prepare_add_topic('http://www.lostfilm.tv/series/12_Monkeys/seasons')
        assert settings['display_name'] == u'12 обезьян / 12 Monkeys'
        assert settings['quality'] == u'SD'

    @use_vcr()
    def test_add_topic(self):
        params = {
            'display_name': u'12 обезьян / 12 Monkeys',
            'quality': '720p'
        }
        assert self.plugin.add_topic('http://www.lostfilm.tv/series/12_Monkeys/seasons', params)
        topic = self.plugin.get_topic(1)
        assert topic is not None
        assert topic['url'] == 'https://www.lostfilm.tv/series/12_Monkeys/seasons'
        assert topic['display_name'] == params['display_name']
        assert topic['quality'] == params['quality']
        assert topic['season'] is None
        assert topic['episode'] is None

    @helper.use_vcr()
    def test_login_verify(self):
        assert not self.plugin.verify()
        assert self.plugin.login() == LoginResult.CredentialsNotSpecified

        credentials = {'username': '', 'password': ''}
        assert self.plugin.update_credentials(credentials) == LoginResult.CredentialsNotSpecified
        assert not self.plugin.verify()

        credentials = {'username': 'admin', 'password': 'admin'}
        assert self.plugin.update_credentials(credentials) == LoginResult.IncorrentLoginPassword
        assert not self.plugin.verify()

        credentials = {
            'username': helper.real_email,
            'password': helper.real_password
        }

        assert self.plugin.update_credentials(credentials) == LoginResult.Ok
        assert self.plugin.verify()

    def test_login_success(self):
        mock_tracker = LostFilmTVTracker()
        mock_tracker.tracker_settings = self.tracker_settings
        mock_tracker.c_uid = '123456'
        login_mock = Mock()
        mock_tracker.login = login_mock
        self.plugin.tracker = mock_tracker
        self.plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        assert self.plugin.login() == LoginResult.Ok

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_incorrect_login_password(self):
        mock_tracker = LostFilmTVTracker()
        mock_tracker.tracker_settings = self.tracker_settings
        login_mock = Mock(side_effect=LostFilmTVLoginFailedException(3))
        mock_tracker.login = login_mock
        self.plugin.tracker = mock_tracker
        self.plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        assert self.plugin.login() == LoginResult.IncorrentLoginPassword

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_unknown_1(self):
        mock_tracker = LostFilmTVTracker()
        mock_tracker.tracker_settings = self.tracker_settings
        login_mock = Mock(side_effect=LostFilmTVLoginFailedException(1))
        mock_tracker.login = login_mock
        self.plugin.tracker = mock_tracker
        self.plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        assert self.plugin.login() == LoginResult.Unknown

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_login_failed_unknown_2(self):
        mock_tracker = LostFilmTVTracker()
        login_mock = Mock(side_effect=Exception)
        mock_tracker.login = login_mock
        self.plugin.tracker = mock_tracker
        self.plugin.update_credentials({'username': 'monitorrent', 'password': 'monitorrent'})
        assert self.plugin.login() == LoginResult.Unknown

        login_mock.assert_called_with('monitorrent', 'monitorrent')

    def test_check_download(self):
        tracker = LostFilmPlugin()

        response = Response()

        response.status_code = 200
        assert tracker.check_download(response) == Status.Ok

        response.status_code = 302
        response.headers['Location'] = '/'
        assert tracker.check_download(response) == Status.NotFound

        response.status_code = 200
        response._content = ('<!--\r\n'
                             '<meta http-equiv="refresh" content="0; url=/">;\r\n'
                             '//-->').encode('utf-8')
        assert tracker.check_download(response) == Status.NotFound

        response.status_code = 500
        response.headers['Location'] = '/'
        # Should be error even with Location header
        assert tracker.check_download(response) == Status.Error

    @data(('http://www.lostfilm.tv/series/12_Monkeys', True),
          ('http://www.lostfilm.tv/browse.php?cat=236', False),
          ('http://www.lostfilm.tv/my.php', False))
    @unpack
    def test_can_parse_url(self, url, value):
        assert self.plugin.can_parse_url(url) == value

    @use_vcr
    def test_prepare_add_topic_success(self):
        result = self.plugin.prepare_add_topic('http://www.lostfilm.tv/series/12_Monkeys/seasons')

        assert result == {'display_name': u'12 обезьян / 12 Monkeys', 'quality': 'SD'}

    @data('SD', '720p', '1080p')
    @use_vcr
    def test_prepare_add_topic_success_2(self, quality):
        self.plugin.update_credentials(
            {'username': 'monitorrent', 'password': 'monitorrent', 'default_quality': quality})
        result = self.plugin.prepare_add_topic('http://www.lostfilm.tv/series/12_Monkeys/seasons')

        assert result == {'display_name': u'12 обезьян / 12 Monkeys', 'quality': quality}

    @use_vcr
    def test_prepare_add_topic_fail(self):
        assert self.plugin.prepare_add_topic('http://www.lostfilm.tv/series/Unknown') is None

    @requests_mock.Mocker()
    def test_execute_download_all_update_to_latest_success(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')
        # Mr. Robot series
        mocker.get('https://www.lostfilm.tv/series/Mr_Robot/seasons',
                   text=self.read_httpretty_content('Series_Mr_Robot.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=245002012',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=245002011',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=11.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=245&s=2&e=12&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=245&s=2&e=11&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=245&s=2&e=11.html', encoding='utf-8'))

        # Scream series
        mocker.get('https://www.lostfilm.tv/series/Scream/seasons',
                   text=self.read_httpretty_content('Series_Scream.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=251002013',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=11.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=251&s=2&e=13&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=251&s=2&e=13.html', encoding='utf-8'))

        # tracktor.in download all files
        mocker.get(re.compile('http://tracktor.in/td.php(\?s=.*)?'), content=torrent_body,
                   headers={'content-disposition': 'attachment; filename=' + file_name})

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic("https://www.lostfilm.tv/series/Mr_Robot/seasons", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', 245, '720p', 2, 10)
        self._add_topic("https://www.lostfilm.tv/series/Scream/seasons", u'Крик / Scream',
                        'Scream', 251, '720p', 2, 12)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)
        topic2 = self.plugin.get_topic(2)

        assert topic1['season'] == 2
        assert topic1['episode'] == 12

        assert topic2['season'] == 2
        assert topic2['episode'] == 13

    @requests_mock.Mocker()
    def test_execute_cant_download_latest_episode_and_download_without_filename(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')
        # Mr. Robot series
        mocker.get('https://www.lostfilm.tv/series/Mr_Robot/seasons',
                   text=self.read_httpretty_content('Series_Mr_Robot.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=245002012',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=245002011',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=11.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=245&s=2&e=12&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=245&s=2&e=11&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=245&s=2&e=11.html', encoding='utf-8'))

        # Scream series
        mocker.get('https://www.lostfilm.tv/series/Scream/seasons',
                   text=self.read_httpretty_content('Series_Scream.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=251002013',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=11.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=251&s=2&e=13&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=251&s=2&e=13.html', encoding='utf-8'))

        # tracktor.in download all files
        mocker.get(re.compile('http://tracktor.in/td.php(\?s=.*)?'), content=torrent_body,
                   headers={'content-disposition': 'attachment; filename=' + file_name})

        # with filename
        mocker.get(re.compile(re.escape('http://tracktor.in/td.php?s=c245s2e11q720')),
                   content=torrent_body,
                   headers={'content-disposition': 'attachment; filename=' + file_name})
        mocker.get(re.compile(re.escape('http://tracktor.in/td.php?s=c245s2e12q720')),
                   text="Not Found", status_code=404)
        # without filename
        mocker.get(re.compile(re.escape('http://tracktor.in/td.php?s=c251s2e13q720')),
                   content=torrent_body)

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic("http://www.lostfilm.tv/series/Mr_Robot/seasons", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', 245, '720p', 2, 10)
        self._add_topic("http://www.lostfilm.tv/series/Scream/seasons", u'Крик / Scream',
                        'Scream', 251, '720p', 2, 12)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)
        topic2 = self.plugin.get_topic(2)

        assert topic1['season'] == 2
        assert topic1['episode'] == 11

        assert topic2['season'] == 2
        assert topic2['episode'] == 13

    @requests_mock.Mocker()
    def test_execute_nothing_changed(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        mocker.get('https://www.lostfilm.tv/series/Mr_Robot/seasons',
                   text=self.read_httpretty_content('Series_Mr_Robot.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/series/Scream/seasons',
                   text=self.read_httpretty_content('Series_Scream.html', encoding='utf-8'))

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic("https://www.lostfilm.tv/series/Mr_Robot/seasons", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', 245, '720p', 2, 12)
        self._add_topic("https://www.lostfilm.tv/series/Scream/seasons", u'Крик / Scream',
                        'Scream', 251, '720p', 2, 13)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)
        topic2 = self.plugin.get_topic(2)

        assert topic1['season'] == 2
        assert topic1['episode'] == 12

        assert topic2['season'] == 2
        assert topic2['episode'] == 13

    @requests_mock.Mocker()
    def test_execute_cant_get_quality(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """

        mocker.get('https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons',
                   text=self.read_httpretty_content('Series_Legend_of_the_Seeker.html', encoding='utf-8'))

        mocker.get('https://www.lostfilm.tv/v_search.php?a=98002022',
                   text=self.read_httpretty_content('v_search.php_c=98&s=2&e=22.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=98&s=2&e=22&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=98&s=2&e=22.html', encoding='utf-8'))

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic(u"https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons",
                        u'Легенда об Искателе / Legend of the Seeker',
                        u'Legend of the Seeker', 98, '720p', 2, 21)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)

        assert topic1['season'] == 2
        assert topic1['episode'] == 21

    @requests_mock.Mocker()
    def test_execute_not_found_status(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        mocker.get('https://www.lostfilm.tv/series/Boardwalk_Empire/seasons', status_code=200,
                   text=self.read_httpretty_content('lostfilm_redirect_to_root.html', encoding='utf-8'))

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic(u"https://www.lostfilm.tv/series/Boardwalk_Empire/seasons",
                        u'Подпольная Империя / Broadwalk Empire',
                        u'Broadwalk Empire', 131, '720p', 1, 12)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic = self.plugin.get_topic(1)

        assert topic['season'] == 1
        assert topic['episode'] == 12
        assert topic['status'] == Status.NotFound

    @requests_mock.Mocker()
    def test_execute_download_html_should_fail(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        mocker.get('https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons',
                   text=self.read_httpretty_content('Series_Legend_of_the_Seeker.html', encoding='utf-8'))

        mocker.get('https://www.lostfilm.tv/v_search.php?a=98002022',
                   text=self.read_httpretty_content('v_search.php_c=98&s=2&e=22.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=98&s=2&e=22&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=98&s=2&e=22.html', encoding='utf-8'))
        mocker.get('http://tracktor.in/td.php?s=c98s2e22q480', text='<html>HTML</html>')

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic(u"https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons",
                        u'Легенда об Искателе / Legend of the Seeker',
                        u'Legend of the Seeker', 98, 'SD', 2, 21)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)

        assert topic1['season'] == 2
        assert topic1['episode'] == 21
        assert topic1['status'] == Status.Ok

    @requests_mock.Mocker()
    def test_execute_error_status(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        mocker.register_uri(requests_mock.GET, 'https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons',
                            status_code=500,
                            text='<error>Backend Error</error>')

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        self._add_topic(u"https://www.lostfilm.tv/series/Legend_of_the_Seeker/seasons",
                        u'Легенда об Искателе / Legend of the Seeker',
                        u'Legend of the Seeker', 98, '720p', 2, 21)

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)

        assert topic1['season'] == 2
        assert topic1['episode'] == 21
        assert topic1['status'] == Status.Error

    @requests_mock.Mocker()
    def test_execute_download_latest_one_only(self, mocker):
        """
        :type mocker: requests_mock.Mocker
        """
        file_name = 'Hell.On.Wheels.S05E02.720p.WEB.rus.LostFilm.TV.mp4.torrent'
        torrent_body = self.read_httpretty_content(file_name, 'rb')

        self.plugin.tracker.setup(helper.real_session)
        self.plugin._execute_login = Mock(return_value=True)

        # Mr. Robot series
        mocker.get('https://www.lostfilm.tv/series/Mr_Robot/seasons',
                   text=self.read_httpretty_content('Series_Mr_Robot.html', encoding='utf-8'))
        mocker.get('https://www.lostfilm.tv/v_search.php?a=245002012',
                   text=self.read_httpretty_content('v_search.php_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.get(re.compile(u'http://retre.org/v3/(index\.php)?\?c=245&s=2&e=12&u=\d+&h=[a-z0-9]+&n=\d+'),
                   text=self.read_httpretty_content('reTre.org_v3_c=245&s=2&e=12.html', encoding='utf-8'))
        mocker.register_uri(requests_mock.GET, 'http://tracktor.in/td.php?s=c245s2e12q720', content=torrent_body,
                            headers={'content-disposition': 'attachment; filename=' + file_name})

        self._add_topic("http://www.lostfilm.tv/series/Mr_Robot/seasons", u'Мистер Робот / Mr. Robot',
                        'Mr. Robot', 245, '720p')

        # noinspection PyTypeChecker
        self.plugin.execute(self.plugin.get_topics(None), EngineMock())

        topic1 = self.plugin.get_topic(1)

        assert topic1['season'] == 2
        assert topic1['episode'] == 12

    def test_execute_login_failed(self):
        execute_login_mock = Mock(return_value=False)
        self.plugin._execute_login = execute_login_mock
        engine_mock = EngineMock()
        # noinspection PyTypeChecker
        self.plugin.execute(None, engine_mock)

        execute_login_mock.assert_called_with(engine_mock)

    @data((1, 10, 'S01E10'),
          (10, 9, 'S10E09'),
          (1, None, 'S01'),
          (11, None, 'S11'),
          (None, None, None))
    @unpack
    def test_get_topic_info(self, season, episode, expected):
        topic = LostFilmTVSeries(season=season, episode=episode)
        info = self.plugin.get_topic_info(topic)
        assert info == expected

    @data((LostFilmShow('Russian', u'Русский', "Russian", 666), u'Русский / Russian'),
          (LostFilmShow('Not Parsed', None, 'Not_Parsed', 666), u'Not Parsed'))
    @unpack
    def test_get_display_name(self, parsed_url, expected):
        # noinspection PyProtectedMember
        display_name = self.plugin._get_display_name(parsed_url)
        self.assertEqual(expected, display_name)

    @use_vcr()
    def test_parse_not_found_url(self):
        result = self.plugin.parse_url("https://www.lostfilm.tv/series/Boardwalk_Empire")
        assert result is None

    @use_vcr()
    def test_parse_url(self):
        result = self.plugin.parse_url("http://www.lostfilm.tv/series/Sherlock")
        assert result is not None
        assert result.russian_name == u'Шерлок'
        assert result.original_name == u'Sherlock'
        assert result.seasons_url == 'https://www.lostfilm.tv/series/Sherlock/seasons'

    def _add_topic(self, url, display_name, search_name, cat, quality, season=None, episode=None):
        with DBSession() as db:
            topic = LostFilmTVSeries()
            topic.url = url
            topic.display_name = display_name
            topic.search_name = search_name
            topic.cat = cat
            topic.season = season
            topic.episode = episode
            topic.quality = quality
            db.add(topic)
            db.commit()
            return topic.id
