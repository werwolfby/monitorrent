import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic
from monitorrent.plugin_managers import TrackersManager


@ddt
class TopicCollectionTest(RestTestBase):
    def test_get_all(self):
        tracker_manager = TrackersManager()
        topic1 = {'id': 1, 'url': 'http://1', 'display_name': '1', 'last_update': None}
        tracker_manager.get_watching_torrents = MagicMock(return_value=[topic1])

        topic_collection = TopicCollection(tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        body = self.simulate_request('/api/topics')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0], topic1)

    def test_successful_add_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.add_topic = MagicMock(return_value=True)

        topic_collection = TopicCollection(tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        request = {'url': 'http://1', 'settings': {}}

        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_CREATED)

    @data({'url': 'http://1'}, {'settings': {'display_name': '1'}})
    def test_failed_add_topic(self, request):
        tracker_manager = TrackersManager()
        tracker_manager.add_topic = MagicMock(return_value=True)

        topic_collection = TopicCollection(tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_failed_tracker_add_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.add_topic = MagicMock(return_value=False)

        topic_collection = TopicCollection(tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        request = {'url': 'http://1', 'settings': {}}
        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class TopicParseTest(RestTestBase):
    def test_success_parse(self):
        tracker_manager = TrackersManager()
        topic = {'display_name': '1', 'form': {}}
        tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        body = self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url': 'http://1'})[1:])
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, dict)
        self.assertEqual(result, topic)

    def test_failed_parse(self):
        tracker_manager = TrackersManager()
        tracker_manager.prepare_add_topic = MagicMock(return_value=False)

        topic_parse = TopicParse(tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url': 'http://1'})[1:])
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_failed_parse_1(self):
        tracker_manager = TrackersManager()
        topic = {'display_name': '1', 'form': {}}
        tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url1': 'http://1'})[1:])
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_failed_parse_2(self):
        tracker_manager = TrackersManager()
        topic = {'display_name': '1', 'form': {}}
        tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])


@ddt
class TopicTest(RestTestBase):
    def raise_key_error(self, *args, **kwargs):
        raise KeyError()

    def test_successful_get_topic(self):
        tracker_manager = TrackersManager()
        topic = {'id': 1, 'display_name': '1', 'last_update': None, 'type': 'plugin'}
        tracker_manager.get_topic = MagicMock(return_value=topic)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        body = self.simulate_request("/api/topic/{0}".format(1))
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertIsInstance(result, dict)
        self.assertEqual(result, topic)

    def test_not_found_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.get_topic = MagicMock(side_effect=self.raise_key_error)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.update_watch = MagicMock(return_value=True)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.update_watch = MagicMock(side_effect=self.raise_key_error)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.update_watch = MagicMock(return_value=False)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)

    def test_successful_delete_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.remove_topic = MagicMock(return_value=True)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_delete_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.remove_topic = MagicMock(side_effect=self.raise_key_error)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_delete_topic(self):
        tracker_manager = TrackersManager()
        tracker_manager.remove_topic = MagicMock(return_value=False)

        topic_parse = Topic(tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)
