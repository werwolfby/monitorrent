import falcon
from monitorrent.plugin_managers import TrackersManager


# noinspection PyUnusedLocal
class TopicCollection(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        resp.json = self.tracker_manager.get_watching_torrents()

    def on_post(self, req, resp):
        body = req.json
        url = body.get('url', None)
        settings = body.get('settings', None)
        added = self.tracker_manager.add_topic(url, settings)
        if not added:
            raise falcon.HTTPBadRequest('CantAdd', 'Can\'t add torrent: \'{}\''.format(url))
        resp.status = 201


class TopicParse(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        url = req.get_param('url', required=True)
        title = self.tracker_manager.prepare_add_topic(url)
        if not title:
            raise falcon.HTTPBadRequest('CantParse', 'Can\' parse url: \'{}\''.format(url))
        resp.json = title


# noinspection PyUnusedLocal,PyShadowingBuiltins
class Topic(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp, id):
        resp.json = self.tracker_manager.get_topic(id)

    def on_put(self, req, resp, id):
        settings = req.json
        updated = self.tracker_manager.update_watch(id, settings)
        if not updated:
            raise falcon.HTTPNotFound(description='Can\'t update topic {}'.format(id))
        resp.status = 204

    def on_delete(self, req, resp, id):
        deleted = self.tracker_manager.remove_topic(id)
        if not deleted:
            raise falcon.HTTPNotFound(description='Topic {} doesn\'t exist'.format(id))
        resp.status = 204
