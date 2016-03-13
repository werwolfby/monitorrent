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
                     for name, client in self.clients_manager.clients.items()]


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
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=unicode(e))
        resp.json = result

    def on_put(self, req, resp, client):
        settings = req.json
        try:
            updated = self.clients_manager.set_settings(client, settings)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=unicode(e))
        if not updated:
            raise falcon.HTTPBadRequest('NotSettable', 'Client plugin \'{0}\' doesn\'t support settings'
                                        .format(client))
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
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=unicode(e))
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
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=unicode(e))
        resp.status = falcon.HTTP_NO_CONTENT
