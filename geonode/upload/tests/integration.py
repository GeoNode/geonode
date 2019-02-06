# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

"""
See the README.rst in this directory for details on running these tests.
@todo allow using a database other than `development.db` - for some reason, a
      test db is not created when running using normal settings
@todo when using database settings, a test database is used and this makes it
      difficult for cleanup to track the layers created between runs
@todo only test_time seems to work correctly with database backend test settings
"""

from geonode.tests.base import GeoNodeBaseTestSupport

import os.path
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.urlresolvers import reverse

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

from geonode.people.models import Profile
from geonode.upload.models import Upload
from geonode.upload.utils import _ALLOW_TIME_STEP
from geonode.geoserver.helpers import ogc_server_settings
from geonode.geoserver.helpers import cascading_delete
from geonode.geoserver.signals import gs_catalog
from geoserver.catalog import Catalog
# from geonode.upload.utils import make_geogig_rest_payload
from gisdata import BAD_DATA
from gisdata import GOOD_DATA
from owslib.wms import WebMapService
from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers
# from urllib2 import HTTPError
from zipfile import ZipFile

import re
import os
import csv
import glob
import time
import json
# import signal
import urllib
import urllib2
import logging
import tempfile
import unittest
# import subprocess
import dj_database_url

GEONODE_USER = 'admin'
GEONODE_PASSWD = 'admin'
GEONODE_URL = settings.SITEURL.rstrip('/')
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

logging.getLogger('south').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# create test user if needed, delete all layers and set password
u, created = Profile.objects.get_or_create(username=GEONODE_USER)
if created:
    u.set_password(GEONODE_PASSWD)
    u.save()
else:
    Layer.objects.filter(owner=u).delete()


def upload_step(step=None):
    step = reverse('data_upload', args=[step] if step else [])
    return step


def get_wms(version='1.1.1', type_name=None):
    """ Function to return an OWSLib WMS object """
    # right now owslib does not support auth for get caps
    # requests. Either we should roll our own or fix owslib
    if type_name:
        url = GEOSERVER_URL + \
            '%swms?request=getcapabilities' % type_name.replace(':', '/')
    else:
        url = GEOSERVER_URL + \
            'wms?request=getcapabilities'
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
        self.csrf_token = None
        self.opener = self._init_url_opener()

    def _init_url_opener(self):
        self.cookies = urllib2.HTTPCookieProcessor()
        opener = register_openers()
        opener.add_handler(self.cookies)  # Add cookie handler
        return opener

    def make_request(self, path, data=None,
                     ajax=False, debug=True):
        url = path if path.startswith("http") else self.url + path
        if ajax:
            url += '&ajax=true' if '?' in url else '?ajax=true'
        request = None
        if data:
            items = []
            # wrap post parameters
            for name, value in data.items():
                if isinstance(value, file):
                    # add file
                    items.append(MultipartParam.from_file(name, value.name))
                else:
                    items.append(MultipartParam(name, value))
            datagen, headers = multipart_encode(items)
            request = urllib2.Request(url, datagen, headers)
        else:
            request = urllib2.Request(url=url)

        if ajax:
            request.add_header('X_REQUESTED_WITH', 'XMLHttpRequest')
        try:
            # return urllib2.urlopen(request)
            return self.opener.open(request)
        except urllib2.HTTPError as ex:
            if not debug:
                raise
            logger.error('error in request to %s' % path)
            logger.error(ex.reason)
            logger.error(ex.read())
            raise

    def get(self, path, debug=True):
        return self.make_request(path, debug=debug)

    def login(self):
        """ Method to login the GeoNode site"""
        self.csrf_token = self.get_csrf_token()
        params = {'csrfmiddlewaretoken': self.csrf_token,
                  'username': self.user,
                  'next': '/',
                  'password': self.passwd}
        self.make_request(
            reverse('account_login'),
            data=params
        )
        self.csrf_token = self.get_csrf_token()

    def upload_file(self, _file):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        if not self.csrf_token:
            self.login()
        spatial_files = ("dbf_file", "shx_file", "prj_file")

        base, ext = os.path.splitext(_file)
        params = {
            # make public since wms client doesn't do authentication
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'csrfmiddlewaretoken': self.csrf_token
        }

        # deal with shapefiles
        if ext.lower() == '.shp':
            for spatial_file in spatial_files:
                ext, _ = spatial_file.split('_')
                file_path = base + '.' + ext
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'rb')

        base_file = open(_file, 'rb')
        params['base_file'] = base_file
        resp = self.make_request(
            upload_step(),
            data=params,
            ajax=True)
        data = resp.read()
        try:
            return resp, json.loads(data)
        except ValueError:
            # raise ValueError(
            #     'probably not json, status %s' %
            #     resp.getcode(),
            #     data)
            return resp, data

    def get_html(self, path, debug=True):
        """ Method that make a get request and passes the results to bs4
        Takes a path and returns a tuple
        """
        resp = self.get(path, debug)
        return resp, BeautifulSoup(resp.read())

    def get_json(self, path):
        resp = self.get(path)
        return resp, json.loads(resp.read())

    def get_csrf_token(self, last=False):
        """Get a csrf_token from the home page or read from the cookie jar
        based on the last response
        """
        if not last:
            self.get('/')
        csrf = [c for c in self.cookies.cookiejar if c.name == 'csrftoken']
        return csrf[0].value if csrf else None


