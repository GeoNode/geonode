#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute('select map_id, stack_order, format, name, opacity, styles, transparent, fixed, "group", visibility, ows_url, layer_params, source_params, local from maps_maplayer')

for src_row in src_cur:
    assignments = []
    #map_id
    id = utils.get_resourceid_by_oldid(src_row[0])
    assignments.append(id)
    #stack_order
    assignments.append(src_row[1])
    #format
    assignments.append(src_row[2])
    #name
    name = src_row[3]
    assignments.append(name)
    #opacity
    assignments.append(src_row[4])
    #styles
    assignments.append(src_row[5])
    #transparent
    assignments.append(src_row[6])
    #fixed
    assignments.append(src_row[7])
    #group
    assignments.append(src_row[8])
    #visibility
    assignments.append(src_row[9])
    #ows_url
    assignments.append(src_row[10])
    #layer_params
    assignments.append(src_row[11])
    #source_params
    assignments.append(src_row[12])
    #local
    assignments.append(src_row[13])

    try:
        print 'Migrating map layer named %s' % name
        dst_cur.execute("insert into maps_maplayer(map_id, stack_order, format, name, opacity, styles, transparent, fixed, \"group\", visibility, ows_url, layer_params, source_params, local) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print 
        print type(error)
        print str(error) + "select map_id, stack_order, format, name, opacity, styles, transparent, fixed, \"group\", visibility, ows_url, layer_params, source_params, local from maps_maplayer"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()

