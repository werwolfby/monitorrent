from builtins import str
from builtins import object
import falcon
from monitorrent.plugin_managers import ClientsManager
from monitorrent.settings_manager import SettingsManager


# noinspection PyUnusedLocal
class ClientCollection(object):
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_get(self, req, resp):
        resp.json = [{'name': name, 'form': client.form, 'is_default': self.clients_manager.get_default() == client}
                     for name, client in list(self.clients_manager.clients.items())]


# noinspection PyUnusedLocal
class Client(object):
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_get(self, req, resp, client):
        try:
            result = self.clients_manager.get_settings(client)
            if not result:
                result = {}
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=str(e))
        resp.json = result

    def on_put(self, req, resp, client):
        settings = req.json
        try:
            self.clients_manager.set_settings(client, settings)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=str(e))
        resp.status = falcon.HTTP_NO_CONTENT


# noinspection PyUnusedLocal
class ClientCheck(object):
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_get(self, req, resp, client):
        try:
            resp.json = {'status': True if self.clients_manager.check_connection(client) else False}
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=str(e))
        resp.status = falcon.HTTP_OK


# TODO: need changes in future
# DefaultClient has url /api/default_client           with GET only
# ClientDefault has url /api/clients/{client}/default with POST only
# noinspection PyUnusedLocal
class DefaultClient:
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_get(self, req, resp):
        try:
            default_client = self.clients_manager.get_default()
            if default_client is None:
                raise falcon.HTTPNotFound(title='Default plugin not set')
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Default plugin not set', description=str(e))

        resp.json = {
            'name': default_client.name,
            'settings': default_client.get_settings(),
            'fields': default_client.SUPPORTED_FIELDS if hasattr(default_client, 'SUPPORTED_FIELDS') else []
        }
        resp.status = falcon.HTTP_OK


# noinspection PyUnusedLocal
class ClientDefault(object):
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_put(self, req, resp, client):
        try:
            self.clients_manager.set_default(client)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=str(e))
        resp.status = falcon.HTTP_NO_CONTENT
