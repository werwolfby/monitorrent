from builtins import object
import json
import falcon
from mock import MagicMock
from ddt import ddt, data

from monitorrent.plugins.clients import DownloadStatus, TorrentDownloadStatus
from tests import RestTestBase
from monitorrent.rest.clients import ClientCollection, Client, ClientCheck, DefaultClient, ClientDefault, TorrentStatus, \
    ClientStatus
from monitorrent.plugin_managers import ClientsManager


@ddt
class ClientCollectionTest(RestTestBase):
    class TestClient(object):
        name = 'test_client'
        form = {}
        SUPPORTED_FIELDS = []

        def get_settings(self):
            return {}

    def test_get_all(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})

        client_collection = ClientCollection(clients_manager)
        self.api.add_route('/api/clients', client_collection)

        body = self.simulate_request('/api/clients', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0], {'name': 'test', 'form': ClientCollectionTest.TestClient.form, 'is_default': True})


class ClientTest(RestTestBase):
    def test_get_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        settings = {'login': 'login'}
        clients_manager.get_settings = MagicMock(return_value=settings)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        body = self.simulate_request('/api/clients/{0}'.format(1), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, settings)

    def test_empty_get_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_settings = MagicMock(return_value=None)

        client = Client(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}', client)

        body = self.simulate_request('/api/clients/{0}'.format(1), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_not_found_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_settings = MagicMock(side_effect=KeyError)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        self.simulate_request('/api/clients/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_error_get_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_settings = MagicMock(side_effect=Exception)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        self.simulate_request('/api/clients/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.set_settings = MagicMock(return_value=True)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        self.simulate_request('/api/clients/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.set_settings = MagicMock(side_effect=KeyError)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        self.simulate_request('/api/clients/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_error_update_settings(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.set_settings = MagicMock(side_effect=Exception)

        client = Client(clients_manager)
        self.api.add_route('/api/clients/{client}', client)

        self.simulate_request('/api/clients/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class TorrentStatusTest(RestTestBase):
    def test_get_download_status_by_hash(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_download_status_by_id = MagicMock(return_value=DownloadStatus(1, 2, 3, 4,
                                                                                          TorrentDownloadStatus.Unknown,
                                                                                          5, 6))

        client = TorrentStatus(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/torrent/status/{torrent_hash}', client)

        body = self.simulate_request('/api/clients/torrent/status/{0}'.format("hash"), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)
        assert result['downloaded_bytes'] == 1
        assert result['total_bytes'] == 2
        assert result['download_speed'] == 3
        assert result['upload_speed'] == 4

@ddt
class ClientStatusTest(RestTestBase):
    def test_get_download_status(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_download_status = MagicMock(return_value={"torrent": DownloadStatus(1, 2, 3, 4,
                                                                                                TorrentDownloadStatus
                                                                                                .Unknown, 5, 6)})

        client = ClientStatus(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/status', client)

        body = self.simulate_request('/api/clients/{0}/status'.format("client"), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)
        torrent = result["torrent"]
        assert torrent['downloaded_bytes'] == 1
        assert torrent['total_bytes'] == 2
        assert torrent['download_speed'] == 3
        assert torrent['upload_speed'] == 4

    def test_check_client_not_found(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_download_status = MagicMock(side_effect=KeyError)

        client = ClientStatus(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/status', client)

        self.simulate_request('/api/clients/{0}/status'.format("client"))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_check_client_error(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.get_download_status = MagicMock(side_effect=Exception)

        client = ClientStatus(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/status', client)

        self.simulate_request('/api/clients/{0}/status'.format("client"))
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class CheckClientTest(RestTestBase):
    @data(True, False)
    def test_check_client(self, value):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.check_connection = MagicMock(return_value=value)

        client = ClientCheck(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/check', client)

        body = self.simulate_request('/api/clients/{0}/check'.format('tracker.org'), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'status': value})

    def test_check_client_not_found(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.check_connection = MagicMock(side_effect=KeyError)

        client = ClientCheck(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/check', client)

        self.simulate_request('/api/clients/{0}/check'.format('tracker.org'))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_check_client_error(self):
        clients_manager = ClientsManager({'test': ClientCollectionTest.TestClient()})
        clients_manager.check_connection = MagicMock(side_effect=Exception)

        client = ClientCheck(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/check', client)

        self.simulate_request('/api/clients/{0}/check'.format('tracker.org'))
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


class DefaultClientTest(RestTestBase):
    class TestClientWithFields(object):
        name = 'test_client_with_fields'
        form = {}
        SUPPORTED_FIELDS = ['download_dir', 'other']

        def get_settings(self):
            return {}

        def get_download_dir(self):
            return u'/mnt/media/download'

    def test_get_default(self):
        clients_manager = ClientsManager({'tracker.org': ClientCollectionTest.TestClient()})

        client = DefaultClient(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/default_client', client)

        body = self.simulate_request('/api/default_client', decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        result = json.loads(body)

        assert result == {'name': 'test_client', 'settings': {}, 'fields': {}}

    def test_get_default_with_fields(self):
        clients_manager = ClientsManager({'tracker.org': self.TestClientWithFields()})

        client = DefaultClient(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/default_client', client)

        body = self.simulate_request('/api/default_client', decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        result = json.loads(body)

        expected_fields = {
            'download_dir': u'/mnt/media/download',
            'other': None
        }
        assert result == {'name': 'test_client_with_fields', 'settings': {}, 'fields': expected_fields}

    def test_get_default_not_found(self):
        clients_manager = ClientsManager({'tracker.org': ClientCollectionTest.TestClient()})
        clients_manager.default_client = None

        client = DefaultClient(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/default_client', client)

        body = self.simulate_request('/api/default_client', decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)


class ClientDefaultTest(RestTestBase):
    def test_set_default(self):
        clients_manager = ClientsManager({'tracker.org': ClientCollectionTest.TestClient()})

        client = ClientDefault(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/default', client)

        self.simulate_request('/api/clients/{0}/default'.format('tracker.org'), method='PUT')
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_set_default_not_found(self):
        clients_manager = ClientsManager({'tracker.org': ClientCollectionTest.TestClient()})

        client = ClientDefault(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/default', client)

        self.simulate_request('/api/clients/{0}/default'.format('random.org'), method='PUT')
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_set_default_on_error(self):
        clients_manager = ClientsManager({'tracker.org': ClientCollectionTest.TestClient()})
        clients_manager.set_default = MagicMock(side_effect=Exception)

        client = ClientDefault(clients_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/clients/{client}/default', client)

        self.simulate_request('/api/clients/{0}/default'.format('tracker.org'), method='PUT')
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)