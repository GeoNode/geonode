# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from tastypie.api import Api

from .api import TagResource, TopicCategoryResource, ProfileResource, \
    GroupResource, RegionResource, OwnersResource, UserOrganizationList, LayerUpload, MakeFeatured, MesseagesUnread, \
        UndockResources, FavoriteUnfavoriteResources, OsmOgrInfo, LayerSourceServer, LayersWithFavoriteAndDoocked, \
    MapsWithFavoriteAndDoocked, GroupsWithFavoriteAndDoocked, DocumentsWithFavoriteAndDoocked, UserNotifications, \
    ViewNotificationTimeSaving, ThesaurusKeywordResource, AccessTokenApi

from .resourcebase_api import LayerResource, MapResource, DocumentResource, \
    ResourceBaseResource, FeaturedResourceBaseResource, LayerResourceWithFavorite, MapResourceWithFavorite, \
    DocumentResourceWithFavorite, GroupsResourceWithFavorite, GroupActivity, WorkSpaceLayerApi, WorkSpaceDocumentApi, \
    WorkSpaceMapApi



api = Api(api_name='api')

api.register(LayerResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(ProfileResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(RegionResource())
api.register(TopicCategoryResource())
api.register(GroupResource())
api.register(FeaturedResourceBaseResource())
api.register(OwnersResource())
api.register(ThesaurusKeywordResource())



#@jahangir091
# new apis
api.register(UserOrganizationList())  # method=get. example: api/user-organization-list/?user__id=7
api.register(LayerUpload())
api.register(MakeFeatured())
api.register(MesseagesUnread()) # api for unread messages for an user
api.register(UndockResources())
api.register(FavoriteUnfavoriteResources())
api.register(OsmOgrInfo())
api.register(LayerSourceServer())
api.register(LayersWithFavoriteAndDoocked())
api.register(MapsWithFavoriteAndDoocked())
api.register(GroupsWithFavoriteAndDoocked())
api.register(DocumentsWithFavoriteAndDoocked())
api.register(LayerResourceWithFavorite())
api.register(MapResourceWithFavorite())
api.register(DocumentResourceWithFavorite())
api.register(GroupsResourceWithFavorite())
api.register(GroupActivity())

api.register(UserNotifications())

api.register(ViewNotificationTimeSaving())





# admin and member workspace apis
# for retrrieving layers, maps and documents

#Layers for member workspace
api.register(WorkSpaceLayerApi())
api.register(WorkSpaceMapApi())
api.register(WorkSpaceDocumentApi())
#end

#get token api
api.register(AccessTokenApi())
