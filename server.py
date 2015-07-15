import os

import cherrypy
from db import init_db_engine, create_db
from plugin_loader import load_plugins, get_plugins

engine = init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
create_db(engine)

plugins = get_plugins('tracker')

class App(object):
    def __init__(self):
        super(App, self).__init__()
        self.api = Api()

    @cherrypy.expose
    def index(self):
        # return file('./static/index.html')
        raise cherrypy.HTTPRedirect("/static/index.html")

class Api(object):
    def __init__(self):
        super(Api, self).__init__()
        self.torrents = TorrentsApi()

    @cherrypy.expose
    def parse(self, url):
        for plugin in plugins:
            result = plugin.parse_url(url)
            if result is not None:
                return result
        raise cherrypy.HTTPError(404, "Can't parse url %s" % url)


class TorrentsApi(object):
    _torrents = [{'id': 1, 'name': u"Arrow"},
                 {'id': 2, 'name': u"Castle"},
                 {'id': 3, 'name': u"Cougar Town"},
                 {'id': 4, 'name': u"Extant"},
                 {'id': 5, 'name': u"Falling Skies"},
                 {'id': 6, 'name': u"Game of Thrones"},
                 {'id': 7, 'name': u"Gotham"},
                 {'id': 8, 'name': u"Grimm"},
                 {'id': 9, 'name': u"Hell on wheels"},
                 {'id': 10, 'name': u"Modern Family"},
                 {'id': 11, 'name': u"Supernatural"},
                 {'id': 12, 'name': u"The Flash"},
                 {'id': 13, 'name': u"The Hundred"},
                 {'id': 14, 'name': u"The Last Ship"},
                 {'id': 15, 'name': u"The Strain"},
                 {'id': 16, 'name': u"The Vampire Diaries"},
                 {'id': 17, 'name': u"Under the Dome"},
                 {'id': 18, 'name': u"Walking Dead"}]

    exposed = True

    @cherrypy.tools.json_out()
    def GET(self):
        return self._torrents

    def DELETE(self, id):
        for torrent in self._torrents:
            if torrent.get('id') == int(id):
                self._torrents.remove(torrent)
                break


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        },
        '/api/torrents': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }

    cherrypy.quickstart(App(), config=conf)
