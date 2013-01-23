#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import os.path
from bs4 import BeautifulSoup
from django.conf import settings
from django.conf.urls import patterns
from django.core.urlresolvers import reverse
from geonode.geoserver.helpers import cascading_delete
from geonode.layers.models import Layer
from geonode.upload.models import Upload
from geonode.upload.views import _ALLOW_TIME_STEP
from geonode.urls import include
from geonode.urls import urlpatterns
from geoserver.catalog import Catalog
from gisdata import BAD_DATA
from gisdata import GOOD_DATA
from owslib.wms import WebMapService
from unittest import TestCase
import MultipartPostHandler
import csv
import glob
import json
import os
import signal
import subprocess
import tempfile
import time
import urllib
import urllib2
from zipfile import ZipFile

GEONODE_USER     = 'admin'
GEONODE_PASSWD   = 'admin'
GEONODE_URL      = settings.SITEURL.rstrip('/')
GEOSERVER_URL    = settings.GEOSERVER_BASE_URL
GEOSERVER_USER, GEOSERVER_PASSWD = settings.GEOSERVER_CREDENTIALS

import logging
logging.getLogger('south').setLevel(logging.WARNING)

# hack the global urls to ensure we're activated locally
urlpatterns += patterns('',(r'^upload/', include('geonode.upload.urls')))

def upload_step(step=None):
    step = reverse('data_upload',args=[step] if step else [])
    return step

def parse_cookies(cookies):
    res = {}
    for part in cookies.split(';'):
        key, value = part.split('=')
        res[key] = value
    return res


def get_wms(version='1.1.1',layer_name=None):
    """ Function to return an OWSLib WMS object """
    # right now owslib does not support auth for get caps
    # requests. Either we should roll our own or fix owslib
    url = GEOSERVER_URL + 'geonode/%s/wms' % layer_name
    return WebMapService(
        url,
        version=version,
        username=GEOSERVER_USER,
        password=GEOSERVER_PASSWD
    )


class Client(object):
    """client for making http requests"""

    def __init__(self, url, user, passwd):
        self.url = url
        self.user = user
        self.passwd = passwd
        self.opener = self._init_url_opener()

    def _init_url_opener(self):
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm='GeoNode realm',
            uri='',
            user=self.user,
            passwd=self.passwd
        )

        return urllib2.build_opener(
            auth_handler,
            urllib2.HTTPCookieProcessor,
            MultipartPostHandler.MultipartPostHandler
        )

    def make_request(self, path, data=None, ajax=False):
        url = path if path.startswith("http") else self.url + path
        req = urllib2.Request(
            url=url, data=data
        )
        if ajax:
            req.add_header('X_REQUESTED_WITH', 'XMLHttpRequest')
        return self.opener.open(req)

    def get(self, path):
        return self.make_request(path)

    def login(self):
        """ Method to login the GeoNode site"""
        params = {'csrfmiddlewaretoken': self.get_crsf_token(),
                  'username': self.user,
                  'next': '/',
                  'password': self.passwd}
        return self.make_request(
            '/account/login/',
            data=urllib.urlencode(params)
        )

    def upload_file(self, _file):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        spatial_files = ("dbf_file", "shx_file", "prj_file")

        base, ext = os.path.splitext(_file)
        params = {
            'permissions': '{"anonymous": "layer_readonly", "users": []}',
            'csrfmiddlewaretoken': self.get_crsf_token()
        }

        # deal with shapefiles
        if ext.lower() == '.shp':
            for spatial_file in spatial_files:
                ext, _ = spatial_file.split('_')
                file_path = base + '.' + ext
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'r')

        params['base_file'] = open(_file, 'r')
        resp = self.make_request(upload_step(), data=params, ajax=True)
        data = resp.read()
        try:
            return (resp, json.loads(data))
        except ValueError:
            raise ValueError('probably not json, status %s' % resp.getcode(), data)

    def get_html(self, path):
        """ Method that make a get request and passes the results to bs4
        Takes a path and returns a tuple
        """
        resp = self.get(path)
        return (resp, BeautifulSoup(resp.read()))

    def get_json(self, path):
        resp = self.get(path)
        return (resp, json.loads(resp.read()))

    def get_crsf_token(self):
        """ Method that makes a request against the home page to get
        the csrf token from the request cookies
        """
        resp = self.get('/')
        cookies = parse_cookies(resp.headers['set-cookie'])
        return cookies.get('csrftoken', None)

    def remove_layer(self, layer_name):
        self.login()
        return self.make_request(
            '/layers/geonode:' + layer_name + '/remove',
            data={'csrfmiddlewaretoken': self.get_crsf_token()}
        )


