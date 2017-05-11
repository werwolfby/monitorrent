from collections import namedtuple

import falcon
from builtins import str
from builtins import object

import structlog
from monitorrent.plugin_managers import NotifierManager

log = structlog.get_logger()


# noinspection PyUnusedLocal
class NotifierCollection(object):
    def __init__(self, notifier_manager):
        """
        :type notifier_manager: NotifierManager
        """
        self.notifier_manager = notifier_manager

    def on_get(self, req, resp):
        resp.json = [{'name': name,
                      'form': notifier.form,
                      'enabled': self.notifier_manager.get_enabled(name),
                      'has_settings': self.notifier_manager.get_settings(name) is not None}
                     for name, notifier in list(self.notifier_manager.notifiers.items())]


# noinspection PyUnusedLocal
class Notifier(object):
    def __init__(self, notifier_manager):
        """
        :type notifier_manager: NotifierManager
        """
        self.notifier_manager = notifier_manager

    def on_get(self, req, resp, notifier):
        try:
            result = self.notifier_manager.get_settings(notifier)
            if not result:
                resp.json = {}
                return
        except KeyError as e:
            log.error("Notifier could not be found", notifier=notifier, exception=str(e))
            raise falcon.HTTPNotFound(title='Notifier plugin \'{0}\' not found'.format(notifier), description=str(e))
        resp.json = result.__props__()

    def on_put(self, req, resp, notifier):
        settings = req.json
        try:
            updated = self.notifier_manager.update_settings(notifier, settings)
        except KeyError as e:
            log.error("Notifier could not be found", notifier=notifier, exception=str(e))
            raise falcon.HTTPNotFound(title='Notifier plugin \'{0}\' not found'.format(notifier), description=str(e))
        if not updated:
            log.error("Notifier plugin doesn't support settings", notifier=notifier)
            raise falcon.HTTPBadRequest('NotSettable', 'Notifier plugin \'{0}\' doesn\'t support settings'
                                        .format(notifier))

        resp.status = falcon.HTTP_NO_CONTENT


class NotifierCheck(object):
    def __init__(self, notifier_manager):
        """
        :type notifier_manager: NotifierManager
        """
        self.notifier_manager = notifier_manager

    def on_get(self, req, resp, notifier):
        try:
            resp.json = {'status': True if self.notifier_manager.send_test_message(notifier) else False}
        except KeyError as e:
            log.error("Notifier could not be found", notifier=notifier, exception=str(e))
            raise falcon.HTTPNotFound(title='Notifier plugin \'{0}\' not found'.format(notifier), description=str(e))
        except Exception as e:
            log.error("An error has occurred", exception=str(e))
            raise falcon.HTTPInternalServerError(title='A server has encountered an error', description=str(e))
        resp.status = falcon.HTTP_OK


class NotifierEnabled(object):
    def __init__(self, notifier_manager):
        """
        :type notifier_manager: NotifierManager
        """
        self.notifier_manager = notifier_manager

    def on_put(self, req, resp, notifier):
        try:
            params = req.json
            enabled = params['enabled']
            updated = self.notifier_manager.set_enabled(notifier, enabled)
        except KeyError as e:
            log.error("Notifier could not be found", notifier=notifier, exception=str(e))
            raise falcon.HTTPNotFound(title='Notifier plugin \'{0}\' not found'.format(notifier), description=str(e))
        if not updated:
            log.error("Notifier plugin doesn't support settings", notifier=notifier)
            raise falcon.HTTPBadRequest('NotSettable', 'Notifier plugin \'{0}\' doesn\'t support settings'
                                        .format(notifier))
        resp.status = falcon.HTTP_NO_CONTENT