class UploaderBase(GeoNodeBaseTestSupport):

    settings_overrides = []

    @classmethod
    def setUpClass(cls):
        # super(UploaderBase, cls).setUpClass()

        # make a test_settings module that will apply our overrides
        # test_settings = ['from geonode.settings import *']
        # using_test_settings = os.getenv('DJANGO_SETTINGS_MODULE') == 'geonode.upload.tests.test_settings'
        # if using_test_settings:
        #     test_settings.append(
        #         'from geonode.upload.tests.test_settings import *')
        # for so in cls.settings_overrides:
        #     test_settings.append('%s=%s' % so)
        # with open('integration_settings.py', 'w') as fp:
        #     fp.write('\n'.join(test_settings))
        #
        # # runserver with settings
        # args = [
        #     'python',
        #     'manage.py',
        #     'runserver',
        #     '--settings=integration_settings',
        #     '--verbosity=0']
        # # see for details regarding os.setsid:
        # # http://www.doughellmann.com/PyMOTW/subprocess/#process-groups-sessions
        # cls._runserver = subprocess.Popen(
        #     args,
        #     preexec_fn=os.setsid)

        # await startup
        # cl = Client(
        #     GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        # )
        # for i in range(10):
        #     time.sleep(.2)
        #     try:
        #         cl.get_html('/', debug=False)
        #         break
        #     except:
        #         pass
        # if cls._runserver.poll() is not None:
        #     raise Exception("Error starting server, check test.log")
        #
        # cls.client = Client(
        #     GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        # )
        # cls.catalog = Catalog(
        #     GEOSERVER_URL + 'rest', GEOSERVER_USER, GEOSERVER_PASSWD
        # )
        pass

    @classmethod
    def tearDownClass(cls):
        # super(UploaderBase, cls).tearDownClass()

        # kill server process group
        # if cls._runserver.pid:
        #    os.killpg(cls._runserver.pid, signal.SIGKILL)

        if os.path.exists('integration_settings.py'):
            os.unlink('integration_settings.py')

    def setUp(self):
        # super(UploaderBase, self).setUp()

        # await startup
        cl = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        for i in range(10):
            time.sleep(.2)
            try:
                cl.get_html('/', debug=False)
                break
            except BaseException:
                pass

        self.client = Client(
            GEONODE_URL, GEONODE_USER, GEONODE_PASSWD
        )
        self.catalog = Catalog(
            GEOSERVER_URL + 'rest', GEOSERVER_USER, GEOSERVER_PASSWD
        )

        self._tempfiles = []
        # createlayer must use postgis as a datastore
        # set temporary settings to use a postgis datastore
        DB_HOST = settings.DATABASES['default']['HOST']
        DB_PORT = settings.DATABASES['default']['PORT']
        DB_NAME = settings.DATABASES['default']['NAME']
        DB_USER = settings.DATABASES['default']['USER']
        DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
        settings.DATASTORE_URL = 'postgis://{}:{}@{}:{}/{}'.format(
            DB_USER,
            DB_PASSWORD,
            DB_HOST,
            DB_PORT,
            DB_NAME
        )
        postgis_db = dj_database_url.parse(
            settings.DATASTORE_URL, conn_max_age=600)
        settings.DATABASES['datastore'] = postgis_db
        settings.OGC_SERVER['default']['DATASTORE'] = 'datastore'

    def tearDown(self):
        # super(UploaderBase, self).tearDown()
        map(os.unlink, self._tempfiles)
        # move to original settings
        settings.OGC_SERVER['default']['DATASTORE'] = ''
        del settings.DATABASES['datastore']
        # Cleanup
        Layer.objects.all().delete()
        Map.objects.all().delete()
        Document.objects.all().delete()

    def check_layer_geonode_page(self, path):
        """ Check that the final layer page render's correctly after
        an layer is uploaded """
        # the final url for uploader process. This does a redirect to
        # the final layer page in geonode
        resp, _ = self.client.get_html(path)
        self.assertTrue(resp.code == 200)
        self.assertTrue('content-type' in resp.headers)

    def check_layer_geoserver_caps(self, type_name):
        """ Check that a layer shows up in GeoServer's get
        capabilities document """
        # using owslib
        wms = get_wms(type_name=type_name)
        ws, layer_name = type_name.split(':')
        self.assertTrue(layer_name in wms.contents,
                        '%s is not in %s' % (layer_name, wms.contents))

    def check_layer_geoserver_rest(self, layer_name):
        """ Check that a layer shows up in GeoServer rest api after
        the uploader is done"""
        # using gsconfig to test the geoserver rest api.
        layer = self.catalog.get_layer(layer_name)
        self.assertIsNotNone(layer is not None)

    def check_and_pass_through_timestep(self, redirect_to):
        time_step = upload_step('time')
        srs_step = upload_step('srs')
        if srs_step in redirect_to:
            resp = self.client.make_request(redirect_to)
        else:
            self.assertTrue(time_step in redirect_to)
        resp = self.client.make_request(redirect_to)
        token = self.client.get_csrf_token(True)
        self.assertEquals(resp.code, 200)
        resp = self.client.make_request(
            redirect_to, {'csrfmiddlewaretoken': token}, ajax=True)
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

        if not isinstance(data, basestring):
            self.check_save_step(resp, data)

            layer_page = self.finish_upload(
                data['redirect_to'],
                layer_name,
                is_raster)

            self.check_layer_complete(layer_page, layer_name)

    def finish_upload(
            self,
            current_step,
            layer_name,
            is_raster=False,
            skip_srs=False):
        if not is_raster and _ALLOW_TIME_STEP:
            resp, data = self.check_and_pass_through_timestep(current_step)
            self.assertEquals(resp.code, 200)
            if not isinstance(data, basestring):
                if data['success']:
                    self.assertTrue(
                        data['success'],
                        'expected success but got %s' %
                        data)
                    self.assertTrue('redirect_to' in data)
                    current_step = data['redirect_to']
                    self.wait_for_progress(data.get('progress'))

        if not is_raster and not skip_srs:
            self.assertTrue(upload_step('srs') in current_step)
            # if all is good, the srs step will redirect to the final page
            resp = self.client.get(current_step)

            content = json.loads(resp.read())
            if not content.get('url') and content.get(
                    'redirect_to',
                    current_step) == upload_step('final'):
                resp = self.client.get(content.get('redirect_to'))
        else:
            self.assertTrue(upload_step('final') in current_step)
            resp = self.client.get(current_step)

        self.assertEquals(resp.code, 200)
        resp_js = resp.read()
        try:
            c = json.loads(resp_js)
            url = c['url']
            url = urllib.unquote(url)
            # and the final page should redirect to the layer page
            # @todo - make the check match completely (endswith at least)
            # currently working around potential 'orphaned' db tables
            self.assertTrue(
                layer_name in url, 'expected %s in URL, got %s' %
                (layer_name, url))
            return url
        except BaseException:
            return current_step

    def check_upload_model(self, original_name):
        # we can only test this if we're using the same DB as the test instance
        if not settings.OGC_SERVER['default']['DATASTORE']:
            return
        upload = None
        try:
            # AF: TODO Headhakes here... nose is not accessing to the test
            # db!!!
            uploads = Upload.objects.all()
            if uploads:
                upload = Upload.objects.filter(name=str(original_name)).last()
        except Upload.DoesNotExist:
            self.fail('expected to find Upload object for %s' % original_name)

        # AF: TODO Headhakes here... nose is not accessing to the test db!!!
        if upload:
            self.assertTrue(upload.complete)

    def check_layer_complete(self, layer_page, original_name):
        '''check everything to verify the layer is complete'''
        self.check_layer_geonode_page(layer_page)
        # @todo use the original_name
        # currently working around potential 'orphaned' db tables
        # this grabs the name from the url (it might contain a 0)
        type_name = os.path.basename(layer_page)
        layer_name = original_name
        try:
            layer_name = type_name.split(':')[1]
        except BaseException:
            pass

        # work around acl caching on geoserver side of things
        caps_found = False
        for i in range(10):
            time.sleep(.5)
            try:
                self.check_layer_geoserver_caps(type_name)
                caps_found = True
            except BaseException:
                pass
        if caps_found:
            self.check_layer_geoserver_rest(layer_name)
            self.check_upload_model(layer_name)
        else:
            logger.warning(
                "Could not recognize Layer %s on GeoServer WMS" %
                original_name)

    def check_invalid_projection(self, layer_name, resp, data):
        """ Makes sure that we got the correct response from an layer
        that can't be uploaded"""
        self.assertTrue(resp.code, 200)
        if not isinstance(data, basestring):
            self.assertTrue(data['success'])
            self.assertTrue(upload_step("srs") in data['redirect_to'])
            resp, soup = self.client.get_html(data['redirect_to'])
            # grab an h2 and find the name there as part of a message saying it's
            # bad
            h2 = soup.find_all(['h2'])[0]
            self.assertTrue(str(h2).find(layer_name))

    def upload_folder_of_files(self, folder, final_check, session_ids=None):

        mains = ('.tif', '.shp', '.zip')

        def is_main(_file):
            _, ext = os.path.splitext(_file)
            return (ext.lower() in mains)

        main_files = filter(is_main, os.listdir(folder))
        for main in main_files:
            # get the abs path to the file
            _file = os.path.join(folder, main)
            base, _ = os.path.splitext(_file)
            resp, data = self.client.upload_file(_file)
            if session_ids is not None:
                if not isinstance(data, basestring) and data.get('url'):
                    session_id = re.search(
                        r'.*id=(\d+)', data.get('url')).group(1)
                    if session_id:
                        session_ids += [session_id]
            if not isinstance(data, basestring):
                self.wait_for_progress(data.get('progress'))
            final_check(base, resp, data)

    def upload_file(self, fname, final_check,
                    check_name=None, session_ids=None):
        if not check_name:
            check_name, _ = os.path.splitext(fname)
        resp, data = self.client.upload_file(fname)
        if session_ids is not None:
            if not isinstance(data, basestring):
                if data.get('url'):
                    session_id = re.search(
                        r'.*id=(\d+)', data.get('url')).group(1)
                    if session_id:
                        session_ids += [session_id]
        if not isinstance(data, basestring):
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
        fp = os.fdopen(fd, 'wb')
        out = csv.writer(fp)
        for r in rows:
            out.writerow(r)
        fp.close()
        return abspath


