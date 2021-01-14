# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models


class AccountEmailaddress(models.Model):
    email = models.CharField(unique=True, max_length=254)
    verified = models.BooleanField()
    primary = models.BooleanField()
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class ActstreamAction(models.Model):
    actor_object_id = models.CharField(max_length=255)
    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    action_object_object_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField()
    public = models.BooleanField()
    data = models.TextField(blank=True, null=True)
    action_object_content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    actor_content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    target_content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'actstream_action'


class ActstreamFollow(models.Model):
    object_id = models.CharField(max_length=255)
    actor_only = models.BooleanField()
    started = models.DateTimeField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)
    flag = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'actstream_follow'
        unique_together = (('user', 'content_type', 'object_id', 'flag'),)


class AnnouncementsAnnouncement(models.Model):
    title = models.CharField(max_length=50)
    level = models.IntegerField()
    content = models.TextField()
    creation_date = models.DateTimeField()
    site_wide = models.BooleanField()
    members_only = models.BooleanField()
    dismissal_type = models.IntegerField()
    publish_start = models.DateTimeField()
    publish_end = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'announcements_announcement'


class AnnouncementsDismissal(models.Model):
    dismissed_at = models.DateTimeField()
    announcement = models.ForeignKey(AnnouncementsAnnouncement, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'announcements_dismissal'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AvatarAvatar(models.Model):
    primary = models.BooleanField()
    avatar = models.CharField(max_length=1024)
    date_uploaded = models.DateTimeField()
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'avatar_avatar'


class BaseConfiguration(models.Model):
    read_only = models.BooleanField()
    maintenance = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'base_configuration'


class BaseContactrole(models.Model):
    role = models.CharField(max_length=255)
    contact = models.ForeignKey('PeopleProfile', models.DO_NOTHING)
    resource = models.ForeignKey('BaseResourcebase', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_contactrole'
        unique_together = (('contact', 'resource', 'role'),)


class BaseCuratedthumbnail(models.Model):
    img = models.CharField(max_length=100)
    resource = models.ForeignKey('BaseResourcebase', models.DO_NOTHING, unique=True)

    class Meta:
        managed = False
        db_table = 'base_curatedthumbnail'


class BaseGroupgeolimit(models.Model):
    wkt = models.TextField()
    group = models.ForeignKey('GroupsGroupprofile', models.DO_NOTHING)
    resource = models.ForeignKey('BaseResourcebase', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_groupgeolimit'


class BaseHierarchicalkeyword(models.Model):
    name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=100)
    path = models.CharField(unique=True, max_length=255)
    depth = models.IntegerField()
    numchild = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'base_hierarchicalkeyword'


class BaseLicense(models.Model):
    identifier = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    abbreviation = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    description_en = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=2000, blank=True, null=True)
    license_text = models.TextField(blank=True, null=True)
    license_text_en = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'base_license'


class BaseLink(models.Model):
    extension = models.CharField(max_length=255)
    link_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    mime = models.CharField(max_length=255)
    url = models.TextField()
    resource = models.ForeignKey('BaseResourcebase', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'base_link'


class BaseMenu(models.Model):
    title = models.CharField(max_length=255)
    order = models.IntegerField()
    placeholder = models.ForeignKey('BaseMenuplaceholder', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_menu'
        unique_together = (('placeholder', 'order'), ('placeholder', 'title'),)


class BaseMenuitem(models.Model):
    title = models.CharField(max_length=255)
    order = models.IntegerField()
    blank_target = models.BooleanField()
    url = models.CharField(max_length=2000)
    menu = models.ForeignKey(BaseMenu, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_menuitem'
        unique_together = (('menu', 'title'), ('menu', 'order'),)


class BaseMenuplaceholder(models.Model):
    name = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'base_menuplaceholder'


class BaseRegion(models.Model):
    code = models.CharField(unique=True, max_length=50)
    name = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, null=True)
    lft = models.IntegerField()
    rght = models.IntegerField()
    tree_id = models.IntegerField()
    level = models.IntegerField()
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    bbox_x0 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_x1 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_y0 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    bbox_y1 = models.DecimalField(max_digits=30, decimal_places=15, blank=True, null=True)
    srid = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'base_region'


class BaseResourcebase(models.Model):
    uuid = models.CharField(max_length=36)
    title = models.CharField(max_length=255)
    date = models.DateTimeField()
    date_type = models.CharField(max_length=255)
    edition = models.CharField(max_length=255, blank=True, null=True)
    abstract = models.TextField()
    purpose = models.TextField(blank=True, null=True)
    maintenance_frequency = models.CharField(max_length=255, blank=True, null=True)
    constraints_other = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=3)
    temporal_extent_start = models.DateTimeField(blank=True, null=True)
    temporal_extent_end = models.DateTimeField(blank=True, null=True)
    supplemental_information = models.TextField()
    data_quality_statement = models.TextField(blank=True, null=True)
    srid = models.CharField(max_length=30)
    csw_typename = models.CharField(max_length=32)
    csw_schema = models.CharField(max_length=64)
    csw_mdsource = models.CharField(max_length=256)
    csw_insert_date = models.DateTimeField(blank=True, null=True)
    csw_type = models.CharField(max_length=32)
    csw_anytext = models.TextField(blank=True, null=True)
    csw_wkt_geometry = models.TextField()
    metadata_uploaded = models.BooleanField()
    metadata_xml = models.TextField(blank=True, null=True)
    popular_count = models.IntegerField()
    share_count = models.IntegerField()
    featured = models.BooleanField()
    is_published = models.BooleanField()
    thumbnail_url = models.TextField(blank=True, null=True)
    detail_url = models.CharField(max_length=255, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey('BaseTopiccategory', models.DO_NOTHING, blank=True, null=True)
    license = models.ForeignKey(BaseLicense, models.DO_NOTHING, blank=True, null=True)
    owner = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)
    polymorphic_ctype = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    restriction_code_type = models.ForeignKey('BaseRestrictioncodetype', models.DO_NOTHING, blank=True, null=True)
    spatial_representation_type = models.ForeignKey('BaseSpatialrepresentationtype', models.DO_NOTHING, blank=True, null=True)
    metadata_uploaded_preserve = models.BooleanField()
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING, blank=True, null=True)
    alternate = models.CharField(max_length=128, blank=True, null=True)
    is_approved = models.BooleanField()
    dirty_state = models.BooleanField()
    last_updated = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)
    doi = models.CharField(max_length=255, blank=True, null=True)
    bbox_polygon = models.PolygonField(blank=True, null=True)
    attribution = models.CharField(max_length=2048, blank=True, null=True)
    resource_type = models.CharField(max_length=1024, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'base_resourcebase'


class BaseResourcebaseGroupsGeolimits(models.Model):
    resourcebase = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    groupgeolimit = models.ForeignKey(BaseGroupgeolimit, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_resourcebase_groups_geolimits'
        unique_together = (('resourcebase', 'groupgeolimit'),)


class BaseResourcebaseRegions(models.Model):
    resourcebase = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    region = models.ForeignKey(BaseRegion, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_resourcebase_regions'
        unique_together = (('resourcebase', 'region'),)


class BaseResourcebaseTkeywords(models.Model):
    resourcebase = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    thesauruskeyword = models.ForeignKey('BaseThesauruskeyword', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_resourcebase_tkeywords'
        unique_together = (('resourcebase', 'thesauruskeyword'),)


class BaseResourcebaseUsersGeolimits(models.Model):
    resourcebase = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    usergeolimit = models.ForeignKey('BaseUsergeolimit', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_resourcebase_users_geolimits'
        unique_together = (('resourcebase', 'usergeolimit'),)


class BaseRestrictioncodetype(models.Model):
    identifier = models.CharField(max_length=255)
    description = models.TextField()
    description_en = models.TextField(blank=True, null=True)
    gn_description = models.TextField()
    gn_description_en = models.TextField(blank=True, null=True)
    is_choice = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'base_restrictioncodetype'


class BaseSpatialrepresentationtype(models.Model):
    identifier = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    description_en = models.CharField(max_length=255, blank=True, null=True)
    gn_description = models.CharField(max_length=255)
    gn_description_en = models.CharField(max_length=255, blank=True, null=True)
    is_choice = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'base_spatialrepresentationtype'


class BaseTaggedcontentitem(models.Model):
    content_object = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    tag = models.ForeignKey(BaseHierarchicalkeyword, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_taggedcontentitem'


class BaseThesaurus(models.Model):
    identifier = models.CharField(unique=True, max_length=255)
    title = models.CharField(max_length=255)
    date = models.CharField(max_length=20)
    description = models.TextField()
    slug = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'base_thesaurus'


class BaseThesauruskeyword(models.Model):
    about = models.CharField(max_length=255, blank=True, null=True)
    alt_label = models.CharField(max_length=255, blank=True, null=True)
    thesaurus = models.ForeignKey(BaseThesaurus, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_thesauruskeyword'
        unique_together = (('thesaurus', 'alt_label'),)


class BaseThesauruskeywordlabel(models.Model):
    lang = models.CharField(max_length=3)
    label = models.CharField(max_length=255)
    keyword = models.ForeignKey(BaseThesauruskeyword, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_thesauruskeywordlabel'
        unique_together = (('keyword', 'lang'),)


class BaseTopiccategory(models.Model):
    identifier = models.CharField(max_length=255)
    description = models.TextField()
    description_en = models.TextField(blank=True, null=True)
    gn_description = models.TextField(blank=True, null=True)
    gn_description_en = models.TextField(blank=True, null=True)
    is_choice = models.BooleanField()
    fa_class = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'base_topiccategory'


class BaseUsergeolimit(models.Model):
    wkt = models.TextField()
    resource = models.ForeignKey(BaseResourcebase, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'base_usergeolimit'


class BrRestoredbackup(models.Model):
    name = models.CharField(max_length=400)
    archive_md5 = models.CharField(max_length=32)
    restoration_date = models.DateTimeField()
    creation_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'br_restoredbackup'


class DialogosComment(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    object_id = models.IntegerField()
    comment = models.TextField()
    submit_date = models.DateTimeField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    public = models.BooleanField()
    author = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'dialogos_comment'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class DocumentsDocument(models.Model):
    resourcebase_ptr = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, primary_key=True)
    title_en = models.CharField(max_length=255, blank=True, null=True)
    abstract_en = models.TextField(blank=True, null=True)
    purpose_en = models.TextField(blank=True, null=True)
    constraints_other_en = models.TextField(blank=True, null=True)
    supplemental_information_en = models.TextField(blank=True, null=True)
    data_quality_statement_en = models.TextField(blank=True, null=True)
    doc_file = models.CharField(max_length=255, blank=True, null=True)
    extension = models.CharField(max_length=128, blank=True, null=True)
    doc_type = models.CharField(max_length=128, blank=True, null=True)
    doc_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documents_document'


class DocumentsDocumentresourcelink(models.Model):
    object_id = models.IntegerField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    document = models.ForeignKey(DocumentsDocument, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'documents_documentresourcelink'


class FavoriteFavorite(models.Model):
    object_id = models.IntegerField()
    created_on = models.DateTimeField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'favorite_favorite'
        unique_together = (('user', 'content_type', 'object_id'),)


class FrequentlyEntry(models.Model):
    question = models.TextField()
    slug = models.CharField(unique=True, max_length=200)
    answer = models.TextField()
    creation_date = models.DateTimeField()
    last_view_date = models.DateTimeField()
    amount_of_views = models.IntegerField()
    fixed_position = models.IntegerField(blank=True, null=True)
    upvotes = models.IntegerField()
    downvotes = models.IntegerField()
    published = models.BooleanField()
    submitted_by = models.CharField(max_length=100)
    owner = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)
    answer_es = models.TextField()
    question_es = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'frequently_entry'


class FrequentlyEntryCategory(models.Model):
    entry = models.ForeignKey(FrequentlyEntry, models.DO_NOTHING)
    entrycategory = models.ForeignKey('FrequentlyEntrycategory', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'frequently_entry_category'
        unique_together = (('entry', 'entrycategory'),)


class FrequentlyEntrycategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(unique=True, max_length=100)
    fixed_position = models.IntegerField(blank=True, null=True)
    last_rank = models.FloatField()
    name_es = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'frequently_entrycategory'


class FrequentlyFeedback(models.Model):
    remark = models.TextField()
    submission_date = models.DateTimeField()
    validation = models.CharField(max_length=1)
    entry = models.ForeignKey(FrequentlyEntry, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'frequently_feedback'


class GeoappGeostoriesGeostory(models.Model):
    geoapp_ptr = models.ForeignKey('GeoappsGeoapp', models.DO_NOTHING, primary_key=True)
    geostory_app_type = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'geoapp_geostories_geostory'


class GeoappsGeoapp(models.Model):
    resourcebase_ptr = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, primary_key=True)
    name = models.TextField(unique=True)
    zoom = models.IntegerField(blank=True, null=True)
    projection = models.CharField(max_length=32, blank=True, null=True)
    center_x = models.FloatField(blank=True, null=True)
    center_y = models.FloatField(blank=True, null=True)
    last_modified = models.DateTimeField()
    urlsuffix = models.CharField(max_length=255, blank=True, null=True)
    data = models.ForeignKey('GeoappsGeoappdata', models.DO_NOTHING, unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'geoapps_geoapp'


class GeoappsGeoappdata(models.Model):
    blob = models.TextField()  # This field type is a guess.
    resource = models.ForeignKey(GeoappsGeoapp, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'geoapps_geoappdata'


class GeonodeThemesGeonodethemecustomization(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    is_enabled = models.BooleanField()
    logo = models.CharField(max_length=100, blank=True, null=True)
    jumbotron_bg = models.CharField(max_length=100, blank=True, null=True)
    jumbotron_welcome_hide = models.BooleanField()
    jumbotron_welcome_title = models.CharField(max_length=255, blank=True, null=True)
    jumbotron_welcome_content = models.TextField(blank=True, null=True)
    body_color = models.CharField(max_length=10)
    navbar_color = models.CharField(max_length=10)
    jumbotron_color = models.CharField(max_length=10)
    copyright_color = models.CharField(max_length=10)
    contactus = models.BooleanField()
    copyright = models.TextField(blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    contact_position = models.CharField(max_length=255, blank=True, null=True)
    contact_administrative_area = models.CharField(max_length=255, blank=True, null=True)
    contact_street = models.CharField(max_length=255, blank=True, null=True)
    contact_postal_code = models.CharField(max_length=255, blank=True, null=True)
    contact_city = models.CharField(max_length=255, blank=True, null=True)
    contact_country = models.CharField(max_length=255, blank=True, null=True)
    contact_delivery_point = models.CharField(max_length=255, blank=True, null=True)
    contact_voice = models.CharField(max_length=255, blank=True, null=True)
    contact_facsimile = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    partners_title = models.CharField(max_length=100, blank=True, null=True)
    jumbotron_cta_hide = models.BooleanField()
    jumbotron_cta_link = models.CharField(max_length=255, blank=True, null=True)
    jumbotron_cta_text = models.CharField(max_length=255, blank=True, null=True)
    cookie_law_info_accept_close_reload = models.CharField(max_length=30)
    cookie_law_info_animate_speed_hide = models.CharField(max_length=30)
    cookie_law_info_animate_speed_show = models.CharField(max_length=30)
    cookie_law_info_as_popup = models.CharField(max_length=30)
    cookie_law_info_background = models.CharField(max_length=30)
    cookie_law_info_bar_enabled = models.BooleanField()
    cookie_law_info_bar_head = models.TextField()
    cookie_law_info_bar_heading_text = models.CharField(max_length=30)
    cookie_law_info_bar_text = models.TextField()
    cookie_law_info_border = models.CharField(max_length=30)
    cookie_law_info_border_on = models.CharField(max_length=30)
    cookie_law_info_button_1_as_button = models.CharField(max_length=30)
    cookie_law_info_button_1_button_colour = models.CharField(max_length=30)
    cookie_law_info_button_1_button_hover = models.CharField(max_length=30)
    cookie_law_info_button_1_link_colour = models.CharField(max_length=30)
    cookie_law_info_button_1_new_win = models.CharField(max_length=30)
    cookie_law_info_button_2_as_button = models.CharField(max_length=30)
    cookie_law_info_button_2_button_colour = models.CharField(max_length=30)
    cookie_law_info_button_2_button_hover = models.CharField(max_length=30)
    cookie_law_info_button_2_hidebar = models.CharField(max_length=30)
    cookie_law_info_button_2_link_colour = models.CharField(max_length=30)
    cookie_law_info_button_3_as_button = models.CharField(max_length=30)
    cookie_law_info_button_3_button_colour = models.CharField(max_length=30)
    cookie_law_info_button_3_button_hover = models.CharField(max_length=30)
    cookie_law_info_button_3_link_colour = models.CharField(max_length=30)
    cookie_law_info_button_3_new_win = models.CharField(max_length=30)
    cookie_law_info_button_4_as_button = models.CharField(max_length=30)
    cookie_law_info_button_4_button_colour = models.CharField(max_length=30)
    cookie_law_info_button_4_button_hover = models.CharField(max_length=30)
    cookie_law_info_button_4_link_colour = models.CharField(max_length=30)
    cookie_law_info_cookie_bar_as = models.CharField(max_length=30)
    cookie_law_info_font_family = models.CharField(max_length=30)
    cookie_law_info_header_fix = models.CharField(max_length=30)
    cookie_law_info_leave_url = models.TextField()
    cookie_law_info_logging_on = models.CharField(max_length=30)
    cookie_law_info_notify_animate_hide = models.CharField(max_length=30)
    cookie_law_info_notify_animate_show = models.CharField(max_length=30)
    cookie_law_info_notify_div_id = models.CharField(max_length=30)
    cookie_law_info_notify_position_horizontal = models.CharField(max_length=30)
    cookie_law_info_notify_position_vertical = models.CharField(max_length=30)
    cookie_law_info_popup_overlay = models.CharField(max_length=30)
    cookie_law_info_popup_showagain_position = models.CharField(max_length=30)
    cookie_law_info_reject_close_reload = models.CharField(max_length=30)
    cookie_law_info_scroll_close = models.CharField(max_length=30)
    cookie_law_info_scroll_close_reload = models.CharField(max_length=30)
    cookie_law_info_show_once = models.CharField(max_length=30)
    cookie_law_info_show_once_yn = models.CharField(max_length=30)
    cookie_law_info_showagain_background = models.CharField(max_length=30)
    cookie_law_info_showagain_border = models.CharField(max_length=30)
    cookie_law_info_showagain_div_id = models.CharField(max_length=30)
    cookie_law_info_showagain_head = models.TextField()
    cookie_law_info_showagain_tab = models.CharField(max_length=30)
    cookie_law_info_showagain_x_position = models.CharField(max_length=30)
    cookie_law_info_text = models.CharField(max_length=30)
    cookie_law_info_widget_position = models.CharField(max_length=30)
    cookie_law_info_data_controller = models.TextField()
    cookie_law_info_data_controller_address = models.TextField()
    cookie_law_info_data_controller_email = models.TextField()
    cookie_law_info_data_controller_phone = models.TextField()
    navbar_dropdown_menu = models.CharField(max_length=10)
    navbar_dropdown_menu_divider = models.CharField(max_length=10)
    navbar_dropdown_menu_hover = models.CharField(max_length=10)
    navbar_dropdown_menu_text = models.CharField(max_length=10)
    navbar_text_color = models.CharField(max_length=10)
    navbar_text_hover = models.CharField(max_length=10)
    navbar_text_hover_focus = models.CharField(max_length=10)
    body_text_color = models.CharField(max_length=10)
    jumbotron_text_color = models.CharField(max_length=10)
    jumbotron_title_color = models.CharField(max_length=10)
    footer_href_color = models.CharField(max_length=10)
    footer_text_color = models.CharField(max_length=10)
    search_bg_color = models.CharField(max_length=10)
    search_link_color = models.CharField(max_length=10)
    search_title_color = models.CharField(max_length=10)
    footer_bg_color = models.CharField(max_length=10)
    welcome_theme = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'geonode_themes_geonodethemecustomization'


class GeonodeThemesGeonodethemecustomizationJumbotronSlideShow(models.Model):
    geonodethemecustomization = models.ForeignKey(GeonodeThemesGeonodethemecustomization, models.DO_NOTHING)
    jumbotronthemeslide = models.ForeignKey('GeonodeThemesJumbotronthemeslide', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'geonode_themes_geonodethemecustomization_jumbotron_slide_show'
        unique_together = (('geonodethemecustomization', 'jumbotronthemeslide'),)


class GeonodeThemesGeonodethemecustomizationPartners(models.Model):
    geonodethemecustomization = models.ForeignKey(GeonodeThemesGeonodethemecustomization, models.DO_NOTHING)
    partner = models.ForeignKey('GeonodeThemesPartner', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'geonode_themes_geonodethemecustomization_partners'
        unique_together = (('geonodethemecustomization', 'partner'),)


class GeonodeThemesJumbotronthemeslide(models.Model):
    slide_name = models.CharField(unique=True, max_length=255)
    jumbotron_slide_image = models.CharField(max_length=100)
    jumbotron_slide_content = models.TextField(blank=True, null=True)
    hide_jumbotron_slide_content = models.BooleanField()
    is_enabled = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'geonode_themes_jumbotronthemeslide'


class GeonodeThemesPartner(models.Model):
    logo = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    href = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'geonode_themes_partner'


class GroupsGroupcategory(models.Model):
    slug = models.CharField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    name_en = models.CharField(unique=True, max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'groups_groupcategory'


class GroupsGroupmember(models.Model):
    role = models.CharField(max_length=10)
    joined = models.DateTimeField()
    group = models.ForeignKey('GroupsGroupprofile', models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'groups_groupmember'


class GroupsGroupprofile(models.Model):
    title = models.CharField(max_length=1000)
    slug = models.CharField(unique=True, max_length=1000)
    logo = models.CharField(max_length=100)
    description = models.TextField()
    email = models.CharField(max_length=254, blank=True, null=True)
    access = models.CharField(max_length=15)
    last_modified = models.DateTimeField(blank=True, null=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING, unique=True)
    description_en = models.TextField(blank=True, null=True)
    title_en = models.CharField(max_length=1000, blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'groups_groupprofile'


class GroupsGroupprofileCategories(models.Model):
    groupprofile = models.ForeignKey(GroupsGroupprofile, models.DO_NOTHING)
    groupcategory = models.ForeignKey(GroupsGroupcategory, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'groups_groupprofile_categories'
        unique_together = (('groupprofile', 'groupcategory'),)


class GuardianGroupobjectpermission(models.Model):
    object_pk = models.CharField(max_length=255)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'guardian_groupobjectpermission'
        unique_together = (('group', 'permission', 'object_pk'),)


class GuardianUserobjectpermission(models.Model):
    object_pk = models.CharField(max_length=255)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'guardian_userobjectpermission'
        unique_together = (('user', 'permission', 'object_pk'),)


class InvitationsInvitation(models.Model):
    email = models.CharField(unique=True, max_length=254)
    accepted = models.BooleanField()
    created = models.DateTimeField()
    key = models.CharField(unique=True, max_length=64)
    sent = models.DateTimeField(blank=True, null=True)
    inviter = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'invitations_invitation'


class LayersAttribute(models.Model):
    attribute = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    attribute_label = models.CharField(max_length=255, blank=True, null=True)
    attribute_type = models.CharField(max_length=50)
    visible = models.BooleanField()
    display_order = models.IntegerField()
    count = models.IntegerField()
    min = models.CharField(max_length=255, blank=True, null=True)
    max = models.CharField(max_length=255, blank=True, null=True)
    average = models.CharField(max_length=255, blank=True, null=True)
    median = models.CharField(max_length=255, blank=True, null=True)
    stddev = models.CharField(max_length=255, blank=True, null=True)
    sum = models.CharField(max_length=255, blank=True, null=True)
    unique_values = models.TextField(blank=True, null=True)
    last_stats_updated = models.DateTimeField()
    layer = models.ForeignKey('LayersLayer', models.DO_NOTHING)
    featureinfo_type = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'layers_attribute'


class LayersLayer(models.Model):
    resourcebase_ptr = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, primary_key=True)
    title_en = models.CharField(max_length=255, blank=True, null=True)
    abstract_en = models.TextField(blank=True, null=True)
    purpose_en = models.TextField(blank=True, null=True)
    constraints_other_en = models.TextField(blank=True, null=True)
    supplemental_information_en = models.TextField(blank=True, null=True)
    data_quality_statement_en = models.TextField(blank=True, null=True)
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storetype = models.CharField(db_column='storeType', max_length=128)  # Field name made lowercase.
    name = models.CharField(max_length=128)
    typename = models.CharField(max_length=128, blank=True, null=True)
    charset = models.CharField(max_length=255)
    default_style = models.ForeignKey('LayersStyle', models.DO_NOTHING, blank=True, null=True)
    upload_session = models.ForeignKey('LayersUploadsession', models.DO_NOTHING, blank=True, null=True)
    elevation_regex = models.CharField(max_length=128, blank=True, null=True)
    has_elevation = models.BooleanField()
    has_time = models.BooleanField()
    is_mosaic = models.BooleanField()
    time_regex = models.CharField(max_length=128, blank=True, null=True)
    remote_service = models.ForeignKey('ServicesService', models.DO_NOTHING, blank=True, null=True)
    featureinfo_custom_template = models.TextField(blank=True, null=True)
    use_featureinfo_custom_template = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'layers_layer'


class LayersLayerStyles(models.Model):
    layer = models.ForeignKey(LayersLayer, models.DO_NOTHING)
    style = models.ForeignKey('LayersStyle', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'layers_layer_styles'
        unique_together = (('layer', 'style'),)


class LayersLayerfile(models.Model):
    name = models.CharField(max_length=255)
    base = models.BooleanField()
    file = models.CharField(max_length=255)
    upload_session = models.ForeignKey('LayersUploadsession', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'layers_layerfile'


class LayersStyle(models.Model):
    name = models.CharField(unique=True, max_length=255)
    sld_title = models.CharField(max_length=255, blank=True, null=True)
    sld_body = models.TextField(blank=True, null=True)
    sld_version = models.CharField(max_length=12, blank=True, null=True)
    sld_url = models.CharField(max_length=1000, blank=True, null=True)
    workspace = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'layers_style'


class LayersUploadsession(models.Model):
    date = models.DateTimeField()
    processed = models.BooleanField()
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    context = models.TextField(blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)
    resource = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'layers_uploadsession'


class MapsMap(models.Model):
    resourcebase_ptr = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, primary_key=True)
    title_en = models.CharField(max_length=255, blank=True, null=True)
    abstract_en = models.TextField(blank=True, null=True)
    purpose_en = models.TextField(blank=True, null=True)
    constraints_other_en = models.TextField(blank=True, null=True)
    supplemental_information_en = models.TextField(blank=True, null=True)
    data_quality_statement_en = models.TextField(blank=True, null=True)
    zoom = models.IntegerField()
    projection = models.CharField(max_length=32)
    center_x = models.FloatField()
    center_y = models.FloatField()
    last_modified = models.DateTimeField()
    urlsuffix = models.CharField(max_length=255)
    featuredurl = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'maps_map'


class MapsMaplayer(models.Model):
    stack_order = models.IntegerField()
    format = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    opacity = models.FloatField()
    styles = models.TextField(blank=True, null=True)
    transparent = models.BooleanField()
    fixed = models.BooleanField()
    group = models.TextField(blank=True, null=True)
    visibility = models.BooleanField()
    ows_url = models.CharField(max_length=200, blank=True, null=True)
    layer_params = models.TextField()
    source_params = models.TextField()
    local = models.BooleanField()
    map = models.ForeignKey(MapsMap, models.DO_NOTHING)
    store = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maps_maplayer'


class Mapstore2AdapterMapstoreattribute(models.Model):
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=80)
    value = models.TextField()
    resource = models.ForeignKey('Mapstore2AdapterMapstoreresource', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'mapstore2_adapter_mapstoreattribute'


class Mapstore2AdapterMapstoredata(models.Model):
    blob = models.TextField()
    resource = models.ForeignKey('Mapstore2AdapterMapstoreresource', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'mapstore2_adapter_mapstoredata'


class Mapstore2AdapterMapstoreresource(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    creation_date = models.DateTimeField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)
    data = models.ForeignKey(Mapstore2AdapterMapstoredata, models.DO_NOTHING, unique=True, blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'mapstore2_adapter_mapstoreresource'


class Mapstore2AdapterMapstoreresourceAttributes(models.Model):
    mapstoreresource = models.ForeignKey(Mapstore2AdapterMapstoreresource, models.DO_NOTHING)
    mapstoreattribute = models.ForeignKey(Mapstore2AdapterMapstoreattribute, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'mapstore2_adapter_mapstoreresource_attributes'
        unique_together = (('mapstoreresource', 'mapstoreattribute'),)


class MonitoringEventtype(models.Model):
    name = models.CharField(unique=True, max_length=16)

    class Meta:
        managed = False
        db_table = 'monitoring_eventtype'


class MonitoringExceptionevent(models.Model):
    created = models.DateTimeField()
    received = models.DateTimeField()
    error_type = models.CharField(max_length=255)
    error_data = models.TextField()
    request = models.ForeignKey('MonitoringRequestevent', models.DO_NOTHING)
    service = models.ForeignKey('MonitoringService', models.DO_NOTHING)
    error_message = models.TextField()

    class Meta:
        managed = False
        db_table = 'monitoring_exceptionevent'


class MonitoringHost(models.Model):
    name = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'monitoring_host'


class MonitoringMetric(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_metric'


class MonitoringMetriclabel(models.Model):
    name = models.TextField()
    user = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_metriclabel'


class MonitoringMetricnotificationcheck(models.Model):
    min_value = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    max_value = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    max_timeout = models.DurationField(blank=True, null=True)
    active = models.BooleanField()
    label = models.ForeignKey(MonitoringMetriclabel, models.DO_NOTHING, blank=True, null=True)
    metric = models.ForeignKey(MonitoringMetric, models.DO_NOTHING)
    notification_check = models.ForeignKey('MonitoringNotificationcheck', models.DO_NOTHING)
    resource = models.ForeignKey('MonitoringMonitoredresource', models.DO_NOTHING, blank=True, null=True)
    service = models.ForeignKey('MonitoringService', models.DO_NOTHING, blank=True, null=True)
    definition = models.ForeignKey('MonitoringNotificationmetricdefinition', models.DO_NOTHING, unique=True, blank=True, null=True)
    event_type = models.ForeignKey(MonitoringEventtype, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_metricnotificationcheck'


class MonitoringMetricvalue(models.Model):
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    value = models.CharField(max_length=255)
    value_num = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    value_raw = models.TextField(blank=True, null=True)
    data = models.TextField()
    label = models.ForeignKey(MonitoringMetriclabel, models.DO_NOTHING)
    resource = models.ForeignKey('MonitoringMonitoredresource', models.DO_NOTHING, blank=True, null=True)
    service = models.ForeignKey('MonitoringService', models.DO_NOTHING)
    service_metric = models.ForeignKey('MonitoringServicetypemetric', models.DO_NOTHING)
    samples_count = models.IntegerField()
    event_type = models.ForeignKey(MonitoringEventtype, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_metricvalue'
        unique_together = (('valid_from', 'valid_to', 'service', 'service_metric', 'resource', 'label', 'event_type'),)


class MonitoringMonitoredresource(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    resource_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_monitoredresource'
        unique_together = (('name', 'type'),)


class MonitoringNotificationcheck(models.Model):
    name = models.CharField(unique=True, max_length=255)
    description = models.CharField(max_length=255)
    user_threshold = models.TextField()
    grace_period = models.DurationField()
    last_send = models.DateTimeField(blank=True, null=True)
    severity = models.CharField(max_length=32)
    active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'monitoring_notificationcheck'


class MonitoringNotificationmetricdefinition(models.Model):
    use_service = models.BooleanField()
    use_resource = models.BooleanField()
    use_label = models.BooleanField()
    field_option = models.CharField(max_length=32)
    metric = models.ForeignKey(MonitoringMetric, models.DO_NOTHING)
    notification_check = models.ForeignKey(MonitoringNotificationcheck, models.DO_NOTHING)
    description = models.TextField(blank=True, null=True)
    max_value = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    min_value = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)
    steps = models.IntegerField(blank=True, null=True)
    use_event_type = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'monitoring_notificationmetricdefinition'


class MonitoringNotificationreceiver(models.Model):
    email = models.CharField(max_length=254, blank=True, null=True)
    notification_check = models.ForeignKey(MonitoringNotificationcheck, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_notificationreceiver'


class MonitoringRequestevent(models.Model):
    created = models.DateTimeField()
    received = models.DateTimeField()
    host = models.CharField(max_length=255)
    request_path = models.TextField()
    request_method = models.CharField(max_length=16)
    response_status = models.IntegerField()
    response_size = models.IntegerField()
    response_time = models.IntegerField()
    response_type = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    user_agent_family = models.CharField(max_length=255, blank=True, null=True)
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    client_lat = models.DecimalField(max_digits=11, decimal_places=5, blank=True, null=True)
    client_lon = models.DecimalField(max_digits=11, decimal_places=5, blank=True, null=True)
    client_country = models.CharField(max_length=255, blank=True, null=True)
    client_region = models.CharField(max_length=255, blank=True, null=True)
    client_city = models.CharField(max_length=255, blank=True, null=True)
    custom_id = models.CharField(max_length=255, blank=True, null=True)
    service = models.ForeignKey('MonitoringService', models.DO_NOTHING)
    user_identifier = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.ForeignKey(MonitoringEventtype, models.DO_NOTHING, blank=True, null=True)
    user_username = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monitoring_requestevent'


class MonitoringRequesteventResources(models.Model):
    requestevent = models.ForeignKey(MonitoringRequestevent, models.DO_NOTHING)
    monitoredresource = models.ForeignKey(MonitoringMonitoredresource, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'monitoring_requestevent_resources'
        unique_together = (('requestevent', 'monitoredresource'),)


class MonitoringService(models.Model):
    name = models.CharField(unique=True, max_length=255)
    check_interval = models.DurationField()
    last_check = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField()
    notes = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    host = models.ForeignKey(MonitoringHost, models.DO_NOTHING)
    service_type = models.ForeignKey('MonitoringServicetype', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'monitoring_service'


class MonitoringServicetype(models.Model):
    name = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'monitoring_servicetype'


class MonitoringServicetypemetric(models.Model):
    metric = models.ForeignKey(MonitoringMetric, models.DO_NOTHING)
    service_type = models.ForeignKey(MonitoringServicetype, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'monitoring_servicetypemetric'


class Oauth2ProviderAccesstoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.CharField(unique=True, max_length=255)
    expires = models.DateTimeField()
    scope = models.TextField()
    application = models.ForeignKey('Oauth2ProviderApplication', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    source_refresh_token = models.ForeignKey('Oauth2ProviderRefreshtoken', models.DO_NOTHING, unique=True, blank=True, null=True)
    id_token = models.ForeignKey('Oauth2ProviderIdtoken', models.DO_NOTHING, unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_accesstoken'


class Oauth2ProviderApplication(models.Model):
    id = models.BigAutoField(primary_key=True)
    client_id = models.CharField(unique=True, max_length=100)
    redirect_uris = models.TextField()
    client_type = models.CharField(max_length=32)
    authorization_grant_type = models.CharField(max_length=32)
    client_secret = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)
    skip_authorization = models.BooleanField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    algorithm = models.CharField(max_length=5)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_application'


class Oauth2ProviderGrant(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=255)
    expires = models.DateTimeField()
    redirect_uri = models.CharField(max_length=255)
    scope = models.TextField()
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    code_challenge = models.CharField(max_length=128)
    code_challenge_method = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_grant'


class Oauth2ProviderIdtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.TextField(unique=True)
    expires = models.DateTimeField()
    scope = models.TextField()
    created = models.DateTimeField()
    updated = models.DateTimeField()
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_idtoken'


class Oauth2ProviderRefreshtoken(models.Model):
    id = models.BigAutoField(primary_key=True)
    token = models.CharField(max_length=255)
    access_token = models.ForeignKey(Oauth2ProviderAccesstoken, models.DO_NOTHING, unique=True, blank=True, null=True)
    application = models.ForeignKey(Oauth2ProviderApplication, models.DO_NOTHING)
    user = models.ForeignKey('PeopleProfile', models.DO_NOTHING)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    revoked = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oauth2_provider_refreshtoken'
        unique_together = (('token', 'revoked'),)


class PeopleProfile(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    organization = models.CharField(max_length=255, blank=True, null=True)
    profile = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=3, blank=True, null=True)
    language = models.CharField(max_length=10)
    timezone = models.CharField(max_length=100)
    other_role = models.CharField(max_length=50, blank=True, null=True)
    use_analysis = models.CharField(max_length=8, blank=True, null=True)
    other_analysis = models.CharField(max_length=50, blank=True, null=True)
    professional_role = models.CharField(max_length=6, blank=True, null=True)
    agree_conditions = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'people_profile'


class PeopleProfileGroups(models.Model):
    profile = models.ForeignKey(PeopleProfile, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'people_profile_groups'
        unique_together = (('profile', 'group'),)


class PeopleProfileUserPermissions(models.Model):
    profile = models.ForeignKey(PeopleProfile, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'people_profile_user_permissions'
        unique_together = (('profile', 'permission'),)


class PinaxNotificationsNoticequeuebatch(models.Model):
    pickled_data = models.TextField()

    class Meta:
        managed = False
        db_table = 'pinax_notifications_noticequeuebatch'


class PinaxNotificationsNoticesetting(models.Model):
    medium = models.CharField(max_length=1)
    send = models.BooleanField()
    scoping_object_id = models.IntegerField(blank=True, null=True)
    notice_type = models.ForeignKey('PinaxNotificationsNoticetype', models.DO_NOTHING)
    scoping_content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'pinax_notifications_noticesetting'
        unique_together = (('user', 'notice_type', 'medium', 'scoping_content_type', 'scoping_object_id'),)


class PinaxNotificationsNoticetype(models.Model):
    label = models.CharField(max_length=40)
    display = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    default = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'pinax_notifications_noticetype'


class RatingsOverallrating(models.Model):
    object_id = models.IntegerField()
    rating = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    category = models.CharField(max_length=250)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'ratings_overallrating'
        unique_together = (('object_id', 'content_type', 'category'),)


class RatingsRating(models.Model):
    object_id = models.IntegerField()
    rating = models.IntegerField()
    timestamp = models.DateTimeField()
    category = models.CharField(max_length=250)
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    overall_rating = models.ForeignKey(RatingsOverallrating, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'ratings_rating'
        unique_together = (('object_id', 'content_type', 'user', 'category'),)


class ServicesHarvestjob(models.Model):
    resource_id = models.CharField(max_length=255)
    status = models.CharField(max_length=15)
    service = models.ForeignKey('ServicesService', models.DO_NOTHING)
    details = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'services_harvestjob'


class ServicesService(models.Model):
    resourcebase_ptr = models.ForeignKey(BaseResourcebase, models.DO_NOTHING, primary_key=True)
    type = models.CharField(max_length=10)
    method = models.CharField(max_length=1)
    base_url = models.CharField(unique=True, max_length=200)
    version = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    online_resource = models.CharField(max_length=200, blank=True, null=True)
    fees = models.CharField(max_length=1000, blank=True, null=True)
    access_constraints = models.CharField(max_length=255, blank=True, null=True)
    connection_params = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50, blank=True, null=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    workspace_ref = models.CharField(max_length=200, blank=True, null=True)
    store_ref = models.CharField(max_length=200, blank=True, null=True)
    resources_ref = models.CharField(max_length=200, blank=True, null=True)
    first_noanswer = models.DateTimeField(blank=True, null=True)
    noanswer_retries = models.IntegerField(blank=True, null=True)
    external_id = models.IntegerField(blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    proxy_base = models.CharField(max_length=200, blank=True, null=True)
    probe = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'services_service'


class ServicesServiceprofilerole(models.Model):
    role = models.CharField(max_length=255)
    profiles = models.ForeignKey(PeopleProfile, models.DO_NOTHING)
    service = models.ForeignKey(ServicesService, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'services_serviceprofilerole'


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.TextField()
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class StudyCasesStudycases(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)
    treatment_plants = models.CharField(max_length=255)
    water_intakes = models.CharField(max_length=255)
    with_carbon_markets = models.BooleanField()
    erosion_control_drinking_water_qa = models.BooleanField()
    nutrient_retention_ph = models.BooleanField()
    nutrient_retention_ni = models.BooleanField()
    flood_mitigation = models.BooleanField()
    groundwater_recharge_enhancement = models.BooleanField()
    baseflow = models.BooleanField()
    annual_water_yield = models.CharField(max_length=1024)
    sediment_delivery_ratio = models.CharField(max_length=1024)
    nutrient_delivery = models.CharField(max_length=1024)
    seasonal_water_yield = models.CharField(max_length=1024)
    carbon_storage = models.CharField(max_length=1024)
    platform_cost_per_year = models.FloatField()
    personnel_salary_benefits = models.FloatField()
    program_director = models.FloatField()
    monitoring_and_evaluation_mngr = models.FloatField()
    finance_and_admin = models.FloatField()
    implementation_manager = models.FloatField()
    office_costs = models.FloatField()
    travel = models.FloatField()
    equipment = models.FloatField()
    contracts = models.FloatField()
    overhead = models.FloatField()
    others = models.FloatField()
    transaction_costs = models.FloatField()
    discount_rate = models.FloatField()
    sensitive_analysis_min_disc_rate = models.FloatField()
    sensitive_analysis_max_disc_rate = models.FloatField()
    nbs_ca_conservation = models.BooleanField()
    nbs_ca_active_restoration = models.BooleanField()
    nbs_ca_passive_restoration = models.BooleanField()
    nbs_ca_agroforestry = models.BooleanField()
    nbs_ca_silvopastoral = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'study_cases_studycases'


class TaggitTag(models.Model):
    name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'taggit_tag'


class TaggitTaggeditem(models.Model):
    object_id = models.IntegerField()
    content_type = models.ForeignKey(DjangoContentType, models.DO_NOTHING)
    tag = models.ForeignKey(TaggitTag, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'taggit_taggeditem'
        unique_together = (('content_type', 'object_id', 'tag'),)


class TastypieApiaccess(models.Model):
    identifier = models.CharField(max_length=255)
    url = models.TextField()
    request_method = models.CharField(max_length=10)
    accessed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tastypie_apiaccess'


class TastypieApikey(models.Model):
    key = models.CharField(max_length=128)
    created = models.DateTimeField()
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING, unique=True)

    class Meta:
        managed = False
        db_table = 'tastypie_apikey'


class UploadUpload(models.Model):
    import_id = models.BigIntegerField(blank=True, null=True)
    state = models.CharField(max_length=16)
    date = models.DateTimeField()
    upload_dir = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    complete = models.BooleanField()
    session = models.TextField(blank=True, null=True)
    metadata = models.TextField(blank=True, null=True)
    mosaic_time_regex = models.CharField(max_length=128, blank=True, null=True)
    mosaic_time_value = models.CharField(max_length=128, blank=True, null=True)
    mosaic_elev_regex = models.CharField(max_length=128, blank=True, null=True)
    mosaic_elev_value = models.CharField(max_length=128, blank=True, null=True)
    layer = models.ForeignKey(LayersLayer, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'upload_upload'


class UploadUploadfile(models.Model):
    file = models.CharField(max_length=100)
    slug = models.CharField(max_length=50)
    upload = models.ForeignKey(UploadUpload, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'upload_uploadfile'


class UserMessagesGroupmemberthread(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    thread = models.ForeignKey('UserMessagesThread', models.DO_NOTHING)
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING)
    deleted = models.BooleanField()
    unread = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'user_messages_groupmemberthread'


class UserMessagesMessage(models.Model):
    sent_at = models.DateTimeField()
    content = models.TextField()
    sender = models.ForeignKey(PeopleProfile, models.DO_NOTHING)
    thread = models.ForeignKey('UserMessagesThread', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_messages_message'


class UserMessagesThread(models.Model):
    subject = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'user_messages_thread'


class UserMessagesUserthread(models.Model):
    unread = models.BooleanField()
    deleted = models.BooleanField()
    thread = models.ForeignKey(UserMessagesThread, models.DO_NOTHING)
    user = models.ForeignKey(PeopleProfile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_messages_userthread'


class WaterproofBdgProcessesEfficiencies(models.Model):
    sistema = models.CharField(max_length=9, blank=True, null=True)
    id_proceso = models.CharField(max_length=3, blank=True, null=True)
    proceso_unitario = models.CharField(max_length=34, blank=True, null=True)
    id_categorias = models.IntegerField(blank=True, null=True)
    simbolo = models.CharField(max_length=3, blank=True, null=True)
    categorias = models.CharField(max_length=42, blank=True, null=True)
    porcen_sedimentos_minimo = models.IntegerField(blank=True, null=True)
    porcen_sedimentos_predefinido = models.CharField(max_length=4, blank=True, null=True)
    porcen_sedimentos_maximo = models.IntegerField(blank=True, null=True)
    porcen_nitrogeno_minimo = models.CharField(max_length=3, blank=True, null=True)
    porcen_nitrogeno_predefinido = models.CharField(max_length=19, blank=True, null=True)
    porcen_nitrogeno_maximo = models.IntegerField(blank=True, null=True)
    porcen_fosforo_minimo = models.CharField(max_length=3, blank=True, null=True)
    porcen_fosforo_predefinido = models.CharField(max_length=18, blank=True, null=True)
    porcen_fosforo_maximo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_bdg_processes_efficiencies'


class WaterproofIntakeBasins(models.Model):
    id = models.DecimalField(primary_key=True, max_digits=65535, decimal_places=65535)
    geom = models.MultiPolygonField(blank=True, null=True)
    continent = models.CharField(max_length=254, blank=True, null=True)
    symbol = models.CharField(max_length=254, blank=True, null=True)
    code = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    label = models.CharField(max_length=50, blank=True, null=True)
    x_min = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    x_max = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    y_min = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    y_max = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_basins'


class WaterproofIntakeCity(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey('WaterproofNbsCaCountries', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_city'


class WaterproofIntakeCostfunctionsprocess(models.Model):
    symbol = models.CharField(max_length=5)
    categorys = models.CharField(max_length=100)
    energy = models.DecimalField(max_digits=14, decimal_places=4)
    labour = models.DecimalField(max_digits=14, decimal_places=4)
    mater_equipment = models.DecimalField(max_digits=14, decimal_places=4)
    function_value = models.CharField(max_length=1000)
    function_name = models.CharField(max_length=250)
    function_description = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_costfunctionsprocess'


class WaterproofIntakeDemandparameters(models.Model):
    interpolation_type = models.CharField(max_length=30)
    initial_extraction = models.DecimalField(max_digits=14, decimal_places=4)
    ending_extraction = models.DecimalField(max_digits=14, decimal_places=4)
    years_number = models.IntegerField()
    is_manual = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'waterproof_intake_demandparameters'


class WaterproofIntakeElementsystem(models.Model):
    name = models.CharField(max_length=100)
    nitrogen = models.DecimalField(max_digits=14, decimal_places=4)
    normalized_category = models.CharField(max_length=100)
    phosphorus = models.DecimalField(max_digits=14, decimal_places=4)
    sediment = models.DecimalField(max_digits=14, decimal_places=4)
    intake = models.ForeignKey('WaterproofIntakeIntake', models.DO_NOTHING)
    q_l_s = models.FloatField(blank=True, null=True)
    awy = models.FloatField(blank=True, null=True)
    cn_mg_l = models.FloatField(blank=True, null=True)
    cp_mg_l = models.FloatField(blank=True, null=True)
    csed_mg_l = models.FloatField(blank=True, null=True)
    wn_kg = models.FloatField(blank=True, null=True)
    wn_ret_kg = models.FloatField(blank=True, null=True)
    wp_ret_ton = models.FloatField(blank=True, null=True)
    wsed_ret_ton = models.FloatField(blank=True, null=True)
    wsed_ton = models.FloatField(blank=True, null=True)
    wp_kg = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_elementsystem'


class WaterproofIntakeElementsystemSystemCost(models.Model):
    elementsystem_id = models.IntegerField()
    systemcosts_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'waterproof_intake_elementsystem_system_cost'


class WaterproofIntakeElementsystemUserCost(models.Model):
    elementsystem_id = models.IntegerField()
    usercosts_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'waterproof_intake_elementsystem_user_cost'


class WaterproofIntakeExternalinputs(models.Model):
    year = models.IntegerField()
    water_volume = models.DecimalField(max_digits=14, decimal_places=4)
    sediment = models.DecimalField(max_digits=14, decimal_places=4)
    nitrogen = models.DecimalField(max_digits=14, decimal_places=4)
    phosphorus = models.DecimalField(max_digits=14, decimal_places=4)
    element = models.ForeignKey(WaterproofIntakeElementsystem, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_externalinputs'


class WaterproofIntakeIntake(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)
    water_source_name = models.CharField(max_length=100)
    xml_graph = models.TextField()
    added_by = models.ForeignKey(PeopleProfile, models.DO_NOTHING, blank=True, null=True)
    city = models.ForeignKey(WaterproofIntakeCity, models.DO_NOTHING)
    demand_parameters = models.ForeignKey(WaterproofIntakeDemandparameters, models.DO_NOTHING)
    creation_date = models.DateField()
    updated_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'waterproof_intake_intake'


class WaterproofIntakePolygon(models.Model):
    area = models.FloatField(blank=True, null=True)
    geom = models.PolygonField(blank=True, null=True)
    delimitation_date = models.DateField()
    delimitation_type = models.CharField(max_length=30)
    basin = models.ForeignKey(WaterproofIntakeBasins, models.DO_NOTHING)
    intake = models.ForeignKey(WaterproofIntakeIntake, models.DO_NOTHING)
    geomintake = models.PolygonField(db_column='geomIntake', blank=True, null=True)  # Field name made lowercase.
    geompoint = models.PointField(db_column='geomPoint', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'waterproof_intake_polygon'


class WaterproofIntakeProcessefficiencies(models.Model):
    name = models.CharField(max_length=100)
    unitary_process = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)
    categorys = models.CharField(max_length=100)
    normalized_category = models.CharField(max_length=100)
    minimal_sediment_perc = models.IntegerField()
    predefined_sediment_perc = models.DecimalField(max_digits=14, decimal_places=4)
    maximal_sediment_perc = models.IntegerField()
    minimal_nitrogen_perc = models.IntegerField()
    predefined_nitrogen_perc = models.DecimalField(max_digits=14, decimal_places=4)
    maximal_nitrogen_perc = models.IntegerField()
    minimal_phoshorus_perc = models.IntegerField()
    predefined_phosphorus_perc = models.DecimalField(max_digits=14, decimal_places=4)
    maximal_phosphorus_perc = models.IntegerField()
    minimal_transp_water_perc = models.IntegerField()
    predefined_transp_water_perc = models.DecimalField(max_digits=14, decimal_places=4)
    maximal_transp_water_perc = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'waterproof_intake_processefficiencies'


class WaterproofIntakeSystemcosts(models.Model):
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_systemcosts'


class WaterproofIntakeUsercosts(models.Model):
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_usercosts'


class WaterproofIntakeWaterextraction(models.Model):
    year = models.IntegerField()
    value = models.DecimalField(max_digits=14, decimal_places=4)
    demand = models.ForeignKey(WaterproofIntakeDemandparameters, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_intake_waterextraction'


class WaterproofNbsCaActivityshapefile(models.Model):
    activity = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    area = models.MultiPolygonField()

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_activityshapefile'


class WaterproofNbsCaCountries(models.Model):
    name = models.CharField(max_length=100)
    factor = models.FloatField()
    region = models.ForeignKey('WaterproofNbsCaRegion', models.DO_NOTHING)
    code = models.CharField(max_length=5)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_countries'


class WaterproofNbsCaCurrency(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    factor = models.CharField(max_length=50)
    country = models.ForeignKey(WaterproofNbsCaCountries, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_currency'


class WaterproofNbsCaRegion(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_region'


class WaterproofNbsCaRiosactivity(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)
    transition = models.ForeignKey('WaterproofNbsCaRiostransition', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_riosactivity'


class WaterproofNbsCaRiostransformation(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)
    activity = models.ForeignKey(WaterproofNbsCaRiosactivity, models.DO_NOTHING)
    unique_id = models.CharField(max_length=1024)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_riostransformation'


class WaterproofNbsCaRiostransition(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1024)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_riostransition'


class WaterproofNbsCaWaterproofnbsca(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2048)
    max_benefit_req_time = models.IntegerField()
    periodicity_maitenance = models.IntegerField()
    profit_pct_time_inter_assoc = models.IntegerField()
    total_profits_sbn_consec_time = models.IntegerField()
    unit_implementation_cost = models.DecimalField(max_digits=14, decimal_places=4)
    unit_maintenance_cost = models.DecimalField(max_digits=14, decimal_places=4)
    unit_oportunity_cost = models.DecimalField(max_digits=14, decimal_places=4)
    added_by = models.ForeignKey(PeopleProfile, models.DO_NOTHING, blank=True, null=True)
    country = models.ForeignKey(WaterproofNbsCaCountries, models.DO_NOTHING)
    currency = models.ForeignKey(WaterproofNbsCaCurrency, models.DO_NOTHING)
    activity_shapefile = models.ForeignKey(WaterproofNbsCaActivityshapefile, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_waterproofnbsca'


class WaterproofNbsCaWaterproofnbscaRiosTransformations(models.Model):
    waterproofnbsca = models.ForeignKey(WaterproofNbsCaWaterproofnbsca, models.DO_NOTHING)
    riostransformation = models.ForeignKey(WaterproofNbsCaRiostransformation, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'waterproof_nbs_ca_waterproofnbsca_rios_transformations'
        unique_together = (('waterproofnbsca', 'riostransformation'),)


class WaterproofStudyCases(models.Model):
    dws_name = models.CharField(max_length=100, blank=True, null=True)
    dws_description = models.CharField(max_length=500, blank=True, null=True)
    dws_analysis_period_value = models.IntegerField(blank=True, null=True)
    dws_type_money = models.CharField(max_length=10, blank=True, null=True)
    dws_benefit_function = models.CharField(max_length=100, blank=True, null=True)
    estado_id = models.IntegerField(blank=True, null=True)
    dws_usr_create = models.IntegerField(blank=True, null=True)
    dws_create_date = models.DateTimeField(blank=True, null=True)
    dws_modif_date = models.DateTimeField(blank=True, null=True)
    dws_rio_analysis_time = models.IntegerField()
    dws_time_implement_briefcase = models.IntegerField(blank=True, null=True)
    dws_climate_scenario_briefcase = models.CharField(max_length=100, blank=True, null=True)
    dws_annual_investment_scenario = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    dws_time_implement_scenario = models.IntegerField(blank=True, null=True)
    dws_climate_scenario_scenario = models.CharField(max_length=100, blank=True, null=True)
    region_id = models.IntegerField(blank=True, null=True)
    ciudad_id = models.IntegerField(blank=True, null=True)
    dws_authorization_case = models.CharField(max_length=20)
    dws_id_parent = models.IntegerField(blank=True, null=True)
    dws_benefit_carbon_market = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_study_cases'
