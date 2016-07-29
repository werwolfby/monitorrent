from builtins import object
import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from tests import RestTestBase
from monitorrent.rest.trackers import TrackerCollection, Tracker, TrackerCheck
from monitorrent.plugin_managers import TrackersManager
from monitorrent.plugins.trackers import WithCredentialsMixin, TrackerPluginBase, TrackerSettings


class TrackersManagerMixin(object):
    tracker_manager = None

    def trackers_manager_set_up(self):
        self.tracker_manager = TrackersManager(TrackerSettings(10, None), {'test': TrackerCollectionTest.TestTracker()})


@ddt
class TrackerCollectionTest(RestTestBase, TrackersManagerMixin):
    class TestTracker(WithCredentialsMixin, TrackerPluginBase):
        def verify(self):
            return True

        def login(self):
            pass

        def _prepare_request(self, **kwargs):
            pass

        def can_parse_url(self, **kwargs):
            pass

        def parse_url(self, **kwargs):
            pass

    def setUp(self, disable_auth=True):
        super(TrackerCollectionTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_get_all(self):
        tracker_collection = TrackerCollection(self.tracker_manager)
        self.api.add_route('/api/trackers', tracker_collection)

        body = self.simulate_request('/api/trackers', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0], {'name': 'test', 'form': WithCredentialsMixin.credentials_form})


class TrackerTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TrackerTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_get_settings(self):
        settings = {'login': 'login'}
        self.tracker_manager.get_settings = MagicMock(return_value=settings)

        tracker = Tracker(self.tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        body = self.simulate_request('/api/trackers/{0}'.format(1), decode='utf-8')
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, settings)

    def test_empty_get_settings(self):
        self.tracker_manager.get_settings = MagicMock(return_value=None)

        tracker = Tracker(self.tracker_manager)
        tracker.__no_auth__ = True
        self.api.add_route('/api/trackers/{tracker}', tracker)

        body = self.simulate_request('/api/trackers/{0}'.format(1), decode='utf-8')
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_not_found_settings(self):
        self.tracker_manager.get_settings = MagicMock(side_effect=KeyError)

        tracker = Tracker(self.tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_settings(self):
        self.tracker_manager.set_settings = MagicMock(return_value=True)

        tracker = Tracker(self.tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_settings(self):
        self.tracker_manager.set_settings = MagicMock(side_effect=KeyError)

        tracker = Tracker(self.tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_settings(self):
        self.tracker_manager.set_settings = MagicMock(return_value=False)

        tracker = Tracker(self.tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)


@ddt
class CheckTrackersTest(RestTestBase, TrackersManagerMixin):
    @staticmethod
    def raise_key_error(*args, **kwargs):
        raise KeyError()

    def setUp(self, disable_auth=True):
        super(CheckTrackersTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    @data(True, False)
    def test_check_client(self, value):
        self.tracker_manager.check_connection = MagicMock(return_value=value)

        client = TrackerCheck(self.tracker_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/trackers/{tracker}/check', client)

        body = self.simulate_request('/api/trackers/{0}/check'.format('tracker.org'), decode='utf-8')
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'status': value})

    def test_check_client_not_found(self):
        self.tracker_manager.check_connection = MagicMock(side_effect=KeyError)

        client = TrackerCheck(self.tracker_manager)
        client.__no_auth__ = True
        self.api.add_route('/api/trackers/{tracker}/check', client)

        self.simulate_request('/api/trackers/{0}/check'.format('tracker.org'))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
