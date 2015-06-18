#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()


dst_cur.execute("delete from base_contactrole")
src_cur.execute("select resource_id, contact_id, role_id from base_contactrole where contact_id in (select id from people_profile)")

for src_row in src_cur:
    #resource_id
    old_res_id = src_row[0]
    resource_id = utils.get_resourceid_by_oldid(src_row[0])
    #user_id
    contact_id = utils.get_userid_by_old_profile_id(src_row[1])
    #primary
    role_id = src_row[2]
    if role_id == 1:
        role_name = 'pointOfContact'
    else:
        role_name = 'author'
    try:
        dst_cur.execute("insert into base_contactrole(resource_id, contact_id, role) values (%s, %s, '%s')" % (resource_id, contact_id, role_name))
        dst.commit()
    except Exception as error:
        print 
        print type(error)
        print str(error) + "select id, user_id, \"primary\", avatar, date_uploaded from avatar_avatar"
        print str(src_row)
        dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
