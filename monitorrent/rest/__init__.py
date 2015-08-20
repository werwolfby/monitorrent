import json
import datetime
import falcon
import os
import mimetypes
from path import path


class MonitorrentJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super(MonitorrentJSONEncoder, self).default(o)


class MonitorrentRequest(falcon.Request):
    json = None


class MonitorrentResponse(falcon.Response):
    json = None


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyUnusedLocal
class JSONTranslator(object):
    def prepare_resource(self, req, resp):
        """
        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.json = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        """
        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        if not resp.json:
            return

        resp.body = json.dumps(resp.json, cls=MonitorrentJSONEncoder, encoding='utf-8', ensure_ascii=False)


# noinspection PyUnusedLocal
class StaticFiles(object):
    def __init__(self, folder=None):
        self.folder = folder

    def on_get(self, req, resp, filename=None):
        file_path = filename or 'index.html'
        if self.folder:
            file_path = os.path.join(self.folder, file_path)
        mime_type, encoding = mimetypes.guess_type(file_path)
        resp.content_type = mime_type
        resp.stream = open(file_path, mode='rb')


def _add_static_route(api, folder):
    p = path(folder)
    api.add_route('/', StaticFiles(folder))
    for f in p.walkdirs():
        parts = filter(None, f.splitall())
        url = '/' + '/'.join(parts[1:]) + '/{filename}'
        api.add_route(url, StaticFiles(f))


def create_api(static_folder):
    app = falcon.API(request_type=MonitorrentRequest, response_type=MonitorrentResponse,
                     middleware=[JSONTranslator()])
    _add_static_route(app, static_folder)
