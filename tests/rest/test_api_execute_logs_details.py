import json
import falcon
from mock import MagicMock, Mock, patch, call
from tests import RestTestBase, TimeMock
from monitorrent.rest.execute_logs_details import ExecuteLogsDetails, ExecuteLogManager


class ExecuteLogDetailsTest(RestTestBase):
    def test_get_all(self):
        entries = [{}, {}, {}]

        log_manager = MagicMock()
        log_manager.get_execute_log_details = MagicMock(return_value=entries)
        log_manager.is_running = MagicMock(return_value=False)

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogsDetails(log_manager)

        self.api.add_route('/api/execute/logs/{execute_id}/details', execute_logs)

        body = self.simulate_request('/api/execute/logs/1/details', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'is_running': False, 'logs': entries})

    def test_bad_request(self):
        log_manager = MagicMock()

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogsDetails(log_manager)

        self.api.add_route('/api/execute/logs/{execute_id}/details', execute_logs)

        self.simulate_request('/api/execute/logs/abcd/details')

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_empty_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_execute_log_details = Mock(return_value=[])
        log_manager.is_running = Mock(return_value=False)

        time = TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_details = ExecuteLogsDetails(log_manager)

            self.api.add_route('/api/execute/logs/{execute_id}/details', execute_log_details)

            body = self.simulate_request('/api/execute/logs/1/details', decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': False, 'logs': []})

    def test_no_wait_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_execute_log_details = Mock(return_value=[{}])
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()

        with patch("monitorrent.rest.execute_logs_details.time", time):
            execute_log_details = ExecuteLogsDetails(log_manager)

            self.api.add_route('/api/execute/logs/{execute_id}/details', execute_log_details)

            body = self.simulate_request('/api/execute/logs/1/details', decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

    def test_no_wait_after_get(self):
        log_manager = ExecuteLogManager()
        get_execute_log_details_mock = Mock(return_value=[{}])
        log_manager.get_execute_log_details = get_execute_log_details_mock
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()

        with patch("monitorrent.rest.execute_logs_details.time", time):
            execute_log_details = ExecuteLogsDetails(log_manager)

            self.api.add_route('/api/execute/logs/{execute_id}/details', execute_log_details)

            body = self.simulate_request('/api/execute/logs/1/details', query_string="after=17", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

        get_execute_log_details_mock.assert_has_calls([call(1, 17)])

    def test_half_wait_get(self):
        result = {'r': None}

        def set_result():
            result['r'] = [{}]

        log_manager = ExecuteLogManager()
        log_manager.get_execute_log_details = Mock(side_effect=lambda *a, **ka: result['r'])
        log_manager.is_running = Mock(return_value=True)

        time = TimeMock()
        time.call_on(115, set_result)

        with patch("monitorrent.rest.execute_logs_details.time", time):
            execute_log_details = ExecuteLogsDetails(log_manager)

            self.api.add_route('/api/execute/logs/{execute_id}/details', execute_log_details)

            body = self.simulate_request('/api/execute/logs/1/details', query_string="after=17", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body)

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})