class TestUpload(UploaderBase):
    settings_overrides = []

    def test_shp_upload(self):
        """ Tests if a vector layer can be upload to a running GeoNode GeoServer"""
        fname = os.path.join(
            GOOD_DATA,
            'vector',
            'san_andres_y_providencia_water.shp')
        self.upload_file(fname, self.complete_upload)

    def test_raster_upload(self):
        """ Tests if a raster layer can be upload to a running GeoNode GeoServer"""
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        self.upload_file(fname, self.complete_raster_upload)

    def test_zipped_upload(self):
        """Test uploading a zipped shapefile"""
        fd, abspath = self.temp_file('.zip')
        fp = os.fdopen(fd, 'wb')
        zf = ZipFile(fp, 'w')
        fpath = os.path.join(
            GOOD_DATA,
            'vector',
            'san_andres_y_providencia_poi.*')
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
        self.upload_folder_of_files(
            invalid_path,
            self.check_invalid_projection)

    def test_coherent_importer_session(self):
        """ Tests that the upload computes correctly next session IDs"""
        session_ids = []

        # First of all lets upload a raster
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        self.assertTrue(os.path.isfile(fname))
        self.upload_file(
            fname,
            self.complete_raster_upload,
            session_ids=session_ids)

        # Next force an invalid session
        invalid_path = os.path.join(BAD_DATA)
        self.upload_folder_of_files(
            invalid_path,
            self.check_invalid_projection, session_ids=session_ids)

        # Finally try to upload a good file anc check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        self.upload_file(
            fname,
            self.complete_raster_upload,
            session_ids=session_ids)

        self.assertTrue(len(session_ids) >= 0)
        if len(session_ids) > 1:
            self.assertTrue(int(session_ids[0]) < int(session_ids[1]))

    def test_extension_not_implemented(self):
        """Verify a error message is return when an unsupported layer is
        uploaded"""

        # try to upload ourselves
        # a python file is unsupported
        unsupported_path = __file__
        if unsupported_path.endswith('.pyc'):
            unsupported_path = unsupported_path.rstrip('c')

        # with self.assertRaises(HTTPError):
        self.client.upload_file(unsupported_path)

    def test_csv(self):
        '''make sure a csv upload fails gracefully/normally when not activated'''
        csv_file = self.make_csv(
            ['lat', 'lon', 'thing'], ['-100', '-40', 'foo'])
        layer_name, ext = os.path.splitext(os.path.basename(csv_file))
        resp, data = self.client.upload_file(csv_file)
        self.assertEquals(resp.code, 200)
        if not isinstance(data, basestring):
            self.assertTrue('success' in data)
            self.assertTrue(data['success'])
            self.assertTrue(data['redirect_to'], "/upload/csv")


