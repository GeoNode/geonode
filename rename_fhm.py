from geonode.settings import GEONODE_APPS
from geonode.cephgeo.models import RIDF
import shutil
import os
import sys
import errno

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

SRC_DIRS = ['/mnt/geostorage/DAD/FLOOD_HAZARD/DREAM',
            '/mnt/geostorage/DAD/FLOOD_HAZARD/Phil-LiDAR']
DST_BASE = '/mnt/geostorage/DAD/FLOOD_HAZARD/Renamed'
SHP_EXTS = ['.shp', '.prj', '.shx', '.dbf', '.shp.xml']


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

if __name__ == '__main__':

    isexit = False

    print 'src_path,dst_path,status'

    for SRC_DIR in SRC_DIRS:

        for root, dirs, files in os.walk(SRC_DIR):
            for f in sorted(files):

                # Get filename and file extension
                src_filename, file_ext = os.path.splitext(f)

                # Check file extension is a shapefile
                if file_ext.lower() == '.shp':

                    # Check if all shapefile parts exists
                    src_shps = []
                    for shp_ext in SHP_EXTS:
                        fp = os.path.abspath(os.path.join(root, src_filename +
                                                          shp_ext))
                        if os.path.isfile(fp):
                            src_shps.append(fp)
                        else:
                            print >>sys.stderr, "File doesn't exist:", fp
                            print fp + ",,File doesn't exist! Skipping file"
                            # exit(1)
                            continue

                    # Check if filename already contains double underscores
                    # If it has double underscores, split it up
                    if not '__' in src_filename:
                        tokens = src_filename.lower().split('_fh')
                        muni = tokens[0]
                        suffix = 'fh' + tokens[1]  # '_fh'

                        # Get RB
                        year = os.path.dirname(root)
                        hazard = os.path.dirname(year)
                        rb = os.path.basename(os.path.dirname(
                            hazard)).lower().replace('_30m', '').replace(' ', '_')
                        # Convert to titlecase
                        # rb = rb_lower[0].upper() + rb_lower[1:]

                        # Special cases
                        if rb == 'cdo':
                            rb = 'cagayan_de_oro'

                        # Get province
                        province = get_province(rb, muni)
                        if province is None:
                            print >>sys.stderr, 'Cannot find province! rb:', rb, 'muni:', muni
                            print os.path.join(root, f) + ",,Can't find province! rb: " + rb + ' muni: ' + muni
                            # exit(1)
                            continue

                    else:
                        tokens = src_filename.lower().split('__')
                        muni = tokens[0]
                        tokens2 = tokens[1].split('_fh')
                        province = tokens2[0]
                        suffix = tokens2[1]
                        # isexit = True

                    # Copy src to dst dir
                    dst_filename = 'muni_' + muni + '_prov_' + province + '_' + suffix

                    # Copy shapefiles for src dir to dst
                    for src_shp in src_shps:
                        # src_fn, src_ext = os.path.splitext(src_shp)
                        src_fn = src_shp[:src_shp.find('.')]
                        src_ext = src_shp[src_shp.find('.'):]

                        # print 'os.path.dirname(SRC_DIR):', os.path.dirname(SRC_DIR)
                        # print 'os.path.dirname(src_shp):', os.path.dirname(src_shp)

                        dst_dir = os.path.dirname(src_shp).replace(
                            os.path.dirname(SRC_DIR), DST_BASE)

                        dst_path = os.path.join(
                            dst_dir, dst_filename + src_ext)

                        if src_filename == dst_filename:
                            print src_shp + ',' + dst_path + ',Copied'
                        else:
                            print src_shp + ',' + dst_path + ',Renamed&Copied'

                        if not os.path.isfile(dst_path):
                            # Create dst dir
                            mkdir_p(dst_dir)

                            # Copy file
                            shutil.copyfile(src_shp, dst_path)

                            # pass

                    sys.stdout.flush()
                    sys.stderr.flush()

                    # exit(1)

                    if isexit:
                        exit(1)
