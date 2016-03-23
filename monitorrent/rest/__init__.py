from builtins import str
from builtins import object
import json
import datetime
import falcon
from enum import Enum
from itsdangerous import JSONWebSignatureSerializer, BadSignature


class MonitorrentJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return str(o)
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


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyUnusedLocal
class AuthMiddleware(object):
    cookie_name = 'jwt'
    serializer = None
    token = None
    auth_enabled = None

    def process_resource(self, req, resp, resource):
        if getattr(resource, '__no_auth__', False):
            return

        if not self.validate_auth(req):
            raise falcon.HTTPUnauthorized('Authentication required', 'AuthCookie is not specified')

    @classmethod
    def validate_auth(cls, req):
        auth_enabled = cls.auth_enabled
        if auth_enabled is not None and not auth_enabled():
            return True

        jwt = req.cookies.get(cls.cookie_name, None)
        if jwt is None:
            return False
        try:
            value = cls.serializer.loads(jwt)
            return value == cls.token
        except BadSignature:
            return False

    @classmethod
    def authenticate(cls, resp):
        value = cls.serializer.dumps(cls.token)
        resp.set_cookie(cls.cookie_name, value, path='/', secure=False)

    @classmethod
    def logout(cls, resp):
        resp.set_cookie(cls.cookie_name, "", path='/', secure=False,
                        expires=datetime.datetime.utcfromtimestamp(0))

    @classmethod
    def init(cls, secret_key, token, auth_enabled):
        cls.serializer = JSONWebSignatureSerializer(secret_key)
        cls.token = token
        if auth_enabled is not None:
            cls.auth_enabled = classmethod(lambda lcls: auth_enabled())
        else:
            cls.auth_enabled = None


def no_auth(obj):
    obj.__no_auth__ = True
    return obj


def create_api(disable_auth=False):
    middleware = list()
    middleware.append(JSONTranslator())
    if not disable_auth:
        middleware.append(AuthMiddleware())
    return falcon.API(request_type=MonitorrentRequest, response_type=MonitorrentResponse,
                      middleware=middleware)
