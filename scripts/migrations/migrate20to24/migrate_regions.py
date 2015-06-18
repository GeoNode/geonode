#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

regions_dict = utils.get_regions_dict()

src_cur.execute("select resourcebase_id, code from base_resourcebase_regions rr join base_region r on rr.region_id = r.id")

for src_row in src_cur:
    resourcebase_id = utils.get_resourceid_by_oldid(src_row[0])
    if resourcebase_id is not None:
        region_code = src_row[1]
        if region_code in regions_dict:
            try:
                print 'Assigning region %s to resource %s' % (region_code, resourcebase_id)
                dst_cur.execute("INSERT INTO base_resourcebase_regions(resourcebase_id, region_id) values (%s, %s)" % (resourcebase_id, regions_dict[region_code]))
                dst.commit()
            except Exception as error:
                print type(error)
                print str(src_row)
                dst.rollback()
        else:
            print 'In GeoNode 2.4 regions table there is not a region with code %s' % region_code

src_cur.close()
dst_cur.close()
src.close()
dst.close()
