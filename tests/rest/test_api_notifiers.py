import json

import falcon
from ddt import ddt, data
from mock import MagicMock

from monitorrent.plugin_managers import NotifierManager
from monitorrent.rest.notifiers import NotifierCollection, Notifier, NotifierCheck, NotifierEnabled
from tests import RestTestBase
from monitorrent.plugins.notifiers import Notifier as BaseNotifier


@ddt
class NotifierCollectionTest(RestTestBase):
    class TestNotifier(object):
        form = {}
        settings = MagicMock()
        settings.is_enabled = True
        get_settings = MagicMock(return_value=settings)

    def test_get_all(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})

        notifier_collection = NotifierCollection(notifiers_manager)
        self.api.add_route('/api/notifiers', notifier_collection)

        body = self.simulate_request('/api/notifiers', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0],
                         {'name': 'test', 'form': NotifierCollectionTest.TestNotifier.form, 'enabled': True})


class NotifierEnabledTest(RestTestBase):
    def test_set_enabled(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        notifiers_manager = NotifierManager({'test': test_notifier})

        settings = MagicMock()
        test_notifier.get_settings = MagicMock(return_value=settings)
        test_notifier.update_settings = MagicMock()

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        body = self.simulate_request('/api/notifiers/{0}/enabled'.format('test'), method="PUT",
                                     body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)
        test_notifier.update_settings.assert_called_once_with(settings)
        self.assertTrue(settings.enabled)

    def test_set_enabled_invalid_key(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        notifiers_manager = NotifierManager({'test': test_notifier})

        settings = MagicMock()
        test_notifier.get_settings = MagicMock(return_value=settings)
        test_notifier.update_settings = MagicMock()

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        body = self.simulate_request('/api/notifiers/{0}/enabled'.format('blabla'), method="PUT",
                                     body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_404)

    def test_set_enabled_error_updating(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        notifiers_manager = NotifierManager({'test': test_notifier})

        settings = MagicMock()
        test_notifier.get_settings = MagicMock(return_value=settings)
        test_notifier.update_settings = MagicMock(return_value=False)

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        body = self.simulate_request('/api/notifiers/{0}/enabled'.format('test'), method="PUT",
                                     body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_400)


class NotifierTest(RestTestBase):
    # noinspection PyCallByClass
    def test_get_settings(self):
        notifier_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        settings = BaseNotifier()
        settings.login = 'login'
        notifier_manager.get_settings = MagicMock(return_value=settings)

        notifier = Notifier(notifier_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        body = self.simulate_request('/api/notifiers/{0}'.format(1), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['login'], settings.login)

    def test_empty_get_settings(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.get_settings = MagicMock(return_value=None)

        notifier = Notifier(notifiers_manager)
        notifier.__no_auth__ = True
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        body = self.simulate_request('/api/notifiers/{0}'.format(1), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_not_found_settings(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.get_settings = MagicMock(side_effect=KeyError)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_settings(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = MagicMock(return_value=True)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format('test'), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_settings(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = MagicMock(side_effect=KeyError)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_settings(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = MagicMock(return_value=False)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)


@ddt
class CheckNotifierTest(RestTestBase):
    @data(True, False)
    def test_check_notifier(self, value):
        notifier_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifier_manager.send_test_message = MagicMock(return_value=value)

        notifier = NotifierCheck(notifier_manager)
        notifier.__no_auth__ = True
        self.api.add_route('/api/notifiers/{notifier}/check', notifier)

        body = self.simulate_request('/api/notifiers/{0}/check'.format('tracker.org'), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'status': value})

    def test_check_notifier_not_found(self):
        notifiers_manager = NotifierManager({'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.send_test_message = MagicMock(side_effect=KeyError)

        notifier = NotifierCheck(notifiers_manager)
        notifier.__no_auth__ = True
        self.api.add_route('/api/clients/{notifier}/check', notifier)

        self.simulate_request('/api/clients/{0}/check'.format('tracker.org'))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
