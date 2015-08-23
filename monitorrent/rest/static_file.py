import mimetypes
import os
import falcon
from monitorrent.rest import no_auth, AuthMiddleware


@no_auth
class StaticFiles(object):
    def __init__(self, folder=None, filename=None, redirect_to_login=True):
        self.folder = folder
        self.filename = filename
        self.redirect_to_login = redirect_to_login

    def on_get(self, req, resp, filename=None):
        if self.redirect_to_login and not AuthMiddleware.validate_auth(req):
            resp.status = falcon.HTTP_FOUND
            resp.location = '/login'
            return

        file_path = filename or self.filename
        if self.folder:
            file_path = os.path.join(self.folder, file_path)
        mime_type, encoding = mimetypes.guess_type(file_path)
        resp.content_type = mime_type
        resp.stream_len = os.path.getsize(file_path)
        resp.stream = open(file_path, mode='rb')
