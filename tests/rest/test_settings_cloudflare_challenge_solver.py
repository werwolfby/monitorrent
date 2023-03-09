import itertools
import json
import unittest

import falcon
import pytest
from mock import Mock, PropertyMock, patch, call
from ddt import ddt, data, idata, unpack
from tests import RestTestBase
from monitorrent.rest.settings_cloudflare_challenge_solver import SettingsCloudflareChallengeSolver
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsCloudflareChallengeSolverTest(RestTestBase):
    @idata(itertools.product([True, False], [True, False], [True, False], [3, 5]))
    @unpack
    def test_cloudflare_challenge_solver_debug(self, debug, record_video, record_har, keep_records):
        with patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_debug',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_debug_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_record_video',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_record_video_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_record_har',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_record_har_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_keep_records',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_keep_records_mock:
            cloudflare_challenge_solver_debug_mock.return_value = debug
            cloudflare_challenge_solver_record_video_mock.return_value = record_video
            cloudflare_challenge_solver_record_har_mock.return_value = record_har
            cloudflare_challenge_solver_keep_records_mock.return_value = keep_records

            settings_manager = SettingsManager()

            settings_cloudflare_challenge_solver = SettingsCloudflareChallengeSolver(settings_manager)
            self.api.add_route('/api/settings/cloudflare-challenge-solver', settings_cloudflare_challenge_solver)

            body = self.simulate_request("/api/settings/cloudflare-challenge-solver", decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_OK)
            self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

            result = json.loads(body)

            expected = {'debug': debug, 'record_video': record_video, 'record_har': record_har, 'keep_records': keep_records}
            self.assertEqual(result, expected)

            cloudflare_challenge_solver_debug_mock.assert_called_once_with()
            cloudflare_challenge_solver_record_video_mock.assert_called_once_with()
            cloudflare_challenge_solver_record_har_mock.assert_called_once_with()
            cloudflare_challenge_solver_keep_records_mock.assert_called_once_with()

    @idata(filter(lambda x: x[:-1] != (None, None, None, None),
                  itertools.product(
                      [True, False, None],
                      [True, False, None],
                      [True, False, None],
                      [3, 5, None],
                      [True, False],
                  )))
    @unpack
    def test_cloudflare_challenge_solver_debug_patch(self, debug, record_video, record_har, keep_records, revert):
        def get_value(value):
            if value is None:
                return True
            return value if not revert else not value

        def get_keep_records(value):
            if value is None:
                return 3
            return value if not revert else value + 1

        with patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_debug',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_debug_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_record_video',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_record_video_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_record_har',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_record_har_mock,\
             patch('monitorrent.settings_manager.SettingsManager.cloudflare_challenge_solver_keep_records',
                   new_callable=PropertyMock) as cloudflare_challenge_solver_keep_records_mock:
            cloudflare_challenge_solver_debug_mock.return_value = get_value(debug)
            cloudflare_challenge_solver_record_video_mock.return_value = get_value(record_video)
            cloudflare_challenge_solver_record_har_mock.return_value = get_value(record_har)
            cloudflare_challenge_solver_keep_records_mock.return_value = get_keep_records(keep_records)

            settings_manager = SettingsManager()

            settings_cloudflare_challenge_solver = SettingsCloudflareChallengeSolver(settings_manager)
            self.api.add_route('/api/settings/cloudflare-challenge-solver', settings_cloudflare_challenge_solver)

            p = dict()
            if debug is not None:
                p['debug'] = debug
            if record_video is not None:
                p['record_video'] = record_video
            if record_har is not None:
                p['record_har'] = record_har
            if keep_records is not None:
                p['keep_records'] = keep_records

            self.simulate_request("/api/settings/cloudflare-challenge-solver", method='PATCH',
                                  body=json.dumps(p), decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

            def assert_calls(value, mock):
                if value is not None:
                    mock.assert_has_calls([call()])
                    if revert:
                        mock.assert_has_calls([call(value)])
                else:
                    mock.assert_not_called()

            assert_calls(debug, cloudflare_challenge_solver_debug_mock)
            assert_calls(record_video, cloudflare_challenge_solver_record_video_mock)
            assert_calls(record_har, cloudflare_challenge_solver_record_har_mock)
            assert_calls(keep_records, cloudflare_challenge_solver_keep_records_mock)

    @data(({'debug': 'invalid'}, 'debug', 'bool'),
          ({'debug': 1}, 'debug', 'bool'),
          ({'debug': 0}, 'debug', 'bool'),
          ({'debug': -1}, 'debug', 'bool'),
          ({'debug': 1.1}, 'debug', 'bool'),
          ({'record_video': 1}, 'record_video', 'bool'),
          ({'record_video': 'invalid'}, 'record_video', 'bool'),
          ({'record_har': 0}, 'record_har', 'bool'),
          ({'record_har': 'invalid'}, 'record_har', 'bool'),
          ({'keep_records': 'invalid'}, 'keep_records', 'int'),
          ({}, 'JSON', 'not empty')
          )
    @unpack
    def test_cloudflare_challenge_solver_debug_patch_invalid(self, body, expected_field, expected_type):
        with patch('monitorrent.settings_manager.SettingsManager'):
            settings_cloudflare_challenge_solver = SettingsCloudflareChallengeSolver(None)
            self.api.add_route('/api/settings/cloudflare-challenge-solver', settings_cloudflare_challenge_solver)

            result = self.simulate_request("/api/settings/cloudflare-challenge-solver", method='PATCH',
                                  body=json.dumps(body), decode='utf-8')

            self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
            self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

            assert expected_field in result
            assert expected_type in result
