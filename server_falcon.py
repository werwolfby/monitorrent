import os
from path import path
import falcon
import mimetypes
from cherrypy import wsgiserver


class StaticFiles(object):
    def __init__(self, folder=None):
        self.folder = folder

    def on_get(self, req, resp, filename=None):
        file_path = 'index.html' if not filename else filename
        if self.folder:
            file_path = os.path.join(self.folder, file_path)
        mime_type, encoding = mimetypes.guess_type(file_path)
        resp.content_type = mime_type
        resp.stream = open(file_path)


app = falcon.API()

p = path('webapp')
app.add_route('/', StaticFiles('webapp'))
for f in p.walkdirs():
    parts = filter(None, f.splitall())
    url = '/' + '/'.join(parts[1:]) + '/{filename}'
    app.add_route(url, StaticFiles(f))


if __name__ == '__main__':
    d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
    server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8080), d)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
