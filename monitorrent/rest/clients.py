import falcon
from monitorrent.plugin_managers import ClientsManager


# noinspection PyUnusedLocal
class ClientCollection(object):
    def __init__(self, clients_manager):
        """
        :type clients_manager: ClientsManager
        """
        self.clients_manager = clients_manager

    def on_get(self, req, resp):
        resp.json = [{'name': name, 'form': client.form} for name, client in
                     self.clients_manager.clients.items()]


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
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=e.message)
        resp.json = result

    def on_put(self, req, resp, client):
        settings = req.json
        try:
            updated = self.clients_manager.set_settings(client, settings)
        except KeyError as e:
            raise falcon.HTTPNotFound(title='Client plugin \'{0}\' not found'.format(client), description=e.message)
        if not updated:
            raise falcon.HTTPBadRequest('NotSettable', 'Client plugin \'{0}\' doesn\'t support settings'
                                        .format(client))
        resp.status = falcon.HTTP_NO_CONTENT
