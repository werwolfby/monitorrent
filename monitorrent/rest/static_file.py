import os
import time
import mimetypes
import falcon
from monitorrent.rest import no_auth, AuthMiddleware
from email.utils import formatdate


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
        if not os.path.isfile(file_path):
            raise falcon.HTTPNotFound(description='Requested page not found')

        mime_type, encoding = mimetypes.guess_type(file_path)
        etag, last_modified = self._get_static_info(file_path)

        resp.content_type = mime_type
        resp.set_header('Date', formatdate(time.time(), usegmt=True))
        resp.set_header('ETag', etag)
        resp.set_header('Last-Modified', last_modified)
        resp.stream_len = os.path.getsize(file_path)
        resp.stream = open(file_path, mode='rb')

    @staticmethod
    def _get_static_info(file_path):
        mtime = os.stat(file_path).st_mtime
        return str(mtime), formatdate(mtime, usegmt=True)