class UploaderBase(TestCase):

    settings_overrides = []

    @classmethod
    def setUpClass(cls):
        super(UploaderBase, cls).setUpClass()

        # don't accidentally delete anyone's layers
        if Layer.objects.all().count():
            if 'DELETE_LAYERS' not in os.environ:
                print
                print 'FAIL: There are layers in the test database'
                print 'Will not run integration tests unless `DELETE_LAYERS`'
                print 'Is specified as an environment variable'
                print
                raise Exception('FAIL, SEE ABOVE')

        # make a test_settings module that will apply our overrides
        test_settings = ['from geonode.settings import *']
        if os.path.exists('geonode/upload/tests/test_settings.py'):
            test_settings.append('from geonode.upload.tests.test_settings import *')
        for so in cls.settings_overrides:
            test_settings.append('%s=%s' % so)
        with open('integration_settings.py', 'w') as fp:
            fp.write('\n'.join(test_settings))

        # runserver with settings
        args = ['python','manage.py','runserver','--settings=integration_settings','--verbosity=0']
        # see http://www.doughellmann.com/PyMOTW/subprocess/#process-groups-sessions
        cls._runserver = subprocess.Popen(args, stderr=open('test.log','w') ,preexec_fn=os.setsid)

        # await startup
        cl = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        for i in range(5):
            try:
                cl.get_html('/')
                break
            except:
                time.sleep(.5)
        if cls._runserver.poll() is not None:
            raise Exception("Error starting server, check test.log")

    @classmethod
    def tearDownClass(cls):
        super(UploaderBase, cls).tearDownClass()

        # kill server process group
        os.killpg(cls._runserver.pid, signal.SIGKILL)
        if os.path.exists('integration_settings.py'):
            os.unlink('integration_settings.py')


    def setUp(self):
        super(UploaderBase, self).setUp()
        self._tempfiles = []
        self.client = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        self.catalog = Catalog(
            GEOSERVER_URL + 'rest', GEOSERVER_USER, GEOSERVER_PASSWD
        )
        # @todo - this is obviously the brute force approach - ideally,
        # these cases would be more declarative and delete only the things
        # they mess with
        for l in Layer.objects.all():
            try:
                l.delete()
            except:
                print 'unable to delete layer', l
        # and destroy anything left dangling on geoserver
        cat = Layer.objects.gs_catalog
        map(lambda name: cascading_delete(cat, name), [l.name for l in cat.get_layers()])

    def tearDown(self):
        super(UploaderBase, self).tearDown()
        map(os.unlink, self._tempfiles)

    def check_layer_geonode_page(self, path):
        """ Check that the final layer page render's correctly after
        an layer is uploaded """
        # the final url for uploader process. This does a redirect to
        # the final layer page in geonode
        resp, _ = self.client.get_html(path)
        self.assertTrue('content-type' in resp.headers)
        # if we don't get a content type of html back, thats how we
        # know there was an error.
        self.assertTrue(
            resp.headers['content-type'].startswith('text/html')
        )

    def check_layer_geoserver_caps(self, original_name):
        """ Check that a layer shows up in GeoServer's get
        capabilities document """
        # using owslib
        wms = get_wms(layer_name=original_name)
        self.assertTrue(original_name in wms.contents,
                        '%s is not in %s' % (original_name, wms.contents))

    def check_layer_geoserver_rest(self, original_name):
        """ Check that a layer shows up in GeoServer rest api after
        the uploader is done"""
        # using gsconfig to test the geoserver rest api.
        layer = self.catalog.get_layer(original_name)
        self.assertIsNotNone(layer is not None)

    def check_and_pass_through_timestep(self):
        raise Exception('not implemented')
        redirect_to = data['redirect_to']
        self.assertEquals(redirect_to, upload_step('time'))
        resp = self.client.make_request(upload_step('time'))
        self.assertEquals(resp.code, 200)
        data = {'csrfmiddlewaretoken': self.client.get_crsf_token()}
        resp = self.client.make_request(upload_step('time'), data)
        data = json.loads(resp.read())
        return resp, data

    def complete_raster_upload(self, file_path, resp, data):
        return self.complete_upload(file_path, resp, data, is_raster=True)
    
    def check_save_step(self, resp, data):
        """Verify the initial save step"""
        self.assertEquals(resp.code, 200)
        self.assertTrue(isinstance(data, dict))
        # make that the upload returns a success True key
        self.assertTrue(data['success'], 'expected success but got %s' % data)
        self.assertTrue('redirect_to' in data)

    def complete_upload(self, file_path, resp, data, is_raster=False):
        """Method to check if a layer was correctly uploaded to the
        GeoNode.

        arguments: file path, the django http response

           Checks to see if a layer is configured in Django
           Checks to see if a layer is configured in GeoServer
               checks the Rest API
               checks the get cap document """
               
        layer_name, ext = os.path.splitext(os.path.basename(file_path))
               
        self.check_save_step(resp, data)

        layer_page = self.finish_upload(data['redirect_to'], layer_name, is_raster)
                     
        self.check_layer_complete(layer_page, layer_name)
        
    def finish_upload(self, current_step, layer_name, is_raster=False, skip_srs=False):

        if (not is_raster and _ALLOW_TIME_STEP):
            resp, data = self.check_and_pass_through_timestep()
            self.assertEquals(resp.code, 200)
            self.assertTrue(data['success'], 'expected success but got %s' % data)
            self.assertTrue('redirect_to' in data)
            current_step = data['redirect_to']
            self.wait_for_progress(data.get('progress'))
            
        if not is_raster and not skip_srs:
            self.assertEquals(current_step, upload_step('srs'))
            # if all is good, the srs step will redirect to the final page
            resp = self.client.get(current_step)
        else:
            self.assertEquals(current_step, upload_step('final'))
            resp = self.client.get(current_step)
           
        # and the final page should redirect to tha layer page
        self.assertTrue(resp.geturl().endswith(layer_name), 
            'expected url to end with %s, but got "%s". possible orphan table in DB' % (layer_name, resp.geturl()))
        self.assertEquals(resp.code, 200)
        
        return resp.geturl()

    def check_upload_model(self, original_name):
        # we can only test this if we're using the same DB as the test instance
        if not settings.DB_DATASTORE: return
        try:
            upload = Upload.objects.get(layer__name=original_name)
        except Upload.DoesNotExist:
            self.fail('expected to find Upload object for %s' % original_name)
        self.assertTrue(upload.complete)
        
    def check_layer_complete(self, layer_page, original_name):
        '''check everything to verify the layer is complete'''
        self.check_layer_geonode_page(layer_page)
        self.check_layer_geoserver_caps(original_name)
        self.check_layer_geoserver_rest(original_name)
        self.check_upload_model(original_name)
        
    def check_invalid_projection(self, layer_name, resp, data):
        """ Makes sure that we got the correct response from an layer
        that can't be uploaded"""
        if _ALLOW_TIME_STEP:
            resp, data = self.check_and_pass_through_timestep()
        self.assertTrue(resp.code, 200)
        self.assertTrue(data['success'])
        self.assertEquals(upload_step("srs"), data['redirect_to'])
        resp, soup = self.client.get_html(data['redirect_to'])
        # grab an h2 and find the name there as part of a message saying it's bad
        h2 = soup.find_all(['h2'])[0]
        self.assertTrue(str(h2).find(layer_name))

    def upload_folder_of_files(self, folder, final_check):

        mains = ('.tif', '.shp', '.zip')

        def is_main(_file):
            _, ext = os.path.splitext(_file)
            return (ext.lower() in mains)

        self.client.login()
        main_files = filter(is_main, os.listdir(folder))
        for main in main_files:
            # get the abs path to the file
            _file = os.path.join(folder, main)
            base, _ = os.path.splitext(_file)
            resp, data = self.client.upload_file(_file)
            self.wait_for_progress(data.get('progress'))
            final_check(base, resp, data)

    def upload_file(self, fname, final_check, check_name=None):
        self.client.login()
        if not check_name:
            check_name, _ = os.path.splitext(fname)
        resp, data = self.client.upload_file(fname)
        self.wait_for_progress(data.get('progress'))
        final_check(check_name, resp, data)

    def wait_for_progress(self, progress_url):
        if progress_url:
            resp = self.client.get(progress_url)
            assert resp.getcode() == 200, 'Invalid progress status code'
            raw_data = resp.read()
            json_data = json.loads(raw_data)
            # "COMPLETE" state means done
            if json_data.get('state', '') == 'RUNNING':
                time.sleep(0.1)
                self.wait_for_progress(progress_url)

    def temp_file(self, ext):
        fd, abspath = tempfile.mkstemp(ext)
        self._tempfiles.append(abspath)
        return fd, abspath

    def make_csv(self, *rows):
        fd, abspath = self.temp_file('.csv')
        fp = os.fdopen(fd,'wb')
        out = csv.writer(fp)
        for r in rows:
            out.writerow(r)
        fp.close()
        return abspath


