from operator import itemgetter, attrgetter

### For additional functions/definitions which may be needed by views

### Sample Ceph object entry:{'hash': '524f26771b90ccea598448b8b7a263b7', 
### 					'name': 'JE3409_ortho.tif', 'bytes': 17299767, 
###						'last_modified': '2015-02-24T07:23:11.000Z', 'content_type': 'image/tiff', 'type': 'Orthophoto'}

### A mapping of file types to their associated file extensions

#EXT_TO_TYPE_DICT = {
#	".tif": "orthophoto/DEM",
#	".csv":	"csv",
#	".dbf": "shapefile",
#	".prj": "shapefile",
#	".sbn": "shapefile",
#	".sbx": "shapefile",
#	".shx": "shapefile",
#	".kml": "kml",
#	".laz": "laz"

#TYPE_TO_IDENTIFIER_DICT = {
#	"DEM-DTM"		: ["_DTM"],
#	"DEM-DSM"		: ["_DSM"],
#	"Orthophoto"	: ["_ortho"],
#}
SORT_TYPES = [ "name", "type", "uploaddate"]

TYPE_TO_IDENTIFIER_DICT = {
	".laz"			: "LAZ file",
	"_dem.tif" 		: "DEM TIF",
	"_ortho.tif"	: "Orthophoto" 
}


#### returns classification of the file based on file extension
#### if no matches, result is an empty string
def file_classifier(file_name):
	
	ext_classification = ''
	for x in TYPE_TO_IDENTIFIER_DICT:
		if len(file_name) > len(TYPE_TO_IDENTIFIER_DICT[x]):
			if file_name.lower().endswith(x):
				ext_classification = TYPE_TO_IDENTIFIER_DICT[x]
		
	return ext_classification

def sort_by(sort_key, object_list, descending=False):
	if descending:
		return sorted(object_list, 	key=itemgetter(sort_key), reverse=True)
	else:
		return sorted(object_list, 	key=itemgetter(sort_key))

#def file_feature_classifier(file_name):
#	pass
