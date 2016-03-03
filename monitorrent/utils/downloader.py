import cgi
import requests


def download(request, **kwargs):
    if isinstance(request, requests.PreparedRequest):
        response = requests.session().send(request, **kwargs)
    else:
        response = requests.get(request, **kwargs)
    if response.status_code == 200:
        filename = None
        if 'content-disposition' in response.headers:
            content_disposition = response.headers['content-disposition']
            t, params = cgi.parse_header(content_disposition)
            if t == 'attachment' and 'filename' in params:
                filename = params['filename']

        return response, filename
    else:
        return response, None
