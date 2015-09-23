#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute("select resourcebase_ptr_id, zoom, projection, center_x, center_y, last_modified, popular_count, share_count from maps_map")

for src_row in src_cur:
    assignments = []
    #resourcebase_ptr_id
    id = utils.get_resourceid_by_oldid(src_row[0])
    assignments.append(id)
    #title_en
    title_en = utils.get_en_fields(id)[0]
    assignments.append(title_en)
    #abstract_en
    assignments.append(utils.get_en_fields(id)[1])
    #purpose_en
    assignments.append(utils.get_en_fields(id)[2])
    #constraints_other_en
    assignments.append(utils.get_en_fields(id)[3])
    #supplemental_information_en
    assignments.append(utils.get_en_fields(id)[4])
    #distribution_description_en
    assignments.append(utils.get_en_fields(id)[5])
    #data_quality_statement_en
    assignments.append(utils.get_en_fields(id)[6])
    #zoom
    assignments.append(src_row[1])
    #projection
    assignments.append(src_row[2])
    #center_x
    assignments.append(src_row[3])
    #center_y
    assignments.append(src_row[4])
    #last_modified
    assignments.append(src_row[5])
    #urlsuffix
    assignments.append("unk")
    #featuredurl
    assignments.append("unknown")

    try:
        print 'Migrating map titled %s' % title_en
        dst_cur.execute("insert into maps_map(resourcebase_ptr_id, title_en, abstract_en, purpose_en, constraints_other_en, supplemental_information_en, distribution_description_en, data_quality_statement_en, zoom, projection, center_x, center_y, last_modified, urlsuffix, featuredurl) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print str(error) + "select resourcebase_ptr_id, zoom, projection, center_x, center_y, last_modified, popular_count, share_count from maps_map"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
