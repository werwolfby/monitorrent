import falcon
import json
from ddt import ddt, data
from mock import MagicMock, Mock, patch, call
from monitorrent.plugins.status import Status
from tests import RestTestBase, TimeMock
from monitorrent.rest.execute import ExecuteCall, ExecuteLogCurrent, ExecuteLogManager


class ExecuteLogCurrentTest(RestTestBase):
    notifier_manager = MagicMock()

    def test_empty_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(return_value=None)
        log_manager.is_running = Mock(return_value=False)

        time = TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route, decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': False, 'logs': []})

    def test_no_wait_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(return_value=[{}])
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route, decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

    def test_no_wait_after_get(self):
        log_manager = ExecuteLogManager()
        get_current_execute_log_details_mock = Mock(return_value=[{}])
        log_manager.get_current_execute_log_details = get_current_execute_log_details_mock
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route, query_string="after=17", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

        get_current_execute_log_details_mock.assert_has_calls([call(17)])

    def test_half_wait_get(self):
        result = {'r': None}

        def set_result():
            result['r'] = [{}]

        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(side_effect=lambda *a, **ka: result['r'])
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()
        time.call_on(115, set_result)

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route, decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

    def test_execute_logs_failure(self):
        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(side_effect=Exception)
        log_manager.is_running = Mock(return_value=True)

        execute_log_current = ExecuteLogCurrent(log_manager)
        time = TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            self.api.add_route(self.test_route, execute_log_current)
            self.simulate_request(self.test_route, decode='utf-8')
            self.assertEqual(self.srmock.status, falcon.HTTP_INTERNAL_SERVER_ERROR)


@ddt
class ExecuteCallTest(RestTestBase):
    def test_execute(self):
        engine_runner = Mock()
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with(None)

    def test_execute_with_ids(self):
        engine_runner = Mock()
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string="ids=1,2,3", method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with([1, 2, 3])

    def test_execute_with_statuses(self):
        trackers_manager = Mock()
        trackers_manager.get_status_topics_ids = Mock(return_value=[1, 2, 3])

        engine_runner = Mock()
        engine_runner.trackers_manager = trackers_manager
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string="statuses=ok,error", method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with([1, 2, 3])
        trackers_manager.get_status_topics_ids.assert_called_once_with([Status.Ok, Status.Error])

    def test_execute_with_tracker(self):
        topic1 = Mock()
        topic1.id = 1

        topic2 = Mock()
        topic2.id = 2

        trackers_manager = Mock()
        trackers_manager.get_tracker_topics = Mock(return_value=[topic1, topic2])

        engine_runner = Mock()
        engine_runner.trackers_manager = trackers_manager
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string="tracker=tracker.tv", method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with([1, 2])
        trackers_manager.get_tracker_topics.assert_called_once_with('tracker.tv')

    def test_execute_with_empty_topics_expect_conflict(self):
        trackers_manager = Mock()
        trackers_manager.get_tracker_topics = Mock(return_value=[])

        engine_runner = Mock()
        engine_runner.trackers_manager = trackers_manager
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string="tracker=tracker.tv", method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_CONFLICT)

        engine_runner.execute.assert_not_called()
        trackers_manager.get_tracker_topics.assert_called_once_with('tracker.tv')

    def test_execute_with_wrong_param_ids(self):
        engine_runner = Mock()
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string="ids=1,abc,3", method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

        engine_runner.execute.assert_not_called()

    @data("ids=1,3&statuses=ok,error",
          "statuses=ok,error&tracker=tracker.tv",
          "ids=1,3&tracker=tracker.tv",
          "ids=1,3&statuses=ok,error&tracker=tracker.tv")
    def test_execute_fail_with_multiple_params(self, query_string):
        engine_runner = Mock()
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, query_string=query_string, method="POST")
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
        engine_runner.execute.assert_not_called()