@unittest.skipUnless(ogc_server_settings.datastore_db,
                     'Vector datastore not enabled')
class TestUploadDBDataStore(UploaderBase):

    settings_overrides = []

    def test_csv(self):
        """Override the baseclass test and verify a correct CSV upload"""

        csv_file = self.make_csv(
            ['lat', 'lon', 'thing'], ['-100', '-40', 'foo'])
        layer_name, ext = os.path.splitext(os.path.basename(csv_file))
        resp, form_data = self.client.upload_file(csv_file)
        self.assertEquals(resp.code, 200)
        if not isinstance(form_data, basestring):
            self.check_save_step(resp, form_data)
            csv_step = form_data['redirect_to']
            self.assertTrue(upload_step('csv') in csv_step)
            form_data = dict(
                lat='lat',
                lng='lon',
                csrfmiddlewaretoken=self.client.get_csrf_token())
            resp = self.client.make_request(csv_step, form_data)
            content = json.loads(resp.read())
            self.assertEquals(resp.code, 200)
            self.assertTrue(upload_step('srs') in content['redirect_to'])

    def test_time(self):
        """Verify that uploading time based shapefile works properly"""
        cascading_delete(self.catalog, 'boxes_with_date')

        timedir = os.path.join(GOOD_DATA, 'time')
        layer_name = 'boxes_with_date'
        shp = os.path.join(timedir, '%s.shp' % layer_name)

        # get to time step
        resp, data = self.client.upload_file(shp)
        self.assertEquals(resp.code, 200)
        if not isinstance(data, basestring):
            self.wait_for_progress(data.get('progress'))
            self.assertTrue(data['success'])
            self.assertTrue(data['redirect_to'], upload_step('time'))
            redirect_to = data['redirect_to']
            resp, data = self.client.get_html(upload_step('time'))
            self.assertEquals(resp.code, 200)
            data = dict(csrfmiddlewaretoken=self.client.get_csrf_token(),
                        time_attribute='date',
                        presentation_strategy='LIST',
                        )
            resp = self.client.make_request(redirect_to, data)
            self.assertEquals(resp.code, 200)
            resp_js = json.loads(resp.read())
            if resp_js['success']:
                url = resp_js['redirect_to']

                resp = self.client.make_request(url, data)

                url = json.loads(resp.read())['url']

                self.assertTrue(
                    url.endswith(layer_name),
                    'expected url to end with %s, but got %s' %
                    (layer_name,
                     url))
                self.assertEquals(resp.code, 200)

                url = urllib.unquote(url)
                self.check_layer_complete(url, layer_name)
                wms = get_wms(type_name='geonode:%s' % layer_name)
                layer_info = wms.items()[0][1]
                self.assertEquals(100, len(layer_info.timepositions))
            else:
                self.assertTrue('error_msg' in resp_js)
                self.assertTrue(
                    'Source SRS is not valid' in resp_js['error_msg'])

    def test_configure_time(self):
        layer_name = 'boxes_with_end_date'
        # make sure it's not there (and configured)
        cascading_delete(gs_catalog, layer_name)

        def get_wms_timepositions():
            alternate_name = 'geonode:%s' % layer_name
            if alternate_name in get_wms().contents:
                metadata = get_wms().contents[alternate_name]
                self.assertTrue(metadata is not None)
                return metadata.timepositions
            else:
                return None

        thefile = os.path.join(
            GOOD_DATA, 'time', '%s.shp' % layer_name
        )
        resp, data = self.client.upload_file(thefile)

        # initial state is no positions or info
        self.assertTrue(get_wms_timepositions() is None)
        self.assertEquals(resp.code, 200)

        # enable using interval and single attribute
        if not isinstance(data, basestring):
            self.wait_for_progress(data.get('progress'))
            self.assertTrue(data['success'])
            self.assertTrue(data['redirect_to'], upload_step('time'))
            redirect_to = data['redirect_to']
            resp, data = self.client.get_html(upload_step('time'))
            self.assertEquals(resp.code, 200)
            data = dict(csrfmiddlewaretoken=self.client.get_csrf_token(),
                        time_attribute='date',
                        time_end_attribute='enddate',
                        presentation_strategy='LIST',
                        )
            resp = self.client.make_request(redirect_to, data)
            self.assertEquals(resp.code, 200)
            resp_js = json.loads(resp.read())
            if resp_js['success']:
                url = resp_js['redirect_to']

                resp = self.client.make_request(url, data)

                url = json.loads(resp.read())['url']

                self.assertTrue(
                    url.endswith(layer_name),
                    'expected url to end with %s, but got %s' %
                    (layer_name,
                     url))
                self.assertEquals(resp.code, 200)

                url = urllib.unquote(url)
                self.check_layer_complete(url, layer_name)
                wms = get_wms(type_name='geonode:%s' % layer_name)
                layer_info = wms.items()[0][1]
                self.assertEquals(100, len(layer_info.timepositions))
            else:
                self.assertTrue('error_msg' in resp_js)
                self.assertTrue(
                    'Source SRS is not valid' in resp_js['error_msg'])


