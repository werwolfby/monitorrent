from builtins import object
import json
import falcon
from datetime import datetime
from ddt import ddt, data
import pytz
from tests import RestTestBase
from monitorrent.rest.settings_execute import SettingsExecute


@ddt
class SettingsExecuteTest(RestTestBase):
    class Bunch(object):
        pass

    def test_is_authentication_enabled(self):
        engine_runner = SettingsExecuteTest.Bunch()
        engine_runner.interval = 399
        engine_runner.last_execute = datetime.now(pytz.utc)
        settings_execute_resource = SettingsExecute(engine_runner)
        self.api.add_route('/api/settings/execute', settings_execute_resource)

        body = self.simulate_request("/api/settings/execute", decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'interval': engine_runner.interval,
                                  'last_execute': engine_runner.last_execute.isoformat()})

    @data(1, 100, 2000, 3600, 7200)
    def test_set_interval(self, value):
        engine_runner = SettingsExecuteTest.Bunch()
        engine_runner.interval = 399
        engine_runner.last_execute = datetime.now(pytz.utc)
        settings_execute_resource = SettingsExecute(engine_runner)
        self.api.add_route('/api/settings/execute', settings_execute_resource)

        request = {'interval': value}
        self.simulate_request("/api/settings/execute", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_set_interval_wrong_interval_type(self):
        engine_runner = SettingsExecuteTest.Bunch()
        engine_runner.interval = 399
        engine_runner.last_execute = datetime.now(pytz.utc)
        settings_execute_resource = SettingsExecute(engine_runner)
        self.api.add_route('/api/settings/execute', settings_execute_resource)

        request = {'interval': 'string'}
        self.simulate_request("/api/settings/execute", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    def test_set_is_authentication_enabled_empty_request(self):
        engine_runner = SettingsExecuteTest.Bunch()
        engine_runner.interval = 399
        engine_runner.last_execute = datetime.now(pytz.utc)
        settings_execute_resource = SettingsExecute(engine_runner)
        self.api.add_route(self.test_route, settings_execute_resource)

        self.simulate_request(self.test_route, method="PUT")

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