class TestUpload(UploaderBase):
    settings_overrides = [
        ('DB_DATASTORE', False)
    ]
    
    def test_shp_upload(self):
        """ Tests if a vector layer can be upload to a running GeoNode GeoServer"""
        fname = os.path.join(GOOD_DATA, 'vector', 'san_andres_y_providencia_water.shp')
        self.upload_file(fname, self.complete_upload)

    def test_raster_upload(self):
        """ Tests if a raster layer can be upload to a running GeoNode GeoServer"""
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        self.upload_file(fname, self.complete_raster_upload)

    def test_zipped_upload(self):
        """Test uploading a zipped shapefile"""
        fd, abspath = self.temp_file('.zip')
        fp = os.fdopen(fd,'wb')
        zf = ZipFile(fp, 'w')
        fpath = os.path.join(GOOD_DATA, 'vector', 'san_andres_y_providencia_poi.*')
        for f in glob.glob(fpath):
            zf.write(f, os.path.basename(f))
        zf.close()
        self.upload_file(abspath, self.complete_upload,
                         check_name='san_andres_y_providencia_poi')

    def test_invalid_layer_upload(self):
        """ Tests the layers that are invalid and should not be uploaded"""
        # this issue with this test is that the importer supports
        # shapefiles without an .prj
        invalid_path = os.path.join(BAD_DATA)
        self.upload_folder_of_files(invalid_path, self.check_invalid_projection)

    def test_extension_not_implemented(self):
        """Verify a error message is return when an unsupported layer is
        uploaded"""

        # try to upload ourselves
        # a python file is unsupported
        unsupported_path = __file__
        if unsupported_path.endswith('.pyc'):
            unsupported_path = unsupported_path.rstrip('c')

        self.client.login()  # make sure the client is logged in
        resp, data = self.client.upload_file(unsupported_path)
        # currently the upload returns a 200 when there is an error thrown
        self.assertEquals(resp.code, 200)
        self.assertTrue('success' in data)
        self.assertTrue(not data['success'])
        self.assertTrue('You uploaded a .py file' in data['errors'][0])

    def test_repeated_upload(self):
        """Verify that we can upload a shapefile twice """
        Layer.objects.filter(title='single_point').delete()

        shp = os.path.join(GOOD_DATA, 'vector', 'single_point.shp')
        base = 'single_point'
        self.client.login()
        resp, data = self.client.upload_file(shp)
        self.wait_for_progress(data.get('progress'))
        self.complete_upload(base, resp, data)

        # try uploading the same layer twice, note the appended '0'
        resp, data = self.client.upload_file(shp)
        self.wait_for_progress(data.get('progress'))
        self.complete_upload(base + "0", resp, data)

    def test_csv(self):
        '''make sure a csv upload fails gracefully/normally when not activated'''
        csv_file = self.make_csv(['lat','lon','thing'],['-100','-40','foo'])
        layer_name, ext = os.path.splitext(os.path.basename(csv_file))
        self.client.login()
        resp, data = self.client.upload_file(csv_file)
        self.assertTrue('success' in data)
        self.assertTrue(not data['success'])
        self.assertTrue('You uploaded a .csv file' in data['errors'][0])


