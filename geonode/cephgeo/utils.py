from operator import itemgetter, attrgetter
import re

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
SORT_TYPES = [ "name", "type", "uploaddate", "nosort"]


TYPE_TO_IDENTIFIER_DICT = {
	".laz"			: "LAZ file",
	"_dem.tif" 		: "DEM TIF",
	"_dsm.tif" 		: "DSM TIF",
	"_ortho.tif"	: "Orthophoto",
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

def is_valid_grid_ref_old(grid_ref_string):
    ptn = re.compile('^[a-zA-Z]{2}[0-9]{4}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False

def is_valid_grid_ref_range(grid_ref_string):
    ptn = re.compile('^[a-zA-Z]{2}[0-9]{4}\-[a-zA-Z ]{2}[0-9]{4}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False

def is_valid_grid_ref(grid_ref_string):
    # E648N803_DSM
    ptn = re.compile('^[a-zA-Z]{1}[0-9]{3}[a-zA-Z]{1}[0-9]{3}$')
    if ptn.match(grid_ref_string) is not None:
        return True
    else:
        return False




def ceph_object_ids_by_geotype(ceph_obj_list):
    obj_name_dict = dict()
    for obj in ceph_obj_list:
        if obj.geo_type in obj_name_dict:
            obj_name_dict[obj.geo_type.encode('utf8')].append(obj.name.encode('utf8'))
        else:
            obj_name_dict[obj.geo_type.encode('utf8')] = [obj.name.encode('utf8'),]
        
    return obj_name_dict
