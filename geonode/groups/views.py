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
from actstream.views import user
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType


from actstream.models import Action
from guardian.models import UserObjectPermission
from notify.signals import notify

from geonode.groups.forms import GroupInviteForm, GroupForm, GroupUpdateForm, GroupMemberForm
from geonode.groups.models import GroupProfile, GroupInvitation, GroupMember
from geonode.people.models import Profile
from geonode.base.libraries.decorators import superuser_check
from geonode.layers.models import Layer
from geonode.groups.models import QuestionAnswer
from geonode.groups.forms import QuestionForm, AnsewerForm
from geonode.settings import ANONYMOUS_USER_ID
from geonode import settings

@login_required
@user_passes_test(superuser_check)
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
            user = Profile.objects.get(id=request.POST['admin'])
            group.join(user, role="manager")
            return HttpResponseRedirect(
                reverse(
                    "group_detail",
                    args=[
                        group.slug]))
    else:
        form = GroupForm()

    return render_to_response("groups/group_create.html", {
        "form": form,
    }, context_instance=RequestContext(request))


@login_required
def group_update(request, slug):
    group = GroupProfile.objects.get(slug=slug)
    if not group.user_is_role(request.user, role="manager") and not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
            if request.POST['admin']:
                user = Profile.objects.get(id=request.POST['admin'])
                group.join(user, role="manager")
            return HttpResponseRedirect(
                reverse(
                    "group_detail",
                    args=[
                        group.slug]))
    else:
        form = GroupForm(instance=group)

    return render_to_response("groups/group_update.html", {
        "form": form,
        "group": group,
    }, context_instance=RequestContext(request))


class GroupDetailView(ListView):

    """
    Mixes a detail view (the group) with a ListView (the members).
    """

    model = get_user_model()
    template_name = "groups/group_detail.html"
    paginate_by = None
    group = None

    def get_queryset(self):
        return self.group.member_queryset().filter(user__is_active=True)

    def get(self, request, *args, **kwargs):
        self.group = get_object_or_404(GroupProfile, slug=kwargs.get('slug'))
        return super(GroupDetailView, self).get(request, *args, **kwargs)

    #@jahangir091
    def user_can_invite(self):
        is_member = self.group.user_is_member(self.request.user)
        is_manager = self.group.user_is_role(self.request.user, "manager")
        try:
            user_invitation = UserInvitationModel.objects.get(user=self.request.user, group=self.group)
        except:
            state = 'free'
        else:
            state = user_invitation.state

        if not is_member and not is_manager and state == 'free':
            return True
        else:
            return False

    def user_invitation_pending(self):
        try:
            user_invitation = UserInvitationModel.objects.get(user=self.request.user, group=self.group)
        except:
            state = 'free'
        else:
            state = user_invitation.state
        if state == 'pending':
            return True
        else:
            return False
#end

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        context['object'] = self.group
        context['maps'] = self.group.resources(resource_type='map')
        context['layers'] = self.group.resources(resource_type='layer')
        context['is_member'] = self.group.user_is_member(self.request.user)
        context['is_manager'] = self.group.user_is_role(
            self.request.user,
            "manager")
        context['can_view'] = self.group.can_view(self.request.user)
        context['can_send_request'] = self.user_can_invite()
        context['pending_request'] = self.user_invitation_pending()
        return context


def group_members(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)
    ctx = {}

    if not group.can_view(request.user):
        raise Http404()

    if group.access in [
            "public-invite",
            "private"] and group.user_is_role(
            request.user,
            "manager") or request.user.is_superuser:
        ctx["invite_form"] = GroupInviteForm()

    if group.user_is_role(request.user, "manager") or request.user.is_superuser:
        ctx["member_form"] = GroupMemberForm()

    ctx.update({
        "group": group,
        "members": group.member_queryset().filter(user__is_active=True),
        "is_member": group.user_is_member(request.user),
        "is_manager": group.user_is_role(request.user, "manager"),
    })
    ctx = RequestContext(request, ctx)
    return render_to_response("groups/group_members.html", ctx)


@require_POST
@login_required
def group_members_add(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)

    if not group.user_is_role(request.user, role="manager") and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = GroupMemberForm(request.POST)

    if form.is_valid():
        role = form.cleaned_data["role"]
        for user in form.cleaned_data["user_identifiers"]:
            try:
                group_member = GroupMember.objects.get(group=group, user=user)
            except GroupMember.DoesNotExist:
                pass
            else:
                if group_member.role == 'manager':
                    permissions = UserObjectPermission.objects.filter(user=user)
                    for layer in Layer.objects.filter(group=group):
                        if layer.owner != user:
                            permissions.filter(object_pk=layer.pk).delete()
            group.join(user, role=role)
        if role == 'manager':
            for layer in Layer.objects.filter(group=group):
                layer.set_managers_permissions()

    return redirect("group_detail", slug=group.slug)