class TestUploadDBDataStore(TestUpload):

    settings_overrides = [
        ('DB_DATASTORE', True)
    ]

    def test_csv(self):
        """Override the baseclass test and verify a correct CSV upload"""

        csv_file = self.make_csv(['lat','lon','thing'],['-100','-40','foo'])
        layer_name, ext = os.path.splitext(os.path.basename(csv_file))
        self.client.login()
        resp, form_data = self.client.upload_file(csv_file)
        self.check_save_step(resp, form_data)
        csv_step = form_data['redirect_to']
        self.assertEquals(csv_step, upload_step('csv'))
        form_data = dict(lat='lat', lng='lon', csrfmiddlewaretoken=self.client.get_crsf_token())
        resp = self.client.make_request(csv_step, form_data)

        self.assertTrue(resp.geturl().endswith(layer_name),
            'expected url to end with %s, but got %s' % (layer_name, resp.geturl()))
        self.assertEquals(resp.code, 200)

        self.check_layer_complete(resp.geturl(), layer_name)

    def test_time(self):
        """Verify that uploading time based csv files works properly"""

        timedir = os.path.join(GOOD_DATA, 'time')
        self.client.login()
        layer_name = 'boxes_with_date'
        shp = os.path.join(timedir, '%s.shp' % layer_name)

        # get to time step
        resp, data = self.client.upload_file(shp)
        self.wait_for_progress(data.get('progress'))
        self.assertEquals(resp.code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(data['redirect_to'], upload_step('time'))

        resp, data = self.client.get_html(upload_step('time'))
        self.assertEquals(resp.code, 200)
        data = dict(csrfmiddlewaretoken=self.client.get_crsf_token(),
                    time_attribute='date',
                    presentation_strategy='LIST',
                    )
        resp = self.client.make_request(upload_step('time'), data)

        self.assertTrue(resp.geturl().endswith(layer_name),
            'expected url to end with %s, but got %s' % (layer_name, resp.geturl()))
        self.assertEquals(resp.code, 200)

        self.check_layer_complete(resp.geturl(), layer_name)
        # verify our 100 timestamps appear in the WMS caps doc
        wms = get_wms(layer_name=layer_name)
        layer_info = wms.items()[0][1]
        self.assertEquals(100, len(layer_info.timepositions))


# disable DB_DATASTORE tests if not setup
if not settings.DB_DATASTORE:
    print 'skipping DB_DATASTORE tests'
    del TestUploadDBDataStore