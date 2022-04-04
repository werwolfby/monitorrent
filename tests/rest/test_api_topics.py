from builtins import object
import json
import falcon
from mock import MagicMock, Mock
from ddt import ddt, data
from tests import RestTestBase
from monitorrent.rest.topics import TopicCollection, TopicParse, Topic, TopicResetStatus, TopicPauseState
from monitorrent.plugins.trackers import TrackerSettings
from monitorrent.plugin_managers import TrackersManager


class TrackersManagerMixin(object):
    tracker_manager = None

    def trackers_manager_set_up(self):
        tracker_settings = TrackerSettings(10, 30000, None)
        settings_manager = Mock()
        settings_manager.tracker_settings = tracker_settings

        # noinspection PyTypeChecker
        self.tracker_manager = TrackersManager(settings_manager, None)


@ddt
class TopicCollectionTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TopicCollectionTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_get_all(self):
        topic1 = {'id': 1, 'url': 'http://1', 'display_name': '1', 'last_update': None}
        self.tracker_manager.get_watching_topics = MagicMock(return_value=[topic1])

        topic_collection = TopicCollection(self.tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        body = self.simulate_request('/api/topics', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0], topic1)

    def test_successful_add_topic(self):
        self.tracker_manager.add_topic = MagicMock(return_value=True)

        topic_collection = TopicCollection(self.tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        request = {'url': 'http://1', 'settings': {}}

        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_CREATED)

    @data({'url': 'http://1'}, {'settings': {'display_name': '1'}})
    def test_failed_add_topic(self, request):
        self.tracker_manager.add_topic = MagicMock(return_value=True)

        topic_collection = TopicCollection(self.tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_failed_tracker_add_topic(self):
        self.tracker_manager.add_topic = MagicMock(return_value=False)

        topic_collection = TopicCollection(self.tracker_manager)
        self.api.add_route('/api/topics', topic_collection)

        request = {'url': 'http://1', 'settings': {}}
        self.simulate_request('/api/topics', method="POST", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class TopicParseTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TopicParseTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_success_parse(self):
        topic = {'display_name': '1', 'form': {}}
        self.tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(self.tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        body = self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url': 'http://1'})[1:],
                                     decode='utf-8')
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, topic)

    def test_failed_parse(self):
        self.tracker_manager.prepare_add_topic = MagicMock(return_value=False)

        topic_parse = TopicParse(self.tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url': 'http://1'})[1:])
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_failed_parse_1(self):
        topic = {'display_name': '1', 'form': {}}
        self.tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(self.tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse', query_string=falcon.to_query_str({'url1': 'http://1'})[1:])
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_failed_parse_2(self):
        topic = {'display_name': '1', 'form': {}}
        self.tracker_manager.prepare_add_topic = MagicMock(return_value=topic)

        topic_parse = TopicParse(self.tracker_manager)
        self.api.add_route('/api/parse', topic_parse)

        self.simulate_request('/api/parse')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])


@ddt
class TopicTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TopicTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_successful_get_topic(self):
        topic = {'id': 1, 'display_name': '1', 'last_update': None, 'type': 'plugin'}
        self.tracker_manager.get_topic = MagicMock(return_value=topic)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        body = self.simulate_request("/api/topic/{0}".format(1), decode='utf-8')
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, topic)

    def test_not_found_topic(self):
        self.tracker_manager.get_topic = MagicMock(side_effect=KeyError)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_topic(self):
        self.tracker_manager.update_topic = MagicMock(return_value=True)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_topic(self):
        self.tracker_manager.update_topic = MagicMock(side_effect=KeyError)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_topic(self):
        self.tracker_manager.update_topic = MagicMock(return_value=False)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="PUT", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)

    def test_successful_delete_topic(self):
        self.tracker_manager.remove_topic = MagicMock(return_value=True)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_delete_topic(self):
        self.tracker_manager.remove_topic = MagicMock(side_effect=KeyError)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_delete_topic(self):
        self.tracker_manager.remove_topic = MagicMock(return_value=False)

        topic_parse = Topic(self.tracker_manager)
        self.api.add_route('/api/topic/{id}', topic_parse)

        self.simulate_request("/api/topic/{0}".format(1), method="DELETE", body="{}")
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


class TopicResetStatusTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TopicResetStatusTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    def test_successful_reset_topic_status(self):
        self.tracker_manager.reset_topic_status = MagicMock(return_value=True)

        topic_parse = TopicResetStatus(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/reset_status', topic_parse)

        self.simulate_request("/api/topic/{0}/reset_status".format(1), method="POST")
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_reset_topic_status(self):
        self.tracker_manager.reset_topic_status = MagicMock(side_effect=KeyError)

        topic_parse = TopicResetStatus(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/reset_status', topic_parse)

        self.simulate_request("/api/topic/{0}/reset_status".format(1), method="POST")
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_reset_topic_status(self):
        self.tracker_manager.reset_topic_status = MagicMock(return_value=False)

        topic_parse = TopicResetStatus(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/reset_status', topic_parse)

        self.simulate_request("/api/topic/{0}/reset_status".format(1), method="POST")
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class TopicPauseStateTest(RestTestBase, TrackersManagerMixin):
    def setUp(self, disable_auth=True):
        super(TopicPauseStateTest, self).setUp(disable_auth)
        self.trackers_manager_set_up()

    @data(True, False)
    def test_successful_set_pause_state(self, value):
        set_topic_paused_mock = Mock(return_value=True)
        self.tracker_manager.set_topic_paused = set_topic_paused_mock

        topic_parse = TopicPauseState(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/pause', topic_parse)

        self.simulate_request("/api/topic/{0}/pause".format(1), method="POST",
                              body=json.dumps({'paused': value}))
        set_topic_paused_mock.assert_called_once_with('1', value)
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_set_pause_state(self):
        set_topic_paused_mock = Mock(side_effect=KeyError)
        self.tracker_manager.set_topic_paused = set_topic_paused_mock

        topic_parse = TopicPauseState(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/pause', topic_parse)

        self.simulate_request("/api/topic/{0}/pause".format(1), method="POST",
                              body=json.dumps({'paused': True}))
        set_topic_paused_mock.assert_called_once_with('1', True)
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    @data(1, 0, '1', 'True', 'False', 'NotBool')
    def test_bad_request_not_bool_set_pause_state(self, value):
        set_topic_paused_mock = Mock(side_effect=KeyError)
        self.tracker_manager.set_topic_paused = set_topic_paused_mock

        topic_parse = TopicPauseState(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/pause', topic_parse)

        self.simulate_request("/api/topic/{0}/pause".format(1), method="POST",
                              body=json.dumps({'paused': value}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        set_topic_paused_mock.assert_not_called()

    def test_bad_request_missed_required_field_set_pause_state(self):
        set_topic_paused_mock = Mock(side_effect=KeyError)
        self.tracker_manager.set_topic_paused = set_topic_paused_mock

        topic_parse = TopicPauseState(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/pause', topic_parse)

        self.simulate_request("/api/topic/{0}/pause".format(1), method="POST",
                              body=json.dumps({'wrong': 'value'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        set_topic_paused_mock.assert_not_called()

    def test_failed_set_pause_state(self):
        set_topic_paused_mock = Mock(return_value=False)
        self.tracker_manager.set_topic_paused = set_topic_paused_mock

        topic_parse = TopicPauseState(self.tracker_manager)
        self.api.add_route('/api/topic/{id}/pause', topic_parse)

        self.simulate_request("/api/topic/{0}/pause".format(1), method="POST",
                              body=json.dumps({'paused': True}))
        set_topic_paused_mock.assert_called_once_with('1', True)
        self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)
