from datetime import datetime

import pytest
import pytz
import json
from ddt import ddt
from pytz import reference
from requests import Response
from requests_mock import Mocker

import monitorrent.plugins.trackers
from monitorrent.plugins.clients import TopicSettings
from monitorrent.plugins.clients.qbittorrent import QBittorrentClientPlugin
from tests import DbTestCase, use_vcr
from mock import patch, Mock


@ddt
class QBittorrentPluginTest(DbTestCase):
    real_host = "http://localhost"
    real_port = 8080
    real_login = "admin"
    real_password = "password"

    bad_host = "http://fake.com"
    bad_port = 1234
    bad_login = "fake"
    bad_password = "more_fake"

    def test_settings(self):
        plugin = QBittorrentClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        self.assertEqual({'host': 'localhost', 'port': None, 'username': 'monitorrent'}, readed_settings)

    @use_vcr
    def test_check_connection_successfull(self):
        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        self.assertTrue(plugin.check_connection())

    @patch('requests.Session.post')
    def test_check_connection_failed(self, post_mock):
        response = Response()
        response.status_code = 404
        post_mock.return_value = response

        plugin = QBittorrentClientPlugin()
        self.password_ = {'host': self.bad_host, 'port': self.bad_port, 'username': self.bad_login,
                          'password': self.bad_password}
        settings = self.password_
        plugin.set_settings(settings)
        self.assertFalse(plugin.check_connection())

    @use_vcr
    @patch("requests.Session.get")
    def test_find_torrent(self, get_mock):
        response = Response()
        response._content = b'[{"added_on":"2016-04-09T20:24:17","completion_on":null,"dlspeed":0,"eta":8640000,"f_l_piece_prio":false,"force_start":false,"hash":"d27c8e30f0c12afe84735b57f6463266b118acea","label":"","name":"Ment.v.zakone.9.2015.HDTVRip.Files-x","num_complete":12,"num_incomplete":42,"num_leechs":0,"num_seeds":0,"priority":1,"progress":0.073527365922927856,"ratio":0.022764846784523337,"save_path":"Downloads","seq_dl":false,"size":5776162816,"state":"pausedDL","super_seeding":false,"upspeed":0}]'
        get_mock.return_value = response

        plugin = QBittorrentClientPlugin()
        torrent_hash = "D27C8E30F0C12AFE84735B57F6463266B118ACEA"
        settings = {'host': self.real_host, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        torrent = plugin.find_torrent(torrent_hash)
        self.assertEqual(torrent['date_added'], datetime(2016, 4, 9, 20, 24, 17, tzinfo=pytz.reference.Local))
        self.assertEqual(torrent['name'], 'Ment.v.zakone.9.2015.HDTVRip.Files-x')

    @use_vcr
    @patch("requests.Session.get")
    def test_find_torrent_for_33_version(self, get_mock):
        response = Response()
        response._content = b'[{"added_on":1481781596,"completion_on":null,"dlspeed":0,"eta":8640000,"f_l_piece_prio":false,"force_start":false,"hash":"d27c8e30f0c12afe84735b57f6463266b118acea","label":"","name":"Ment.v.zakone.9.2015.HDTVRip.Files-x","num_complete":12,"num_incomplete":42,"num_leechs":0,"num_seeds":0,"priority":1,"progress":0.073527365922927856,"ratio":0.022764846784523337,"save_path":"Downloads","seq_dl":false,"size":5776162816,"state":"pausedDL","super_seeding":false,"upspeed":0}]'
        get_mock.return_value = response

        plugin = QBittorrentClientPlugin()
        torrent_hash = "D27C8E30F0C12AFE84735B57F6463266B118ACEA"
        settings = {'host': self.real_host, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        torrent = plugin.find_torrent(torrent_hash)
        self.assertEqual(torrent['date_added'], datetime(2016, 12, 15, 5, 59, 56, tzinfo=pytz.reference.utc))
        self.assertEqual(torrent['name'], 'Ment.v.zakone.9.2015.HDTVRip.Files-x')

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_find_torrent_failed(self, post_mock, get_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200
        post_mock.return_value = response
        get_mock.side_effect = Exception('boom')

        plugin = QBittorrentClientPlugin()
        torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)
        with pytest.raises(Exception) as e:
            torrent = plugin.find_torrent(torrent_hash)

    def test_find_torrent_no_settings(self):
        with patch.object(monitorrent.plugins.clients.qbittorrent.requests.Session, 'post', side_effect=Exception):
            plugin = QBittorrentClientPlugin()
            torrent_hash = "8347DD6415598A7409DFC3D1AB95078F959BFB93"
            settings = {'host': self.bad_host, 'port': self.bad_port, 'username': self.bad_login,
                        'password': self.bad_password}
            plugin.set_settings(settings)
            torrent = plugin.find_torrent(torrent_hash)
            self.assertFalse(torrent)

    def test_add_torrent_bad_settings(self):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.add_torrent(torrent, None))

    @patch('requests.Session.post')
    def test_add_torrent_failed(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200

        post_mock.side_effect = [response, Exception('boom')]

        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        with pytest.raises(Exception) as e:
            plugin.add_torrent(torrent, None)

    @patch('requests.Session.post')
    def test_add_torrent_success(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200
        good_response = Response()
        good_response.status_code = 200
        post_mock.side_effect = [response, good_response]

        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.add_torrent(torrent, None))

    @patch('requests.Session.post')
    def test_add_torrent_with_settings_success(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200
        good_response = Response()
        good_response.status_code = 200
        post_mock.side_effect = [response, good_response]

        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.add_torrent(torrent, TopicSettings("/path/to/download")))

    def test_remove_torrent_bad_settings(self):
        plugin = QBittorrentClientPlugin()
        torrent = b'torrent'
        self.assertFalse(plugin.remove_torrent(torrent))

    @patch('requests.Session.post')
    def test_remove_torrent_failed(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200

        post_mock.side_effect = [response, Exception('boom')]

        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        with pytest.raises(Exception) as e:
            plugin.remove_torrent(torrent)

    @patch('requests.Session.post')
    def test_remove_torrent_success(self, post_mock):
        response = Response()
        response._content = b"Ok."
        response.status_code = 200
        good_response = Response()
        good_response.status_code = 200
        post_mock.side_effect = [response, good_response]

        plugin = QBittorrentClientPlugin()
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        torrent = b'torrent'
        self.assertTrue(plugin.remove_torrent(torrent))

    @Mocker()
    def test_get_download_dir_success(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        preferences = {'save_path': u'/mnt/media/downloads'}
        mocker.get(target + "query/preferences", text=json.dumps(preferences))

        plugin = QBittorrentClientPlugin()

        assert plugin.get_download_dir() is None

        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin.set_settings(settings)

        assert plugin.get_download_dir() == u'/mnt/media/downloads'

    @Mocker()
    def test_get_download_dir_error(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        error = {'error': 500}
        mocker.get(target + "query/preferences", status_code=500, text=json.dumps(error))

        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}

        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        with pytest.raises(Exception) as e:
            plugin.get_download_dir()

    @Mocker()
    def test_should_get_download_status_by_hash_successfully(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        hash_string = 'hash'

        mocker.get(target + "query/propertiesGeneral/" + hash_string,
                   status_code=200,
                   text="{\"addition_date\":1487792728,\"comment\":\"\",\"completion_date\":-1,\"created_by\":\"\","
                        "\"creation_date\":1487792646,\"dl_limit\":-1,\"dl_speed\":5990252,\"dl_speed_avg\":5851317,"
                        "\"eta\":1025,\"last_seen\":1487792930,\"nb_connections\":16,\"nb_connections_limit\":100,"
                        "\"peers\":2,\"peers_total\":15,\"piece_size\":8388608,\"pieces_have\":136,"
                        "\"pieces_num\":871,\"reannounce\":2849,"
                        "\"save_path\":\"C:\\\\Users\\\\DSilence\\\\Downloads\\\\test_dir\\\\\",\"seeding_time\":0,"
                        "\"seeds\":14,\"seeds_total\":16,\"share_ratio\":0.015455593117895568,\"time_elapsed\":202,"
                        "\"total_downloaded\":1187817372,\"total_downloaded_session\":1187817372,"
                        "\"total_size\":7299496252,\"total_uploaded\":18358422,\"total_uploaded_session\":18358422,"
                        "\"total_wasted\":110,\"up_limit\":-1,\"up_speed\":129319,\"up_speed_avg\":90435}")
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        result = plugin.get_download_status_by_hash(hash_string)
        assert result.upload_speed == 129319
        assert result.download_speed == 5990252
        assert result.downloaded_bytes == 1187817372
        assert result.total_bytes == 7299496252

    @Mocker()
    def test_should_fail_download_status_by_hash_when_not_logged_in(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Fails.")

        hash_string = 'hash'

        mocker.get(target + "query/propertiesGeneral/" + hash_string,
                   status_code=200,
                   text="{\"addition_date\":1487792728,\"comment\":\"\",\"completion_date\":-1,\"created_by\":\"\","
                        "\"creation_date\":1487792646,\"dl_limit\":-1,\"dl_speed\":5990252,\"dl_speed_avg\":5851317,"
                        "\"eta\":1025,\"last_seen\":1487792930,\"nb_connections\":16,\"nb_connections_limit\":100,"
                        "\"peers\":2,\"peers_total\":15,\"piece_size\":8388608,\"pieces_have\":136,"
                        "\"pieces_num\":871,\"reannounce\":2849,"
                        "\"save_path\":\"C:\\\\Users\\\\sad\\\\tmp\\\\test_dir\\\\\",\"seeding_time\":0,"
                        "\"seeds\":14,\"seeds_total\":16,\"share_ratio\":0.015455593117895568,\"time_elapsed\":202,"
                        "\"total_downloaded\":1187817372,\"total_downloaded_session\":1187817372,"
                        "\"total_size\":7299496252,\"total_uploaded\":18358422,\"total_uploaded_session\":18358422,"
                        "\"total_wasted\":110,\"up_limit\":-1,\"up_speed\":129319,\"up_speed_avg\":90435}")
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        assert plugin.get_download_status_by_hash(hash_string) is False

    @Mocker()
    def test_should_fail_when_download_status_by_hash_wasnt_retrieved(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        error = {'error': 500}
        hash_string = 'hash'
        mocker.get(target + "query/propertiesGeneral/" + hash_string, status_code=500, text=json.dumps(error))

        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}

        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        with pytest.raises(Exception) as e:
            plugin.get_download_status_by_hash(hash_string)

    @Mocker()
    def test_should_get_download_status_successfully(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        mocker.get(target + "query/torrents/",
                   status_code = 200,
                   text='[{"added_on":1489778322,"category":"","completion_on":4294967295,"dlspeed":5242223,'
                          '"eta":8640000,"f_l_piece_prio":false,"force_start":false,'
                          '"hash":"1bc6e893df6ee2d5b84aa41bb5cf4e189112a8a7",'
                          '"name":"en_windows_10_pro_10240_x64_dvd","num_complete":28,"num_incomplete":2,'
                          '"num_leechs":0,"num_seeds":0,"priority":1,"progress":0.20,"ratio":0,'
                          '"save_path":"C:\\\\Users\\\\DSilence\\\\Downloads\\\\","seq_dl":false,"size":3992293376,'
                          '"state":"pausedDL","super_seeding":false,"upspeed":0}]')
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                   'password': self.real_password}
        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        expected_key = '1bc6e893df6ee2d5b84aa41bb5cf4e189112a8a7'
        status = plugin.get_download_status()
        assert expected_key in status
        result = status[expected_key]
        assert result.upload_speed == 0
        assert result.download_speed == 5242223
        assert result.downloaded_bytes == 798458675.2
        assert result.total_bytes == 3992293376

    @Mocker()
    def test_should_fail_download_status_when_not_logged_in(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Fails.")

        mocker.get(target + "query/torrents/",
                   status_code=200,
                   text='[{"added_on":1489778322,"category":"","completion_on":4294967295,"dlspeed":5242223,'
                        '"eta":8640000,"f_l_piece_prio":false,"force_start":false,'
                        '"hash":"1bc6e893df6ee2d5b84aa41bb5cf4e189112a8a7",'
                        '"name":"en_windows_10_pro_10240_x64_dvd","num_complete":28,"num_incomplete":2,'
                        '"num_leechs":0,"num_seeds":0,"priority":1,"progress":0.20,"ratio":0,'
                        '"save_path":"C:\\\\Users\\\\DSilence\\\\Downloads\\\\","seq_dl":false,"size":3992293376,'
                        '"state":"pausedDL","super_seeding":false,"upspeed":0}]')
        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}
        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        assert plugin.get_download_status() is False

    @Mocker()
    def test_should_fail_when_download_status_wasnt_retrieved(self, mocker):
        target = "{0}:{1}/".format(self.real_host, self.real_port)

        mocker.post(target + "login", text="Ok.")

        error = {'error': 500}
        mocker.get(target + "query/torrents/", status_code=500, text=json.dumps(error))

        settings = {'host': self.real_host, 'port': self.real_port, 'username': self.real_login,
                    'password': self.real_password}

        plugin = QBittorrentClientPlugin()
        plugin.set_settings(settings)

        with pytest.raises(Exception) as e:
            plugin.get_download_status()
