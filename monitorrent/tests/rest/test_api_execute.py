import falcon
import json
from mock import MagicMock, Mock, patch, call
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute import ExecuteCall, ExecuteLogCurrent, ExecuteLogManager


class ExecuteLogCurrentTest(RestTestBase):
    class TimeMock(Mock):
        value = 100
        triggers = []

        def time(self):
            return self.value

        def sleep(self, value):
            self.value += value
            for t, f in self.triggers:
                if self.value >= t:
                    f()

        def call_on(self, trigger, func):
            self.triggers.append((trigger, func))

    def test_empty_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(return_value=None)
        log_manager.is_running = Mock(return_value=False)

        time = self.TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route)

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body[0])

            self.assertEqual(result, {'is_running': False, 'logs': []})

    def test_no_wait_get(self):
        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(return_value=[{}])
        log_manager.is_running = Mock(return_value=True)

        time = self.TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route)

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body[0])

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

    def test_no_wait_after_get(self):
        log_manager = ExecuteLogManager()
        get_current_execute_log_details_mock = Mock(return_value=[{}])
        log_manager.get_current_execute_log_details = get_current_execute_log_details_mock
        log_manager.is_running = Mock(return_value=True)

        time = self.TimeMock()

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route, query_string="after=17")

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body[0])

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})

        get_current_execute_log_details_mock.assert_has_calls([call(17)])

    def test_half_wait_get(self):
        result = {'r': None}

        def set_result():
            result['r'] = [{}]

        log_manager = ExecuteLogManager()
        log_manager.get_current_execute_log_details = Mock(side_effect=lambda *a, **ka: result['r'])
        log_manager.is_running = Mock(return_value=True)

        time = self.TimeMock()
        time.call_on(115, set_result)

        with patch("monitorrent.rest.execute.time", time):
            execute_log_current = ExecuteLogCurrent(log_manager)

            self.api.add_route(self.test_route, execute_log_current)

            body = self.simulate_request(self.test_route)

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)

            result = json.loads(body[0])

            self.assertEqual(result, {'is_running': True, 'logs': [{}]})


class ExecuteCallTest(RestTestBase):
    def test_execute(self):
        engine_runner = Mock()
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with()
