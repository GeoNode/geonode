#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

permissions = utils.get_permissions_dict()

sql = """
select user_id, object_ct_id, object_id, title, username from security_userobjectrolemapping uor
join security_objectrole r on uor.role_id = r.id
join auth_user u on uor.user_id = u.id
"""

src_cur.execute(sql)

for src_row in src_cur:
    print src_row
    #user_id
    user_id = utils.get_userid_by_oldid(src_row[0])
    #object_ct_id
    object_ct_id = utils.get_content_type_id_by_oldid(src_row[1])
    #object_id
    object_id = utils.get_resourceid_by_oldid(src_row[2])
    #title
    title = src_row[3]
    # username
    username= src_row[4]
    guardian_perms = []
    if title == 'Read/Write':
        guardian_perms = [
            'view_resourcebase',
            'download_resourcebase',
            'change_resourcebase_metadata',
        ]
        if utils.get_content_type_id('layer') == object_ct_id:
            guardian_perms = guardian_perms + [
                'change_layer_data',
                'change_layer_style',
            ]
    if title == 'Administrative':
        guardian_perms = guardian_perms + [
            'change_resourcebase',
            'delete_resourcebase',
            'change_resourcebase_permissions',
            'publish_resourcebase',
        ]
    print guardian_perms
    for perm in guardian_perms:
        object_ct_id = utils.get_content_type_id('resourcebase')
        perm_id = permissions[perm]
        if perm in ('change_layer_data', 'change_layer_style'):
            object_ct_id = utils.get_content_type_id('layer')
        print 'Inserting permission %s for user %s for content %s' % (perm, username, object_id)
        sql_insert = "INSERT INTO guardian_userobjectpermission (permission_id, content_type_id, object_pk, user_id) VALUES (%s, %s, '%s', %s)" % (perm_id, object_ct_id, object_id, user_id)
        print sql_insert
        try:
            dst_cur.execute(sql_insert)
            dst.commit()
        except Exception as error:
            print 
            print type(error)
            print str(error) + "select id, user_id, timezone, language from account_account"
            print str(src_row)
            dst.rollback()

src_cur.close()
dst_cur.close()
src.close()
dst.close()
