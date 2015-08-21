import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.trackers import TrackerCollection, Tracker
from monitorrent.plugin_managers import TrackersManager
from monitorrent.plugins.trackers import TrackerPluginWithCredentialsBase


@ddt
class TopicCollectionTest(RestTestBase):
    class TestTracker(TrackerPluginWithCredentialsBase):
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

    def test_get_all(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})

        tracker_collection = TrackerCollection(tracker_manager)
        self.api.add_route('/api/trackers', tracker_collection)

        body = self.simulate_request('/api/trackers')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0], {'name': 'test', 'form': TrackerPluginWithCredentialsBase.credentials_form})


class TrackerTest(RestTestBase):
    def raise_key_error(self, *args, **kwargs):
        raise KeyError()

    def test_get_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        settings = {'login': 'login'}
        tracker_manager.get_settings = MagicMock(return_value=settings)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        body = self.simulate_request('/api/trackers/{0}'.format(1))
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, dict)
        self.assertEqual(result, settings)

    def test_empty_get_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        tracker_manager.get_settings = MagicMock(return_value=None)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        body = self.simulate_request('/api/trackers/{0}'.format(1))
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_not_found_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        tracker_manager.get_settings = MagicMock(side_effect=self.raise_key_error)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        tracker_manager.set_settings = MagicMock(return_value=True)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        tracker_manager.set_settings = MagicMock(side_effect=self.raise_key_error)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_settings(self):
        tracker_manager = TrackersManager({'test': TopicCollectionTest.TestTracker()})
        tracker_manager.set_settings = MagicMock(return_value=False)

        tracker = Tracker(tracker_manager)
        self.api.add_route('/api/trackers/{tracker}', tracker)

        self.simulate_request('/api/trackers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
