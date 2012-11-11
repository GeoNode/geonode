from django.conf.urls.defaults import patterns, url
from django.views.i18n import javascript_catalog

urlpatterns = patterns('geonode.documents.views',
	url(r'^$','documents', name='documents_browse'),
	url(r'^(?P<docid>\d+)/?$', 'documentdetail', name='document_detail'),
	url(r'^upload/?$', 'upload_document', name='document-upload'),
	(r'^newmap$', 'newmaptpl'),
	url(r'^search/?$', 'documents_search_page', name='documents_search'),
    url(r'^search/api/?$', 'documents_search', name='documents_search_api'),
    url(r'^(?P<docid>\d+)/ajax-permissions$', 'ajax_document_permissions', name='ajax_document_permissions'),
    url(r'^(?P<docid>\d+)/metadata$', 'document_metadata', name='document_metadata'),
    url(r'^resources/search/api/?$', 'resources_search', name='resources_search'),
)