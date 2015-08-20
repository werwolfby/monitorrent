import falcon
from monitorrent.plugin_managers import TrackersManager


# noinspection PyUnusedLocal
class Topics(object):
    def __init__(self, tracker_manager):
        """
        :type tracker_manager: TrackersManager
        :return:
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
        :return:
        """
        self.tracker_manager = tracker_manager

    def on_get(self, req, resp):
        url = req.get_param('url', required=True)
        title = self.tracker_manager.prepare_add_topic(url)
        if not title:
            raise falcon.HTTPBadRequest('CantParse', 'Can\' parse url: \'{}\''.format(url))
        resp.json = title
