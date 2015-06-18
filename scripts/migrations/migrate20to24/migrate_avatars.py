#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

src_cur.execute("select id, user_id, \"primary\", avatar, date_uploaded from avatar_avatar")

for src_row in src_cur:
    assignments = []
    #id
    assignments.append(src_row[0])
    #user_id
    assignments.append(utils.get_userid_by_oldid(src_row[1]))
    #primary
    assignments.append(src_row[2])
    #avatar
    assignments.append(src_row[3])
    #date_uploaded
    assignments.append(src_row[4])

    try:
        dst_cur.execute("insert into avatar_avatar(id, user_id, \"primary\", avatar, date_uploaded) values (%s, %s, %s, %s, %s)", assignments)
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
