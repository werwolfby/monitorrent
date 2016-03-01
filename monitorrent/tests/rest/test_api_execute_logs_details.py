import json
import falcon
from mock import MagicMock
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute_logs_details import ExecuteLogsDetails


class ExecuteLogDetailsTest(RestTestBase):
    def test_get_all(self):
        entries = [{}, {}, {}]

        log_manager = MagicMock()
        log_manager.get_execute_log_details = MagicMock(return_value=entries)
        log_manager.is_running = MagicMock(return_value=False)

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogsDetails(log_manager)

        self.api.add_route('/api/execute/logs/{execute_id}/details', execute_logs)

        body = self.simulate_request('/api/execute/logs/1/details')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body[0])

        self.assertEqual(result, {'is_running': False, 'logs': entries})

    def test_bad_request(self):
        log_manager = MagicMock()

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogsDetails(log_manager)

        self.api.add_route('/api/execute/logs/{execute_id}/details', execute_logs)

        self.simulate_request('/api/execute/logs/abcd/details')

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
