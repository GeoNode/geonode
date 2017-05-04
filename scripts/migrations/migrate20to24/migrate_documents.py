#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute("select resourcebase_ptr_id, content_type_id, object_id, doc_file, extension, popular_count, share_count from documents_document")

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
    #object_id, content_type_id
    if src_row[2] is not None:
        object_id = utils.get_resourceid_by_oldid(src_row[2])
        content_type_id = utils.get_content_type_id_by_oldid(src_row[1])
    else:
        object_id = None
        content_type_id = None
    assignments.append(object_id)
    assignments.append(content_type_id)
    #doc_file
    assignments.append(src_row[3])
    #extension
    assignments.append(src_row[4])
    #doc_type
    assignments.append(None)
    #doc_url
    assignments.append(None)

    try:
        print 'Migrating document titled %s' % title_en
        dst_cur.execute("insert into documents_document(resourcebase_ptr_id, title_en, abstract_en, purpose_en, constraints_other_en, supplemental_information_en, distribution_description_en, data_quality_statement_en, content_type_id, object_id, doc_file, extension, doc_type, doc_url) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print 
        print type(error)
        print str(error) + "select resourcebase_ptr_id, content_type_id, object_id, doc_file, extension, popular_count, share_count from documents_document"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
