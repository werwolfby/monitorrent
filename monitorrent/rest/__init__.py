import json
import datetime
import falcon


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
    def process_resource(self, req, resp, resource):
        """
        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        if req.content_length in (None, 0):
            return

        body = req.stream.read()
        try:
            req.json = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPBadRequest('Malformed JSON',
                                        'Could not decode the request body. The '
                                        'JSON was incorrect or not encoded as '
                                        'UTF-8.')

    def process_response(self, req, resp, resource):
        """
        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        if resp.json is None:
            return

        resp.body = json.dumps(resp.json, cls=MonitorrentJSONEncoder, encoding='utf-8', ensure_ascii=False)


def create_api():
    return falcon.API(request_type=MonitorrentRequest, response_type=MonitorrentResponse,
                      middleware=[JSONTranslator()])
