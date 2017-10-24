from __future__ import print_function
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import unittest

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from geonode.contrib.dataverse_layer_metadata.models import DataverseLayerMetadata
from geonode.contrib.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm, CheckForExistingLayerForm

from django.conf import settings

def msg(m): print(m)
def dashes(): msg('-' * 40)
def msgt(m): dashes(); msg(m); dashes()

class ValidationFormTest(TestCase):

    def setUp(self):
         self.test_data = {\
                     #
                     # Datafile
                     #
                     u'datafile_content_type': u'application/zipped-shapefile',\
                     u'datafile_create_datetime': u'2014-09-30 10:00:54.544',\
                     u'datafile_download_url': u'http://localhost:8080/api/access/datafile/1388',\
                     u'datafile_expected_md5_checksum': u'e16c3b5c43781343ad6dfa180f176d7c',\
                     u'datafile_filesize': 225975,\
                     u'datafile_id': 1388,\
                     u'datafile_label': u'social_disorder_in_boston_yqh.zip',\
                     #
                     # Dataset
                     #
                     u'dataset_citation': u'Privileged, Pete, 2014, "social disorder", http://dx.doi.org/10.5072/FK2/1383,  Root Dataverse,  DRAFT VERSION ',\
                     u'dataset_description': u'',\
                     u'dataset_id': 1383,\
                     u'dataset_name': u'social disorder',\
                     u'dataset_semantic_version': u'DRAFT',\
                     u'dataset_version_id': 362,\
                     #
                     # Dataverse
                     #
                     u'dataverse_description': u'The root dataverse.',\
                     u'dataverse_id': 1,\
                     u'dataverse_installation_name': u'Harvard Dataverse',\
                     u'dataverse_name': u'Root',\
                     #
                     # Dataverse user
                     #
                     u'dv_user_email': u'pete@malinator.com',\
                     u'dv_user_id': 1,\
                     u'dv_username': u'Pete Privileged',\
                     u'return_to_dataverse_url': u'http://localhost:8080/dataset.xhtml?id=1383&versionId362'\
                    }
    def test_form_validation1(self):

        msgt('(1) Test valid data')

        validation_form = DataverseLayerMetadataValidationForm(self.test_data)
        #print 'valid',validation_form.is_valid()
        self.assertEqual(validation_form.is_valid(), True)


    def test_form_validation2(self):

        msgt('(2) Test invalid data for: [dataset_id, return_to_dataverse_url]')

        tdata = self.test_data.copy()
        tdata['dataset_id'] = '11z'
        tdata['return_to_dataverse_url'] = 'ha'
        #msg(tdata)
        validation_form = DataverseLayerMetadataValidationForm(tdata)
        #msg('valid: %s' % validation_form.is_valid())
        self.assertEqual(validation_form.is_valid(), False)

        msg('check for attributes in error')
        err_keys = validation_form.errors.keys()
        msg(err_keys)
        self.assertEqual('return_to_dataverse_url' in err_keys, True)
        self.assertEqual('dataset_id' in err_keys, True)

        msg('check for err messages')
        err_msgs = validation_form.errors.values()
        msg(err_msgs)
        self.assertEqual([u'Enter a valid URL.'] in err_msgs, True)
        self.assertEqual([u'Enter a whole number.'] in err_msgs, True)

    def test_form_validation3(self):

        msgt('(3) Does form validate with the Geoconnect GISDataFile object turned to a dict--it has extra fields')

        tdata = self.test_data.copy()
        tdata['gis_scratch_work_directory'] = 'geoconnect/test_setup/gis_scratch_work/2014-0911-1622__1'
        tdata['map_layer'] = 'Another extra field...'


        validation_form = DataverseLayerMetadataValidationForm(tdata)
        validation_form.is_valid()
        msg(validation_form.errors)
        self.assertEqual(validation_form.is_valid(), True)

        dvinfo_obj = validation_form.save(commit=False)
        self.assertEqual(type(dvinfo_obj), DataverseLayerMetadata)
        msg('yes, converts into a DataverseMetadata object (minus the map_layer)')


    #@unittest.skip("testing skipping")
    def test_form_validation4(self):
        msgt('(4) Does the CheckForExistingLayerForm form work?)')

        form_data = dict(dv_user_id=10, datafile_id=1)
        f = CheckForExistingLayerForm(form_data)
        self.assertEqual(f.is_valid(), True)
        msg('Yes valid params')
        self.assertEqual(f.cleaned_data, dict(dv_user_id=10, datafile_id=1))
        msg('cleaned_data is as expected')

        form_data = dict(dv_user_id='99', datafile_id=1)
        f = CheckForExistingLayerForm(form_data)
        self.assertEqual(f.is_valid(), True)

        msg('Yes valid params 2')
        self.assertEqual(f.cleaned_data, dict(dv_user_id=99, datafile_id=1))
        msg('cleaned_data is as expected')

        self.assertEqual(f.get_latest_dataverse_layer_metadata(), None)
        msg('No layers found')

        form_data = dict(dv_user_id='99')
        f = CheckForExistingLayerForm(form_data)
        self.assertEqual(f.is_valid(), False)
        msg('Invalid params')        #get_latest_dataverse_layer_metadata

        self.assertRaises(AssertionError, f.get_latest_dataverse_layer_metadata)
        msg('Attempting to retrieve metadata on invalid form raises assertion error')



class SimpleClientTest(unittest.TestCase):

    def test_view_1(self):
        msgt('(1) get_existing_layer_data: without authentication')
        client = Client()
        response = client.post(reverse('get_existing_layer_data'))
        print ('response.content', response.content)
        self.assertEqual(response.status_code, 401)
        msg('get response gives 401')

        self.assertEqual(response.content, """{"message": "Authentication failed.", "success": false}""")
        msg('check error message')


    def test_view_2(self):
        msgt('(2) get_existing_layer_data: with a get, not a post')
        client = Client()
        response = client.get(reverse('get_existing_layer_data') + '?geoconnect_token=%s' % settings.WORLDMAP_TOKEN_FOR_DATAVERSE)
        self.assertEqual(response.status_code, 401)
        msg('get response gives 401')

        self.assertEqual(response.content, """{"message": "The request must be a POST, not GET", "success": false}""")
        msg('check error message')


    def test_view_3(self):
        msgt('(3) get_existing_layer_data: with a auth and post, but no other data')
        client = Client()

        data = dict(geoconnect_token=settings.WORLDMAP_TOKEN_FOR_DATAVERSE)

        response = client.post(reverse('get_existing_layer_data'), data)
        self.assertEqual(response.status_code, 401)
        msg('get response gives 401')

        self.assertEqual(response.content, """{"message": "The request did not validate.  Expected a 'dv_user_id' and 'datafile_id'", "success": false}""")
        msg('check error message')


    def test_view_4(self):
        msgt('(4) get_existing_layer_data: valid, no existing layers found')
        client = Client()

        data = dict(geoconnect_token=settings.WORLDMAP_TOKEN_FOR_DATAVERSE\
                    , dv_user_id=107\
                    , datafile_id=1\
                    )
        response = client.post(reverse('get_existing_layer_data'), data)
        print (response.status_code, response.content)

        self.assertEqual(response.status_code, 200)
        msg('response gives a 200')

        self.assertEqual(response.content, """{"message": "This layer does not yet exist", "success": false}""")
        msg('check message')





"""

"""
