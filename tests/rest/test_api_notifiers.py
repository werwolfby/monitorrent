import json

import falcon
from ddt import ddt, data
from mock import Mock, PropertyMock

from monitorrent.plugin_managers import NotifierManager
from monitorrent.rest.notifiers import NotifierCollection, Notifier, NotifierCheck, NotifierEnabled
from tests import RestTestBase
from monitorrent.plugins.notifiers import Notifier as BaseNotifier


@ddt
class NotifierCollectionTest(RestTestBase):
    class TestNotifier(object):
        form = {}
        settings = Mock()
        settings.is_enabled = True
        get_settings = Mock(return_value=settings)
        is_enabled = PropertyMock(return_value=True)

    def test_get_all(self):
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})

        notifier_collection = NotifierCollection(notifiers_manager)
        self.api.add_route('/api/notifiers', notifier_collection)

        body = self.simulate_request('/api/notifiers', decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, list)
        self.assertEqual(1, len(result))

        self.assertEqual(result[0],
                         {
                             'name': 'test',
                             'form': NotifierCollectionTest.TestNotifier.form,
                             'has_settings': True,
                             'enabled': True
                         })


class NotifierEnabledTest(RestTestBase):
    def test_set_enabled(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': test_notifier})

        settings = Mock()
        test_notifier.get_settings = Mock(return_value=settings)
        test_notifier.update_settings = Mock()

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        self.simulate_request('/api/notifiers/{0}/enabled'.format('test'), method="PUT",
                              body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)
        self.assertTrue(test_notifier.is_enabled)

    def test_set_enabled_invalid_key(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': test_notifier})

        settings = Mock()
        test_notifier.get_settings = Mock(return_value=settings)
        test_notifier.update_settings = Mock()

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        self.simulate_request('/api/notifiers/{0}/enabled'.format('blabla'), method="PUT",
                              body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_404)

    def test_set_enabled_error_updating(self):
        test_notifier = NotifierCollectionTest.TestNotifier()
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': test_notifier})

        settings = Mock()
        test_notifier.get_settings = Mock(return_value=settings)
        type(test_notifier).is_enabled = PropertyMock(side_effect=Exception)

        notifier_enabled = NotifierEnabled(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}/enabled', notifier_enabled)

        self.simulate_request('/api/notifiers/{0}/enabled'.format('test'), method="PUT",
                              body=json.dumps({'enabled': True}))
        self.assertEqual(self.srmock.status, falcon.HTTP_400)


class NotifierTest(RestTestBase):
    # noinspection PyCallByClass
    def test_get_settings(self):
        # noinspection PyTypeChecker
        notifier_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        settings = BaseNotifier()
        settings.login = 'login'
        notifier_manager.get_settings = Mock(return_value=settings)

        notifier = Notifier(notifier_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        body = self.simulate_request('/api/notifiers/{0}'.format(1), decode="utf-8")
        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['login'], settings.login)

    def test_empty_get_settings(self):
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.get_settings = Mock(return_value=None)

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
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.get_settings = Mock(side_effect=KeyError)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1))

        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

    def test_successful_update_settings(self):
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = Mock(return_value=True)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format('test'), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    def test_not_found_update_settings(self):
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = Mock(side_effect=KeyError)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)

    def test_failed_update_settings(self):
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.update_settings = Mock(return_value=False)

        notifier = Notifier(notifiers_manager)
        self.api.add_route('/api/notifiers/{notifier}', notifier)

        self.simulate_request('/api/notifiers/{0}'.format(1), method="PUT",
                              body=json.dumps({'login': 'login', 'password': 'password'}))
        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)


@ddt
class CheckNotifierTest(RestTestBase):
    @data(True, False)
    def test_check_notifier(self, value):
        # noinspection PyTypeChecker
        notifier_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifier_manager.send_test_message = Mock(return_value=value)

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
        # noinspection PyTypeChecker
        notifiers_manager = NotifierManager(Mock(), {'test': NotifierCollectionTest.TestNotifier()})
        notifiers_manager.send_test_message = Mock(side_effect=KeyError)

        notifier = NotifierCheck(notifiers_manager)
        notifier.__no_auth__ = True
        self.api.add_route('/api/clients/{notifier}/check', notifier)

        self.simulate_request('/api/clients/{0}/check'.format('tracker.org'))
        self.assertEqual(self.srmock.status, falcon.HTTP_NOT_FOUND)
