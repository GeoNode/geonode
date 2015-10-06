import psycopg2
import ConfigParser, os

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gn_migration.cfg'))

gn20_dbname = config.get('db20', 'dbname')
gn20_host = config.get('db20', 'host')
gn20_user = config.get('db20', 'user')
gn20_password = config.get('db20', 'password')

gn24_dbname = config.get('db24', 'dbname')
gn24_host = config.get('db24', 'host')
gn24_user = config.get('db24', 'user')
gn24_password = config.get('db24', 'password')


def get_src():
    """Get input db conn (GeoNode 2.0)"""
    conn = psycopg2.connect(
        "dbname='%s' user='%s' port='5432' host='%s' password='%s'" % (gn20_dbname, gn20_user, gn20_host, gn20_password)
    )
    return conn


def get_dst():
    """Get output db conn (GeoNode 2.4)"""
    conn = psycopg2.connect(
        "dbname='%s' user='%s' port='5432' host='%s' password='%s'" % (gn24_dbname, gn24_user, gn24_host, gn24_password)
    )
    return conn


def get_userid_by_oldid(id):
    """Get an username id by old id"""
    print 'Getting new user id for user id %s' % id
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()
    src_cur.execute('SELECT username FROM auth_user WHERE id = %s;' % id)
    username = src_cur.next()[0]
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM people_profile WHERE username = '%s';" % username)
    new_id = dst_cur.next()[0]
    print 'Id for user %s was %s and is now %s' % (username, id, new_id)
    return new_id


def get_userid_by_old_profile_id(id):
    """Get an username id by old profile id"""
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()

    src_cur.execute('SELECT username FROM people_profile p JOIN auth_user u on p.user_id = u.id WHERE p.id = %s;' % id)
    username = src_cur.next()[0]
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM people_profile WHERE username = '%s';" % username)
    new_id = dst_cur.next()[0]
    print 'Id for user %s is now %s' % (username, new_id)
    return new_id


def get_resourceid_by_oldid(id):
    """Get an resource id by old id"""
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()
    src_cur.execute('SELECT uuid, title FROM base_resourcebase WHERE id = %s;' % id)
    if src_cur.rowcount == 0:
        return None
    src_row = src_cur.next()
    uuid = src_row[0]
    title = src_row[1]
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM base_resourcebase WHERE uuid = '%s';" % uuid)
    if dst_cur.rowcount == 0:
        return None
    new_id = dst_cur.next()[0]
    print 'Resource id %s (%s) is now %s' % (id, title, new_id)
    return new_id


def get_categoryid_by_oldid(id):
    """Get a category id by old id"""
    if id is None:
        return None
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()
    src_cur.execute('SELECT identifier FROM base_topiccategory WHERE id=%s;' % id)
    identifier = src_cur.next()[0]
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM base_topiccategory WHERE identifier = '%s';" % identifier)
    if dst_cur.rowcount == 0:
        print 'Error! There is not this identifier in geonode 2.4 database'
        return None
    new_id = dst_cur.next()[0]
    print 'Category id %s is now %s' % (id, new_id)
    return new_id


def get_spatrepid_by_oldid(id):
    """Get a spatial representation id by old id"""
    if id is None:
        return None
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()
    src_cur.execute('SELECT identifier FROM base_spatialrepresentationtype WHERE id=%s;' % id)
    identifier = src_cur.next()[0]
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM base_spatialrepresentationtype WHERE identifier = '%s';" % identifier)
    if dst_cur.rowcount == 0:
        print 'Error! There is not this identifier in geonode 2.4 database'
        return None
    new_id = dst_cur.next()[0]
    print 'Spatial representation id %s is now %s' % (id, new_id)
    return new_id


def get_content_type_id_by_oldid(id):
    """Get content_type_id by old id"""
    src = get_src()
    dst = get_dst()
    src_cur = src.cursor()
    src_cur.execute('select app_label, model from django_content_type where id = %s;' % id)
    if src_cur.rowcount == 0:
        return None
    row = src_cur.next()
    app_label = row[0]
    model = row[1]
    dst_cur = dst.cursor()
    dst_cur.execute("select id from django_content_type where app_label = '%s' and model = '%s'" % (app_label, model))
    if dst_cur.rowcount == 0:
        return None
    new_id = dst_cur.next()[0]
    print 'Content type id %s is now %s' % (id, new_id)
    return new_id


def get_tag_id(slug):
    """Get tag id from tag slug"""
    dst = get_dst()
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM taggit_tag WHERE slug = '%s';" % slug)
    if dst_cur.rowcount == 0:
        return None
    id = dst_cur.next()[0]
    print 'Tag id for %s is %s' % (slug, id)
    return id


def get_content_type_id(model):
    """Get content type id from model's name"""
    dst = get_dst()
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT id FROM django_content_type WHERE model = '%s';" % model)
    id = dst_cur.next()[0]
    print 'Content type id for %s is %s' % (model, id)
    return id


def get_en_fields(id):
    """Get values for *_en fields"""
    dst = get_dst()
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT title, abstract, purpose, constraints_other, supplemental_information, distribution_description, data_quality_statement FROM base_resourcebase WHERE id = %s" % id)
    en_fields = dst_cur.next()
    return en_fields


def get_permissions_dict():
    """Dict to get auth permission id from code name"""
    dst = get_dst()
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT codename, id FROM auth_permission;")
    permissions_dict = {}
    for row in dst_cur.fetchall():
        permissions_dict[row[0]] = row[1]
    return permissions_dict


def get_regions_dict():
    """Dict to get regions id from code"""
    dst = get_dst()
    dst_cur = dst.cursor()
    dst_cur.execute("SELECT code, id FROM base_region;")
    regions_dict = {}
    for row in dst_cur.fetchall():
        regions_dict[row[0]] = row[1]
    return regions_dict


def get_attributes_by_uuid(uuid, model):
    """Get attributes from layers/documents/maps for a given uuid"""
    src = get_src()
    src_cur = src.cursor()
    model_table = ''
    if model == 'layer':
        model_table = 'layers_layer'
    if model == 'map':
        model_table = 'maps_map'
    if model == 'document':
        model_table = 'documents_document'
    src_cur.execute("select popular_count, share_count from base_resourcebase rb join %s m on rb.id = m.resourcebase_ptr_id where uuid = '%s'" % (model_table, uuid))
    attributes = src_cur.next()
    return attributes
