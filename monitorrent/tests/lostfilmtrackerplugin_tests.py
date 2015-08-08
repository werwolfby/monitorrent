# coding=utf-8
from monitorrent.db import init_db_engine, create_db, close_db
from monitorrent.plugins.trackers.lostfilm import LostFilmPlugin
from monitorrent.plugins.trackers import LoginResult
from unittest import TestCase
from monitorrent.tests import use_vcr
from monitorrent.tests.lostfilmtracker_helper import LostFilmTrackerHelper
from monitorrent.engine import Logger
import datetime

helper = LostFilmTrackerHelper()


class EngineMock(object):
    log = Logger()

    def add_torrent(self, filename, torrent, old_hash):
        return datetime.datetime.now()


class LostFilmTrackerPluginTest(TestCase):
    def setUp(self):
        init_db_engine("sqlite:///:memory:", echo=True)
        create_db()

    def tearDown(self):
        close_db()

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

    @helper.use_vcr()
    def test_execute(self):
        plugin = LostFilmPlugin()
        credentials = {
            'username': helper.real_login,
            'password': helper.real_password
        }
        plugin.update_credentials(credentials)

        self.assertTrue(plugin.add_topic("http://www.lostfilm.tv/browse.php?cat=245",
                                         {'display_name': 'Mr. Robot', 'quality': '720p'}))
        self.assertTrue(plugin.add_topic("http://www.lostfilm.tv/browse.php?cat=251",
                                         {'display_name': 'Scream', 'quality': '720p'}))

        plugin.execute(None, EngineMock())

        topic1 = plugin.get_topic(1)
        topic2 = plugin.get_topic(2)

        self.assertEqual(topic1['season'], 1)
        self.assertEqual(topic1['episode'], 7)

        self.assertEqual(topic2['season'], 1)
        self.assertEqual(topic2['episode'], 6)
