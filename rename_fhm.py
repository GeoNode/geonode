from geonode.settings import GEONODE_APPS
from geonode.cephgeo.models import RIDF
import shutil
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")


def get_province(rb, muni):
    ridf_list = RIDF.objects.filter(riverbasins__name__icontains=rb)
    for ridf in ridf_list:
        if ridf.municipality == muni:
            return ridf.province

    
# path = ''
# walk through each RB folder
# match RB with RB keyword in RIDF model
# if line contains RIDF.municipality and RIDF.keywords(riverbasin), append RIDF.province
# filename will be municipality__province_fh{X}yr_{Y}m

SRC_DIRS = ['/mnt/geostorage/DAD/FLOOD_HAZARD/DREAM/',
            '/mnt/geostorage/DAD/FLOOD_HAZARD/Phil-LiDAR/']
DST_DIR = '/mnt/geostorage/DAD/FLOOD_HAZARD/RenameTest/'
SHP_EXTS = ['.shp', '.prj', '.shx', '.dbf', '.shp.xml']

if __name__ == '__main__':

    for SRC_DIR in SRC_DIRS:
        print 'SRC_DIR:', SRC_DIR
        for root, dirs, files in os.walk(SRC_DIR):
            for f in sorted(files):
                print 'f:', f
                # Get filename and file extension
                src_filename, file_ext = os.path.splitext(f)
                # Check file extension is a shapefile
                if file_ext.lower() == '.shp':
                    print '#' * 40
                    print 'src:', f
                    # Check if all shapefile parts exists
                    src_shps = []
                    for shp_ext in SHP_EXTS:
                        fp = os.path.abspath(os.path.join(root, src_filename +
                                                          shp_ext))
                        if os.path.isfile(fp):
                            src_shps.append(fp)
                        else:
                            print >>sys.stderr,"File doesn't exist:", fp
                            print 'Skipping file!'
                            continue
                    print 'src_shps:', src_shps
                    tokens = src_filename.lower().split('_fh')
                    print 'tokens:', tokens
                    muni = tokens[0]
                    print 'muni:', muni
                    suffix = 'fh' + tokens[1] #'_fh'
                    print 'suffix:', suffix

                    # Get RB
                    year = os.path.dirname(root)
                    print 'year:', year
                    hazard = os.path.dirname(year)
                    print 'hazard:', hazard
                    rb_lower = os.path.basename(os.path.dirname(hazard)).lower().replace('_30m', '')
                    print 'rb_lower:', rb_lower
                    rb = rb_lower[0].upper() + rb_lower[1:]
                    print 'rb:', rb

                    if rb_lower == 'cdo':
                        rb = 'Cagayan_de_Oro'
                    print 'rb:', rb

                    # Get province                    
                    province = get_province(rb, muni)
                    if province is None:
                        print >>sys.stderr, 'Cannot find province! rb:', rb, 'muni:', muni
                        print 'Skipping file!'
                        continue
                    print 'province:', province

                    # Copy src to dst dir
                    dst_filename = muni + '__' + province + '_' + suffix
                    # print 'dst:', dst_filename
                    for src_shp in src_shps:
                        src_fn, src_ext = os.path.splitext(src_shp)
                        print 'src_fn:', src_fn
                        dst_path = os.path.join(DST_DIR, dst_filename + src_ext)
                        print 'dst_path:', dst_path

                        if not os.path.isfile(dst_path):
                            pass
                        # shutil.copyfile(src_fn, dst_path)

                    # exit(1)
                    sys.stdout.flush()
                    sys.stderr.flush()
                # break