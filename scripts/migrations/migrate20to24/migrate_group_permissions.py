#!/usr/bin/python
import utils

src = utils.get_src()
dst = utils.get_dst()

src_cur = src.cursor()
dst_cur = dst.cursor()

permissions = utils.get_permissions_dict()

# get anonymous and registered group id
dst_cur.execute("SELECT id FROM auth_group WHERE name = 'anonymous'")
anonymous_group_id = dst_cur.next()[0]
dst_cur.execute("SELECT id FROM auth_group WHERE name = 'authenticated'")
authenticated_group_id = dst_cur.next()[0]

dst_cur.execute('TRUNCATE TABLE guardian_groupobjectpermission;')

sql = """
SELECT object_ct_id, object_id, subject, title FROM security_genericobjectrolemapping rl
JOIN security_objectrole r ON rl.role_id = r.id
WHERE object_id IN (SELECT id FROM base_resourcebase)
"""

src_cur.execute(sql)

for src_row in src_cur:
    # object_ct_id
    object_ct_id = utils.get_content_type_id_by_oldid(src_row[0])
    # object_id
    object_id = utils.get_resourceid_by_oldid(src_row[1])
    # subject
    subject = src_row[2]
    # title
    title = src_row[3]

    # group to which to apply permissions
    group_id = anonymous_group_id
    if subject == 'authenticated':
        group_id = authenticated_group_id

    # permissions to assign
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
    if title == 'Read Only':
        guardian_perms = [
            'view_resourcebase',
            'download_resourcebase',
        ]
    print guardian_perms
    for perm in guardian_perms:
        object_ct_id = utils.get_content_type_id('resourcebase')
        perm_id = permissions[perm]
        if perm in ('change_layer_data', 'change_layer_style'):
            object_ct_id = utils.get_content_type_id('layer')
        print 'Inserting permission %s for group %s for content %s' % (perm, subject, object_id)
        sql_insert = "INSERT INTO guardian_groupobjectpermission (permission_id, content_type_id, object_pk, group_id) VALUES (%s, %s, '%s', %s)" % (perm_id, object_ct_id, object_id, group_id)
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
