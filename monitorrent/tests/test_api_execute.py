import json
from mock import MagicMock
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute import ExecuteLog, EngineRunnerLogger


class ExecuteLogTest(RestTestBase):
    def test_simple_log(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLog(logger)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        resp = next(body)
        queue = attach_mock.call_args_list[0][0][0]

        e1 = {'test': '1'}
        e2 = {'test': '2'}
        queue.put(e1)
        queue.put(e2)
        queue.put(None)

        for r in body:
            resp += r

        resp_parsed = json.loads(resp)

        self.assertEqual(2, len(resp_parsed))
        self.assertEqual(resp_parsed, [e1, e2])

    def test_break(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLog(logger, timeout=1)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        resp = next(body)

        for r in body:
            resp += r

        resp_parsed = json.loads(resp)

        self.assertEqual(0, len(resp_parsed))
        self.assertEqual(resp_parsed, [])

    def test_exit(self):
        attach_mock, detach_mock, logger = self._create_logger()
        execute_log = ExecuteLog(logger, timeout=1)

        self.api.add_route(self.test_route, execute_log)

        body = self.simulate_request(self.test_route)
        next(body)
        body.close()

        self.assertTrue(attach_mock.called)
        self.assertEqual(attach_mock.call_count, 1)

        self.assertTrue(detach_mock.called)
        self.assertEqual(detach_mock.call_count, 1)

    def _create_logger(self):
        logger = EngineRunnerLogger()
        attach_mock = MagicMock()
        detach_mock = MagicMock()
        logger.attach = attach_mock
        logger.detach = detach_mock
        return attach_mock, detach_mock, logger
