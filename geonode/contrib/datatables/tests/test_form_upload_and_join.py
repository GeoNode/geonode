from os.path import dirname, join, realpath
from django.utils import unittest
from geonode.contrib.datatables.forms import TableUploadAndJoinRequestForm
from django.core.files.uploadedfile import SimpleUploadedFile

class TableUploadAndJoinFormTestCase(unittest.TestCase):
    def setUp(self):
        pass
        #self.lion = Animal.objects.create(name="lion", sound="roar")
        #self.cat = Animal.objects.create(name="cat", sound="meow")

    def test_no_params(self):
        d = {}
        f = TableUploadAndJoinRequestForm(d)
        self.assertEqual(f.is_valid(), False)

    def test_years(self):

        d = dict(title="Boston Income for 2000",
                 abstract="Dataset from sources x, y, z",
                 delimiter='\t',
                 uploaded_file=None,
                 table_attribute='census_tract',
                 layer_name='Census 2000',
                 layer_attribute='CTract')


        # ------------------------------------------
        # Validate form WITHOUT the uploaded file
        # ------------------------------------------
        f = TableUploadAndJoinRequestForm(d)

        self.assertEqual(f.is_valid(), False)
        self.assertEqual(f.errors.has_key('uploaded_file'), True)
        self.assertEqual(f.errors.get('uploaded_file'), ["This field is required."])

        # ------------------------------------------
        # Validate form with the file
        # ------------------------------------------
        upload_file = open(join(dirname(realpath(__file__)), 'input', 'test_upload.txt'), 'rb')
        file_dict = {'uploaded_file': SimpleUploadedFile(upload_file.name, upload_file.read())}
        f = TableUploadAndJoinRequestForm(d, file_dict)
        self.assertEqual(f.is_valid(), True)

        d.pop('delimiter')
        f = TableUploadAndJoinRequestForm(d, file_dict)
        self.assertEqual(f.is_valid(), False)
        #print f.errors
        self.assertEqual(f.errors.has_key('delimiter'), True)
        self.assertEqual(f.errors.get('delimiter'), ["This field is required."])
