#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute("select resourcebase_ptr_id, workspace, store, \"storeType\", name, typename, popular_count, share_count from layers_layer")

for src_row in src_cur:
    assignments = []
    #resourcebase_ptr_id
    id = utils.get_resourceid_by_oldid(src_row[0])
    assignments.append(id)
    # _en fields
    en_fields = utils.get_en_fields(id)
    #title_en
    assignments.append(en_fields[0])
    #abstract_en
    assignments.append(en_fields[1])
    #purpose_en
    assignments.append(en_fields[2])
    #constraints_other_en
    assignments.append(en_fields[3])
    #supplemental_information_en
    assignments.append(en_fields[4])
    #distribution_description_en
    assignments.append(en_fields[5])
    #data_quality_statement_en
    assignments.append(en_fields[6])
    #workspace
    assignments.append(src_row[1])
    #store
    assignments.append(src_row[2])
    #storeType
    assignments.append(src_row[3])
    #name
    assignments.append(src_row[4])
    #typename
    assignments.append(src_row[5])
    #charset
    assignments.append("UTF8")
    #upload_session_id
    assignments.append(None)
    #service_id
    assignments.append(None)

    try:
        dst_cur.execute("insert into layers_layer(resourcebase_ptr_id, title_en, abstract_en, purpose_en, constraints_other_en, supplemental_information_en, distribution_description_en, data_quality_statement_en, workspace, store, \"storeType\", name, typename, charset, upload_session_id, service_id) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print 
        print type(error)
        print str(error) + "select resourcebase_ptr_id, workspace, store, \"storeType\", name, typename, popular_count, share_count, default_style_id from layers_layer"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
