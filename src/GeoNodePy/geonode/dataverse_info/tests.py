from __future__ import print_function
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.test import TestCase
from geonode.dataverse_info.models import DataverseInfo
from geonode.dataverse_info.forms import DataverseInfoValidationForm

def msg(m): print(m)
def dashes(): msg('-' * 40)
def msgt(m): dashes(); msg(m); dashes()

class ValidationFormTest(TestCase):
    
    def setUp(self):
        self.test_data = dict(dv_username='bari_user'\
                    , dv_user_email='bari@bari.org'\
                    , return_to_dataverse_url=''\
                    , dataverse_name='BARI'\
                    , dataverse_description='boston area research initiative'\
                    , doi='FHG/134'\
                    , dataset_id=77\
                    , dataset_version_id='1.2'\
                    , dataset_name='Massachusetts Commuting'\
                    , dataset_description='Transportation to work based on census tracts'\
                    , datafile_label='commute_ma.zip'\
                    , datafile_description='Zipped Shapefile'\
                    )
    
    def test_form_validation1(self):
    
        msgt('(1) Test valid data')
        
        validation_form = DataverseInfoValidationForm(self.test_data)
        #print 'valid',validation_form.is_valid()
        self.assertEqual(validation_form.is_valid(), True)

    def test_form_validation2(self):

        msgt('(2) Test invalid data')

        tdata = self.test_data.copy()
        tdata['dataset_id'] = '11z'
        tdata['return_to_dataverse_url'] = 'ha'
        #msg(tdata)
        validation_form = DataverseInfoValidationForm(tdata)
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
        
        msgt('(3) Does form validates with the geoconnect object GISDataFile turned to a dict--it has extra fields')
        tdata = dict(datafile_expected_md5_checksum=''
           , datafile_type=''
           , gis_scratch_work_directory='geoconnect/test_setup/gis_scratch_work/2014-0911-1622__1'
           , datafile_label='boston_commute.zip'
           , dv_user_email='rp@harvard.edu'
           , dv_username='rp'
           , md5='698d51a19d8a121ce581499d7b701668'
           , dv_id='-1'
           , dataset_description='Files related to moving in the Boston, as well as MA area'
           , datafile_id='1'
           , dv_user_id='1'
           , dataset_version_id='-1'
           , dataverse_name='BARI Dataverse'
           , datafile_description='shapefile of MA commuting data'
           , dataset_id='-1'
           , dv_file='dv_files/2014/09/7/social_disorder_in_boston.zip'
           , dv_session_token=''
           , id='1'
           , dataset_name='Boston Transportation'
           , return_to_dataverse_url='http://dataverse.org/dataset.xhtml?id=124'
        ) 
        
        validation_form = DataverseInfoValidationForm(tdata)
        validation_form.is_valid()
        msg(validation_form.errors)
        self.assertEqual(validation_form.is_valid(), True)
        
        dvinfo_obj = validation_form.save(commit=False)
        self.assertEqual(type(dvinfo_obj), DataverseInfo)
        msg('yes, converts into a DataverseInfo object (minus the map_layer)')
        