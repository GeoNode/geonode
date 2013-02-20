# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.documents',),
}

urlpatterns = patterns('geonode.documents.views',
    url(r'^$', 'document_list', name='documents_browse'),
    url(r'^tag/(?P<slug>[-\w]+?)/$', 'document_tag', name='document_browse_tag'),
    url(r'^(?P<docid>\d+)/?$', 'document_detail', name='document_detail'),
    url(r'^upload/?$', 'document_upload', name='document_upload'),
    url(r'^search/?$', 'document_search_page', name='document_search_page'),
    url(r'^search/api/?$', 'documents_search', name='documents_search_api'),
    url(r'^(?P<docid>\d+)/ajax-permissions$', 'ajax_document_permissions', name='ajax_document_permissions'),
    url(r'^(?P<docid>\d+)/metadata$', 'document_metadata', name='document_metadata'),
    url(r'^resources/search/api/?$', 'resources_search', name='resources_search'),
)