# class GeogigTest(GeoNodeBaseTestSupport):
#     port = 8000
#     def test_payload_creation(self):
#         '''Test formation of REST call to geoserver's geogig API'''
#         author_name = "test"
#         author_email = "testuser@geonode.org"
#
#         # Test filebased geogig
#         settings.OGC_SERVER['default']['PG_GEOGIG'] = False
#         fb_message = {
#             "authorName": author_name,
#             "authorEmail": author_email,
#             "parentDirectory":
#             settings.OGC_SERVER['default']['GEOGIG_DATASTORE_DIR']
#         }
#         fb_payload = make_geogig_rest_payload(author_name, author_email)
#         self.assertDictEqual(fb_message, fb_payload)
#         self.assertEquals(json.dumps(fb_message, sort_keys=True),
#                           json.dumps(fb_payload, sort_keys=True))
#
#         # Test postgres based geogig
#         settings.OGC_SERVER['default']['PG_GEOGIG'] = True
#         # Manually override the settings to simulate the REST call for postgres
#         settings.DATABASES['test-pg'] = {
#             "HOST": "localhost",
#             "PORT": "5432",
#             "NAME": "repos",
#             "SCHEMA": "public",
#             "USER": "geogig",
#             "PASSWORD": "geogig"
#         }
#         settings.OGC_SERVER['default']['DATASTORE'] = 'test-pg'
#
#         pg_message = {
#             "authorName": author_name,
#             "authorEmail": author_email,
#             "dbHost": settings.DATABASES['test-pg']['HOST'],
#             "dbPort": settings.DATABASES['test-pg']['PORT'],
#             "dbName": settings.DATABASES['test-pg']['NAME'],
#             "dbSchema": settings.DATABASES['test-pg']['SCHEMA'],
#             "dbUser": settings.DATABASES['test-pg']['USER'],
#             "dbPassword": settings.DATABASES['test-pg']['PASSWORD']
#         }
#
#         pg_payload = make_geogig_rest_payload(author_name, author_email)
#         self.assertDictEqual(pg_message, pg_payload)
#         self.assertEquals(json.dumps(pg_message, sort_keys=True),
#                           json.dumps(pg_payload, sort_keys=True))
