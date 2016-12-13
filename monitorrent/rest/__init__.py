"""
init code for run falcon API
"""
import json
import datetime
import falcon
from enum import Enum
from itsdangerous import JSONWebSignatureSerializer, BadSignature


class MonitorrentJSONEncoder(json.JSONEncoder):
    """
    can return datetime in ISO format and Enum as regular string
    """

    # pylint: disable=E0202
    # more info https://github.com/PyCQA/pylint/issues/414
    def default(self, o):
        """default method"""
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return str(o)
        return super(MonitorrentJSONEncoder, self).default(o)


class MonitorrentRequest(falcon.Request):
    """
    support for json in request
    """
    json = None


class MonitorrentResponse(falcon.Response):
    """
    support for json in response
    """
    json = None


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyUnusedLocal
class JSONTranslator(object):
    """
    falcon middleware to read json from request and write json into response
    """

    # pylint: disable=W0613
    def process_resource(self, req, resp, resource, params):
        """
        set json property on request

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

    # pylint: disable=W0613
    def process_response(self, req, resp, resource):
        """
        set body from json property on response

        :type req: MonitorrentRequest
        :type resp: MonitorrentResponse
        """
        if resp.json is None:
            return

        resp.body = json.dumps(resp.json, cls=MonitorrentJSONEncoder, ensure_ascii=False)


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyUnusedLocal
class AuthMiddleware(object):
    """
    falcon middleware for authenticate requests over JWT
    """

    cookie_name = 'jwt'
    serializer = None
    token = None
    auth_enabled = None

    # pylint: disable=W0613
    def process_resource(self, req, resp, resource, params):
        """
        validate auth before request, if resource marked with no_auth decorator ignore auth
        if requests hasn't valid JWT token respon 401 will be returned
        """
        if getattr(resource, '__no_auth__', False):
            return

        if not self.validate_auth(req):
            raise falcon.HTTPUnauthorized('Authentication required', 'AuthCookie is not specified', None)

    @classmethod
    def validate_auth(cls, req):
        """check if auth_enabled and JWT token from request is valid"""
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
        """generate JWT token and write it to response"""
        value = cls.serializer.dumps(cls.token).decode()
        resp.set_cookie(cls.cookie_name, value, path='/', secure=False)

    @classmethod
    def logout(cls, resp):
        """expire JWT token cookie"""
        resp.set_cookie(cls.cookie_name, "", path='/', secure=False,
                        expires=datetime.datetime.utcfromtimestamp(0))

    @classmethod
    def init(cls, secret_key, token, auth_enabled):
        """init middleware"""
        cls.serializer = JSONWebSignatureSerializer(secret_key)
        cls.token = token
        if auth_enabled is not None:
            cls.auth_enabled = classmethod(lambda lcls: auth_enabled())
        else:
            cls.auth_enabled = None


def no_auth(obj):
    """decorator for disable resource authentication"""
    obj.__no_auth__ = True
    return obj


def create_api(disable_auth=False):
    """create falcon API with Json and Auth middlewares"""
    middleware = list()
    middleware.append(JSONTranslator())
    if not disable_auth:
        middleware.append(AuthMiddleware())
    return falcon.API(request_type=MonitorrentRequest, response_type=MonitorrentResponse, middleware=middleware)
