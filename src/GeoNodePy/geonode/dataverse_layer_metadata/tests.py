from __future__ import print_function
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import TestCase

from geonode.dataverse_layer_metadata.models import DataverseLayerMetadata
from geonode.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm

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

"""
        from datetime import datetime
        from geonode.dataverse_layer_metadata.forms import DataverseLayerMetadataValidationForm
        DATETIME_PAT_STR = '%Y-%m-%d %H:%M'
        s='2010-09-05 04:00:00+00:00'
        DataverseLayerMetadataValidationForm.format_datafile_create_datetime(s)
"""
