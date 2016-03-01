import falcon
from mock import MagicMock, Mock
from monitorrent.tests import RestTestBase
from monitorrent.rest.execute import ExecuteCall


class ExecuteCallTest(RestTestBase):
    def test_execute(self):
        engine_runner = Mock
        engine_runner.execute = MagicMock()
        # noinspection PyTypeChecker
        execute_call = ExecuteCall(engine_runner)

        self.api.add_route(self.test_route, execute_call)

        self.simulate_request(self.test_route, method="POST")

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)

        engine_runner.execute.assert_called_once_with()
