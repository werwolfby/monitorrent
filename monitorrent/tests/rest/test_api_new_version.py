import json
import falcon
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.new_version import NewVersion
from monitorrent.new_version_checker import NewVersionChecker


@ddt
class SettingsDeveloperTest(RestTestBase):
    @data('https://github.com/werwolfby/monitorrent/releases/tag/1.0.2',
          'https://github.com/werwolfby/monitorrent/releases/tag/1.0.1',
          'https://github.com/werwolfby/monitorrent/releases/tag/1.0.0')
    def test_get_url(self, url):
        new_version_checker = NewVersionChecker(False)
        new_version_resource = NewVersion(new_version_checker)
        new_version_checker.new_version_url = url
        self.api.add_route('/api/new_version', new_version_resource)

        body = self.simulate_request("/api/new_version", decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'url': url})
