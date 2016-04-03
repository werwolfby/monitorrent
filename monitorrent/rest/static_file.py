from builtins import object
import os
import time
import mimetypes
import falcon
from monitorrent.rest import no_auth, AuthMiddleware
from email.utils import formatdate, parsedate


@no_auth
class StaticFiles(object):
    def __init__(self, folder=None, filename=None, redirect_to_login=True):
        self.folder = folder
        self.filename = filename
        self.redirect_to_login = redirect_to_login

    def on_get(self, req, resp, filename=None):
        """
        :type req: falcon.Request
        :type resp: falcon.Response
        """
        if self.redirect_to_login and not AuthMiddleware.validate_auth(req):
            resp.status = falcon.HTTP_FOUND
            # noinspection PyUnresolvedReferences
            resp.location = '/login'
            return

        file_path = filename or self.filename
        if self.folder:
            file_path = os.path.join(self.folder, file_path)
        if not os.path.isfile(file_path):
            raise falcon.HTTPNotFound(description='Requested page not found')

        mime_type, encoding = mimetypes.guess_type(file_path)
        etag, last_modified = self._get_static_info(file_path)

        # noinspection PyUnresolvedReferences
        resp.content_type = mime_type or 'text/plain'

        headers = {'Date': formatdate(time.time(), usegmt=True),
                   'ETag': etag,
                   'Last-Modified': last_modified,
                   'Cache-Control': 'max-age=86400'}
        resp.set_headers(headers)

        if_modified_since = req.get_header('if-modified-since', None)
        if if_modified_since and (parsedate(if_modified_since) >= parsedate(last_modified)):
            resp.status = falcon.HTTP_NOT_MODIFIED
            return

        if_none_match = req.get_header('if-none-match', None)
        if if_none_match and (if_none_match == '*' or etag in if_none_match):
            resp.status = falcon.HTTP_NOT_MODIFIED
            return

        resp.stream_len = os.path.getsize(file_path)
        resp.stream = open(file_path, mode='rb')

    @staticmethod
    def _get_static_info(file_path):
        mtime = os.stat(file_path).st_mtime
        return str(mtime), formatdate(mtime, usegmt=True)
