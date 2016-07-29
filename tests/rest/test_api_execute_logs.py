from builtins import range
import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from tests import RestTestBase
from monitorrent.rest.execute_logs import ExecuteLogs


class ExecuteLogsTest(RestTestBase):
    def test_get_all(self):
        entries = [{}, {}, {}]
        count = 3

        log_manager = MagicMock()
        log_manager.get_log_entries = MagicMock(return_value=(entries, count))

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogs(log_manager)

        self.api.add_route('/api/execute/logs', execute_logs)

        body = self.simulate_request('/api/execute/logs', query_string='take=10', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(entries, result['data'])
        self.assertEqual(count, result['count'])

    def test_get_paged(self):
        # count should be less than 30
        count = 23
        entries = [{'i': i} for i in range(count)]

        def get_log_entries(skip, take):
            return entries[skip:skip + take], count

        log_manager = MagicMock()
        log_manager.get_log_entries = MagicMock(side_effect=get_log_entries)

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogs(log_manager)

        self.api.add_route('/api/execute/logs', execute_logs)

        body = self.simulate_request('/api/execute/logs', query_string='take=10', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(entries[0:10], result['data'])
        self.assertEqual(count, result['count'])

        body = self.simulate_request('/api/execute/logs', query_string='take=10&skip=0', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(entries[0:10], result['data'])
        self.assertEqual(count, result['count'])

        body = self.simulate_request('/api/execute/logs', query_string='take=10&skip=10', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(entries[10:20], result['data'])
        self.assertEqual(count, result['count'])

        body = self.simulate_request('/api/execute/logs', query_string='take=10&skip=20', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        # assume that count is less then 30
        self.assertEqual(entries[20:count], result['data'])
        self.assertEqual(count, result['count'])

    def test_bad_requests(self):
        entries = [{}, {}, {}]
        count = 3

        log_manager = MagicMock()
        log_manager.get_log_entries = MagicMock(return_value=(entries, count))

        # noinspection PyTypeChecker
        execute_logs = ExecuteLogs(log_manager)

        self.api.add_route('/api/execute/logs', execute_logs)

        self.simulate_request('/api/execute/logs')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'take is required')

        self.simulate_request('/api/execute/logs', query_string='take=abcd')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'take should be int')

        self.simulate_request('/api/execute/logs', query_string='take=10&skip=abcd')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'skip should be int')

        self.simulate_request('/api/execute/logs', query_string='take=101')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'take should be less or equal to 100')

        self.simulate_request('/api/execute/logs', query_string='take=-10')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'take should be greater than 0')

        self.simulate_request('/api/execute/logs', query_string='take=0')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'take should be greater than 0')

        self.simulate_request('/api/execute/logs', query_string='take=10&skip=-1')
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST, 'skip should be greater or equal to 0')
