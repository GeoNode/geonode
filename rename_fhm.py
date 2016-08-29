from geonode.settings import GEONODE_APPS
from geonode.cephgeo.models import RIDF
import shutil

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def get_province(rb, muni):
    ridf_list = RIDF.objects.filter(keywords__name__icontains=rb)
    for ridf in ridf_list:
        if ridf.municipality == muni:
            return ridf.province

    
# path = ''
# walk through each RB folder
# match RB with RB keyword in RIDF model
# if line contains RIDF.municipality and RIDF.keywords(riverbasin), append RIDF.province
# filename will be municipality__province_fh{X}yr_{Y}m

SRC_DIRS = ['/mnt/geostorage/DAD/FLOOD_HAZARD/Phil-LiDAR/',
            '/mnt/geostorage/DAD/FLOOD_HAZARD/DREAM/']
DST_DIR = '/mnt/geostorage/DAD/FLOOD_HAZARD/RenameTest/'
SHP_EXTS = ['.shp', '.prj', '.shx', '.dbf', '.shp.xml']

if __name__ == '__main__':

    for SRC_DIR in SRC_DIRS:
        for root, dirs, files in os.walk(SRC_DIR):
            for f in sorted(files):
                # Get filename and file extension
                src_filename, file_ext = os.path.splitext(f).lower()
                # Check file extension is a shapefile
                if file_ext == '.shp':
                    print 'src:', f
                    # Check if all shapefile parts exists
                    src_shps = []
                    for shp_ext in SHP_EXTS:
                        fp = os.path.abspath(os.path.join(root, src_filename +
                                                          shp_ext))
                        if os.path.isfile(fp):
                            src_shps.append(fp)
                        else:
                            print "File doesn't exist:", fp
                            print 'Skipping file!'
                            continue
                    tokens = src_filename.split('_')
                    muni = tokens[0].lower()
                    suffix = '_'.join(tokens[1:]).lower()

                    # Get RB
                    year = os.path.dirname(root)
                    hazard = os.path.dirname(year)
                    rb = os.path.dirname(hazard).lower().replace('_30m', '')

                    # Get province                    
                    province = get_province(rb, muni)
                    if province is None:
                        print 'Cannot find province! rb:', rb, 'muni:', muni
                        print 'Skipping file!'
                        continue

                    # Copy src to dst dir
                    dst_filename = muni + '_' + province + '_' + suffix
                    # print 'dst:', dst_filename
                    for src_shp in src_shps:
                        src_fn, src_ext = os.path.splitext(src_shp)

                        dst_path = os.path.join(DST_DIR, dst_filename + src_ext)
                        print 'dst_path:', dst_path

                        # shutil.copyfile(src_fn, dst_path)
