from django.test import TestCase

import utils
# Create your tests here.

TEST_EXT_TO_TYPE_DICT = {
	".tif": "orthophoto/DEM",
	".csv":	"csv",
	".dbf": "shapefile",
	".prj": "shapefile",
	".sbn": "shapefile",
	".sbx": "shapefile",
	".shp": "shapefile",
	".shx": "shapefile",
	".kml": "kml"
}

class FileExtensionClassifierTestCase(TestCase):
	### tests if defined mapping dictionaries in utils.py are correct
	def test_ext_to_type_dict(self):
		for x in utils.TYPE_TO_IDENTIFIER_DICT:
			self.assertEqual(utils.TYPE_TO_IDENTIFIER_DICT[x],TEST_EXT_TO_TYPE_DICT[x])
	
	
	### tests if file names with the correct file extensions are mapped to their proper descriptions
	def test_extension_classifier1(self):
		for x in utils.TYPE_TO_IDENTIFIER_DICT:
			result=file_classifier("somestring."+x)
			self.assertEqual(result,TEST_EXT_TO_TYPE_DICT[x])
	
	### tests if file names with the wrong file extensions result to an empty string		
	def test_extension_classifier2(self):
		for x in utils.TYPE_TO_IDENTIFIER_DICT:
			result=file_classifier("somestring."+x+"xyz")
			self.assertEqual(result,'')
	
	### tests if file names without any file extensions result to an empty string
	def test_extension_classifier3(self):
		result=file_classifier("randomstring")
		self.assertEqual(result,'')
	
	### tests function behavior when given an empty string
	def test_extension_classifier4(self):
		result=file_classifier("")
		self.assertEqual(result,'')
		
