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

from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from .views import GroupDetailView, GroupActivityView, AnswerUpdate, UserInvitationListView, UserInvitationDeleteView
urlpatterns = patterns('geonode.groups.views',
                       url(r'^$', TemplateView.as_view(template_name='groups/group_list.html'), name="group_list"),
                       url(r'^create/$', 'group_create', name="group_create"),
                       url(r'^group/(?P<slug>[-\w]+)/$', GroupDetailView.as_view(), name='group_detail'),
                       url(r'^group/(?P<slug>[-\w]+)/update/$', 'group_update', name='group_update'),
                       url(r'^group/(?P<slug>[-\w]+)/members/$', 'group_members', name='group_members'),
                       url(r'^group/(?P<slug>[-\w]+)/invite/$', 'group_invite', name='group_invite'),
                       url(r'^group/(?P<slug>[-\w]+)/members_add/$', 'group_members_add', name='group_members_add'),
                       url(r'^group/(?P<slug>[-\w]+)/member_remove/(?P<username>.+)$', 'group_member_remove',
                           name='group_member_remove'),
                       url(r'^group/(?P<slug>[-\w]+)/remove/$', 'group_remove', name='group_remove'),
                       url(r'^group/(?P<slug>[-\w]+)/join/$', 'group_join', name='group_join'),
                       url(r'^group/[-\w]+/invite/(?P<token>[\w]{40})/$', 'group_invite_response',
                           name='group_invite_response'),
                       url(r'^group/(?P<slug>[-\w]+)/activity/$', GroupActivityView.as_view(), name='group_activity'),


		       #@jahangir091
                       # group detail page, question and answer
                       url(r'^group/(?P<slug>[-\w]+)/questionlist/$', 'question_answer_list_view', name='question-answer-list'),
                       url(r'^group/(?P<slug>[-\w]+)/(?P<question_pk>[0-9]+)/answer/$', 'answer_view', name='create-answer'),
                       url(r'^group/(?P<slug>[-\w]+)/(?P<question_pk>[0-9]+)/delete/$', 'delete_question', name='delete-question'),

                       url(r'^group/(?P<slug>[-\w]+)/(?P<answer_pk>[0-9]+)/update$', AnswerUpdate.as_view(), name='answer-update'),


                       url(r'^group/(?P<slug>[-\w]+)/user-invitation$', 'userinvitation', name='user-invitation'),
                       url(r'^group/(?P<slug>[-\w]+)/user-invitations/list$', UserInvitationListView.as_view(), name='user-invitation-list'),
                       url(r'^group/(?P<slug>[-\w]+)/user-invitations/(?P<invitation_pk>[0-9]+)/delete$', UserInvitationDeleteView.as_view(), name='user-invitation-delete'),
                       url(r'^group/(?P<slug>[-\w]+)/user-invitations/(?P<user_pk>[0-9]+)/accept$', 'accept_user_invitation', name='user-invitation-accept'),
		       #end






                       )
