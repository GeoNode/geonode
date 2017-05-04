#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

# 1. taggit_tag

src_cur.execute("select name, slug from taggit_tag")

for src_row in src_cur:
    assignments = []
    #name
    assignments.append(src_row[0])
    #slug
    assignments.append(src_row[1])

    try:
        dst_cur.execute("insert into taggit_tag(name, slug) values (%s, %s)", assignments)
        dst.commit()
    except Exception as error:
        print type(error)
        print str(error)
        print str(src_row)
        dst.rollback()

# 2. taggit_taggeditem

src_cur.execute("select slug, object_id, content_type_id from taggit_taggeditem tt join taggit_tag t on tt.tag_id = t.id")

for src_row in src_cur:
    assignments = []
    object_id = utils.get_resourceid_by_oldid(src_row[1])
    if object_id is not None:
        #tag_id
        assignments.append(utils.get_tag_id(src_row[0]))
        #object_id
        assignments.append(object_id)
        #content_type_id
        assignments.append(utils.get_content_type_id_by_oldid(src_row[2]))

        try:
            dst_cur.execute("insert into taggit_taggeditem(tag_id, object_id, content_type_id) values (%s, %s, %s)", assignments)
            dst.commit()
        except Exception as error:
            print 
            print type(error)
            print str(error) + "select tag_id, object_id, content_type_id from taggit_taggeditem"
            print str(src_row)
            dst.rollback()
            
src_cur.close()
dst_cur.close()
src.close()
dst.close()