@login_required
def group_member_remove(request, slug, username):
    group = get_object_or_404(GroupProfile, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if not group.user_is_role(request.user, role="manager") and not request.user.is_superuser:
        return HttpResponseForbidden()
    else:
        group_member = GroupMember.objects.get(group=group, user=user)
        if group_member.role == 'manager':
            permissions = UserObjectPermission.objects.filter(user=user)
            for layer in Layer.objects.filter(group=group):
                if layer.owner != user:
                    permissions.filter(object_pk=layer.pk).delete()
        group_member.delete()
        user.groups.remove(group.group)
        return redirect("group_detail", slug=group.slug)


@require_POST
@login_required
def group_join(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)

    if group.access == "private":
        raise Http404()

    if group.user_is_member(request.user):
        return redirect("group_detail", slug=group.slug)
    else:
        group.join(request.user, role="member")
        return redirect("group_detail", slug=group.slug)


@require_POST
def group_invite(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)

    if not group.can_invite(request.user):
        raise Http404()

    form = GroupInviteForm(request.POST)

    if form.is_valid():
        for user in form.cleaned_data["invite_user_identifiers"].split("\n"):
            group.invite(
                user,
                request.user,
                role=form.cleaned_data["invite_role"],
            )

            # notify user that he/she is invited by the group
            try:
                requested_user = Profile.objects.get(email=user)
            except:
                pass
            else:
                notify.send(request.user, recipient=requested_user, actor=request.user,
                verb='invited you to join')

    return redirect("group_members", slug=group.slug)


@login_required
def group_invite_response(request, token):
    invite = get_object_or_404(GroupInvitation, token=token)
    ctx = {"invite": invite}

    if request.user != invite.user:
        redirect("group_detail", slug=invite.group.slug)

    if request.method == "POST":
        if "accept" in request.POST:
            invite.accept(request.user)

        if "decline" in request.POST:
            invite.decline()

        return redirect("group_detail", slug=invite.group.slug)
    else:
        ctx = RequestContext(request, ctx)
        return render_to_response("groups/group_invite_response.html", ctx)


@login_required
def group_remove(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)
    if request.method == 'GET':
        return render_to_response(
            "groups/group_remove.html", RequestContext(request, {"group": group}))
    if request.method == 'POST':

        if  request.user.is_superuser:
            group.delete()
            return HttpResponseRedirect(reverse("group_list"))
        else:
            return HttpResponseForbidden()

       
    else:
        return HttpResponseNotAllowed()


class GroupActivityView(ListView):
    """
    Returns recent group activity.
    """

    template_name = 'groups/activity.html'
    group = None
    paginate_by = 15

    def get_queryset(self):
        if not self.group:
            return None
        else:
            members = ([(member.user.id) for member in self.group.member_queryset()])
            return Action.objects.filter(public=True, actor_object_id__in=members, )

    def get(self, request, *args, **kwargs):
        self.group = None
        group = get_object_or_404(GroupProfile, slug=kwargs.get('slug'))

        if not group.can_view(request.user):
            raise Http404()

        self.group = group

        return super(GroupActivityView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupActivityView, self).get_context_data(**kwargs)
        # for filtering contenttype as ContentType model in 1.8.7 does not contain name field
        from django.contrib.contenttypes.models import ContentType
        contenttypes = ContentType.objects.all()
        for ct in contenttypes:
            if ct.name == 'layer':
                ct_layer_id = ct.id
            if ct.name == 'map':
                ct_map_id = ct.id
            if ct.name == 'comment':
                ct_comment_id = ct.id
        context['group'] = self.group
        # Additional Filtered Lists Below
        members = ([(member.user.id) for member in self.group.member_queryset()])
        context['action_list_layers'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__model='layer')[:15]
        context['action_list_maps'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__model='map')[:15]
        context['action_list_comments'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__model='comment')[:15]
        return context


#@jahangir091
def question_answer_list_view(request, slug):

    """
    This view returns wuestions and answers for an organization.
    """

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        group = get_object_or_404(GroupProfile, slug=slug)
        if form.is_valid():
            question = QuestionAnswer()
            asked_question = form.cleaned_data["question"]
            if request.user.is_authenticated():
                questioner = request.user
            else:
                questioner = Profile.objects.get(id=ANONYMOUS_USER_ID)
            question.question = asked_question
            question.questioner = questioner
            question.group = group
            question.save()
            return redirect("group_detail", slug=slug)
        else:
            return redirect("group_detail", slug=slug)

    else:
        group = get_object_or_404(GroupProfile, slug=slug)
        context_dict = {
            'form': QuestionForm,
            'slug': slug,
            'answerform': AnsewerForm,
            'group': group
        }
        managers = group.get_managers()
        if request.user in managers:
            context_dict['question_list'] = QuestionAnswer.objects.filter(group=group)
        else:
            context_dict['question_list'] = QuestionAnswer.objects.filter(group=group, answered=True)
        return render_to_response(
            "groups/question_answer.html",
            RequestContext(request, context_dict))


@login_required
def answer_view(request, slug, question_pk):
    """
    This view is for answering an asked question. Only managers can answer a question.
    """
    if request.method == 'POST':
        form = AnsewerForm(request.POST)
        respondent = request.user
        group = get_object_or_404(GroupProfile, slug=slug)
        managers = group.get_managers()
        if form.is_valid() and respondent in managers:
            question = get_object_or_404(QuestionAnswer, pk=question_pk)
            answer = form.cleaned_data["answer"]
            question.answer = answer
            question.group = group
            question.respondent = respondent
            question.answered = True
            question.save()
            return redirect("group_detail", slug=slug)
        else:
            return redirect("group_detail", slug=slug)
    else:
        return redirect("group_detail", slug=slug)


@login_required
def delete_question(request, slug, question_pk):
    """
    This view is for deleting a question with answer.
    """
    if request.method == 'POST':
        group = get_object_or_404(GroupProfile, slug=slug)
        managers = group.get_managers()
        if request.user in managers:
            question = get_object_or_404(QuestionAnswer, pk=question_pk)
            question.delete()
            return redirect("group_detail", slug=slug)
        else:
            return redirect("group_detail", slug=slug)
    else:
        return redirect("group_detail", slug=slug)


class AnswerUpdate(UpdateView):
    """
    This view is for updating an existing answer
    """
    model = QuestionAnswer
    form_class = AnsewerForm

    def get_object(self):
        return QuestionAnswer.objects.get(pk=self.kwargs['answer_pk'])

    def get_success_url(self):
        return reverse('group_detail', kwargs={'slug': self.kwargs['slug']})


from models import UserInvitationModel
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.shortcuts import render
@require_POST
@login_required
def userinvitation(request, slug):
    """

    """
    if request.method == 'POST':
        group = get_object_or_404(GroupProfile, slug=slug)
        if group.access == "public-invite":
            user_invitation = UserInvitationModel(user=request.user, group=group, state='pending')
            user_invitation.save()
            managers = list(group.get_managers())
            notify.send(request.user, recipient_list=managers, actor=request.user,
                    target=group, verb='requested to join {}'.format(group.title))
            return redirect("group_detail", slug=slug)


class UserInvitationListView(ListView):
    model = UserInvitationModel
    template_name = 'groups/user_invitation_list.html'

    def get(self, request, slug):
        group = get_object_or_404(GroupProfile, slug=slug)
        pending_invitations = UserInvitationModel.objects.filter(group=group, state='pending').order_by('date_updated')
        slug = slug
        if request.user not in group.get_managers() and not request.user.is_superuser:
            return HttpResponse(
                    loader.render_to_string(
                        '401.html', RequestContext(
                        request, {
                        'error_message': _("You are not allowed to perform this job.")})), status=403)
        else:
            # return HttpResponse(self.get_context_data())
            return render(request, self.template_name, {'pending_invitations': pending_invitations, 'slug':slug})

    # def get_context_data(self, *args, **kwargs):
    #     context = super(ListView, self).get_context_data(*args, **kwargs)
    #     slug = self.kwargs['slug']
    #     group = get_object_or_404(GroupProfile, slug=slug)
    #     context['pending_invitations'] = UserInvitationModel.objects.filter(group=group, state='pending').order_by('date_updated')
    #     context['slug'] = slug
    #
    #     return context


class UserInvitationDeleteView(DeleteView):
    """

    """
    # template_name = 'slider_image_delete.html'
    model = UserInvitationModel

    def get_success_url(self):
        return reverse('user-invitation-list', kwargs={'slug': self.kwargs['slug']})

    def get_object(self):
        slug = self.kwargs['slug']
        group = get_object_or_404(GroupProfile, slug=slug)
        return UserInvitationModel.objects.get(pk=self.kwargs['invitation_pk'])

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)



@login_required
def accept_user_invitation(request, slug, user_pk):
    
    group = get_object_or_404(GroupProfile, slug=slug)
    user = get_object_or_404(Profile, pk=user_pk)
    if request.method == 'POST':

        if not group.user_is_role(request.user, role="manager") and not request.user.is_superuser:
            return HttpResponseForbidden()

        group.join(user, role='member')
        user_invitation = UserInvitationModel.objects.get(group=group, user=user)
        user_invitation.state='connected'
        user_invitation.save()
        return redirect("user-invitation-list", slug=slug)

    else:
        return redirect("user-invitation-list", slug=slug)

#end