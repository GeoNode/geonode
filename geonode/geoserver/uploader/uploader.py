import httplib2
import logging
import os
import pprint
import json
import mimetypes

from urlparse import urlparse
from urllib import urlencode

from geonode.geoserver.uploader.api import parse_response
from geonode.geoserver.uploader.utils import shp_files 

_logger = logging.getLogger(__name__)

class Uploader(object):

    def __init__(self, url, username="admin", password="geoserver"):
        self.client = _Client(url,username,password)

    def _call(self,fun,*args):
        robj = fun(*args)
        if isinstance(robj, list):
            for i in robj:
                i._uploader = self
        else:
            robj._uploader = self
        return robj

    def get_sessions(self):
        return self._call(self.client.get_imports)
        
    def get_session(self,id):
        """Get an existing session by id.
        """
        return self._call(self.client.get_import,id)

    def start_import(self, import_id=None):
        """Create a new import session.
        import_id - optional id to specify
        returns an uploader.api.Session object
        """
        session = self._call(self.client.start_import, import_id)
        if import_id: assert session.id >= import_id
        return session
        
    def upload(self, fpath, use_url=False, import_id=None):
        """Try a complete import - create a session and upload the provided file.
        fpath can be a path to a zip file or the 'main' file if a shapefile or a tiff
        returns a uploader.api.Session object
        
        use_url - if True, will post a URL to geoserver, not the file itself
                  for now, this only works with actual files, not remote urls
        import_id - if provided, PUT to the endpoint to create the specified id
        """
        files = [ fpath ]
        if fpath.lower().endswith(".shp"):
            files = shp_files(fpath)
            
        session = self.start_import(import_id)
        session.upload_task(files, use_url)
        return session
        
    # pickle protocol - client object cannot be serialized
    # this allows api objects to be seamlessly pickled and loaded without restarting
    # the connection more explicitly but this will have consequences if other state is stored
    # in the uploader or client objects
    def __getstate__(self):
        cl = self.client
        return {'url':cl.service_url,'username':cl.username,'password':cl.password}
    def __setstate__(self,state):
        self.client = _Client(state['url'],state['username'],state['password'])
        
class BadRequest(Exception):
    pass
            
class RequestFailed(Exception):
    pass

class NotFound(Exception):
    pass
        
class _Client(object):
    """Lower level http client"""

    # @todo some sanity on return values, either parsed object or resp,content tuple
    
    def __init__(self, url, username, password):
        self.service_url = url
        if self.service_url.endswith("/"):
            self.service_url = self.service_url.strip("/")
        self.http = httplib2.Http()
        self.username = username
        self.password = password
        self.http.add_credentials(self.username, self.password)
        netloc = urlparse(url).netloc
        self.http.authorizations.append(
            httplib2.BasicAuthentication(
                (username, password),
                netloc,
                url,
                {},
                None,
                None,
                self.http
            ))
            
    def url(self,path):
        return "%s/%s" % (self.service_url,path)

    def post(self, url):
        return self._request(url, "POST")
    
    def delete(self, url):
        return self._request(url, "DELETE")
        
    def put_json(self, url, data):
        return self._request(url, "PUT", data, {
            "Content-type" : "application/json"
        })
        
    def _parse_errors(self, content):
        try:
            resp = json.loads(content)
        except ValueError:
            return content
        return resp['errors']
    
    def _request(self, url, method="GET", data=None, headers={}):
        _logger.info("%s request to %s:\n%s",method,url,data)
        resp, content = self.http.request(url,method,data,headers)
        _debug(resp, content)
        if resp.status == 404:
            raise NotFound()
        if resp.status < 200 or resp.status > 299:
            if resp.status == 400:
                raise BadRequest(*self._parse_errors(content))
            raise RequestFailed(resp.status,content)
        return resp, content
    
    def post_upload_url(self, url, upload_url):
        data = urlencode({
            'url' : upload_url
        })
        return self._request(url, "POST", data, {
            # importer very picky
            'Content-type' : "application/x-www-form-urlencoded"
        })
        
    def put_zip(self,url,payload):
        message = open(payload)
        with message:
            return self._request(url,"PUT",message,{
                "Content-type": "application/zip",
            })
            
    def get_import(self,i):
        return parse_response(self._request(self.url("imports/%s" % i)))

    def get_imports(self):
        return parse_response(self._request(self.url("imports")))
    
    def start_import(self, import_id=None):
        method = 'POST'
        if import_id is not None:
            url = self.url("imports/%s" % import_id)
            method = 'PUT'
        else:
            url = self.url("imports")
        return parse_response(self._request(url, method))
        
    def post_multipart(self,url,files,fields=[]):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of name or (name,filename) or (name, filename, value) 
        elements for data to be uploaded as files
        
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        _logger.info("post_multipart %s %s %s",url,files,fields)
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % str(key))
            L.append('')
            L.append(str(value))
        for fpair in files:
            if isinstance(fpair,basestring):
                fpair = (fpair,fpair)
            key = fpair[0]
            if len(fpair) == 2:
                filename = os.path.basename(fpair[1])
                fp = open(fpair[1])
                value = fp.read()
                fp.close()
            else:
                filename, value = fpair[1:]
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (str(key), str(filename)))
            L.append('Content-Type: %s' % _get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        return self._request(
            url, 'POST', CRLF.join(L), {
                'Content-Type' : 'multipart/form-data; boundary=%s' % BOUNDARY
            }
        )
        
        
def _get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def _debug(resp, content):
    if _logger.isEnabledFor(logging.DEBUG):
        _logger.debug("response : %s",pprint.pformat(resp))
        if "content-type" in resp and resp['content-type'] == 'application/json':
            try:
                content = json.loads(content) 
                content = json.dumps(content,indent=2)
            except ValueError:
                pass

        _logger.debug("content : %s",content)
