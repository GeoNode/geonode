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

from django.views import View
from geonode.base.views import user_and_group_permission
import logging

from actstream.models import Action
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import DetailView
from django.db.models import Q

from geonode.decorators import view_decorator, superuser_only
from geonode.base.views import SimpleSelect2View

from dal import autocomplete

from . import forms
from . import models
from .models import GroupMember

logger = logging.getLogger(__name__)


class SetGroupDatasetPermission(View):
    def get(self, request):
        return user_and_group_permission(request, "groupprofile")

    def post(self, request):
        return user_and_group_permission(request, "groupprofile")


@view_decorator(superuser_only, subclass=True)
class GroupCategoryCreateView(CreateView):
    model = models.GroupCategory
    fields = ["name", "description"]


class GroupCategoryDetailView(DetailView):
    model = models.GroupCategory


class GroupCategoryUpdateView(UpdateView):
    model = models.GroupCategory
    fields = ["name", "description"]
    template_name_suffix = "_update_form"


group_category_create = GroupCategoryCreateView.as_view()
group_category_detail = GroupCategoryDetailView.as_view()
group_category_update = GroupCategoryUpdateView.as_view()


@superuser_only
def group_create(request):
    if request.method == "POST":
        form = forms.GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
            group.join(request.user, role="manager")
            return HttpResponseRedirect(reverse("group_detail", args=[group.slug]))
    else:
        form = forms.GroupForm()

    return render(request, "groups/group_create.html", context={"form": form})


@login_required
def group_update(request, slug):
    group = models.GroupProfile.objects.get(slug=slug)
    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = forms.GroupUpdateForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse("group_detail", args=[group.slug]))
    else:
        form = forms.GroupForm(instance=group)

    return render(
        request,
        "groups/group_update.html",
        context={
            "form": form,
            "group": group,
        },
    )


class GroupDetailView(ListView):
    """
    Mixes a detail view (the group) with a ListView (the members).
    """

    model = get_user_model()
    template_name = "groups/group_detail.html"
    paginate_by = None
    group = None

    def get_queryset(self):
        return self.group.member_queryset()

    def get(self, request, *args, **kwargs):
        self.group = get_object_or_404(models.GroupProfile, slug=kwargs.get("slug"))
        if self.group.access == "private" and not self.group.user_is_member(request.user):
            raise Http404
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.group
        context["maps"] = self.group.resources(resource_type="map")
        context["datasets"] = self.group.resources(resource_type="dataset")
        context["documents"] = self.group.resources(resource_type="document")
        context["is_member"] = self.group.user_is_member(self.request.user)
        context["is_manager"] = self.group.user_is_role(self.request.user, "manager")
        context["can_view"] = self.group.can_view(self.request.user)
        return context


def group_members(request, slug):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    if not group.can_view(request.user):
        raise Http404()
    is_manager = group.user_is_role(request.user, "manager")
    return render(
        request,
        "groups/group_members.html",
        context={
            "group": group,
            "members": group.member_queryset(),
            "member_form": forms.GroupMemberForm(request.user) if is_manager else None,
        },
    )


@require_POST
@login_required
def group_members_add(request, slug):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()
    form = forms.GroupMemberForm(request.user, request.POST)
    if form.is_valid():
        for user in form.cleaned_data["user_identifiers"]:
            try:
                group.join(user, role=GroupMember.MANAGER if form.cleaned_data["manager_role"] else GroupMember.MEMBER)
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
                return redirect("group_members", slug=group.slug)
    return redirect("group_detail", slug=group.slug)


@login_required
def group_member_remove(request, slug, username):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()
    else:
        GroupMember.objects.get(group=group, user=user).delete()
        return redirect("group_detail", slug=group.slug)


@login_required
def group_member_promote(request, slug, username):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()
    else:
        GroupMember.objects.get(group=group, user=user).promote()
        return redirect("group_members", slug=group.slug)


@login_required
def group_member_demote(request, slug, username):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()
    else:
        GroupMember.objects.get(group=group, user=user).demote()
        return redirect("group_members", slug=group.slug)


@require_POST
@login_required
def group_join(request, slug):
    group = get_object_or_404(models.GroupProfile, slug=slug)

    if group.access == "private":
        raise Http404()

    if group.user_is_member(request.user):
        return redirect("group_detail", slug=group.slug)
    else:
        group.join(request.user, role="member")
        return redirect("group_detail", slug=group.slug)


@login_required
def group_remove(request, slug):
    group = get_object_or_404(models.GroupProfile, slug=slug)
    if request.method == "GET":
        return render(request, "groups/group_remove.html", context={"group": group})
    if request.method == "POST":
        if not group.user_is_role(request.user, role="manager"):
            return HttpResponseForbidden()

        group.delete()
        return HttpResponseRedirect(reverse("group_list"))
    else:
        return HttpResponseNotAllowed()


class GroupActivityView(ListView):
    """
    Returns recent group activity.
    """

    template_name = "groups/activity.html"
    group = None

    def get_queryset(self):
        if not self.group:
            return None
        else:
            members = [(member.user.id) for member in self.group.member_queryset()]
            return Action.objects.filter(
                public=True,
                actor_object_id__in=members,
            )[:15]

    def get(self, request, *args, **kwargs):
        self.group = None
        group = get_object_or_404(models.GroupProfile, slug=kwargs.get("slug"))

        if not group.can_view(request.user):
            raise Http404()

        self.group = group

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        def getKey(action):
            return action.timestamp

        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        # Additional Filtered Lists Below
        action_list = []
        actions = Action.objects.filter(public=True, action_object_content_type__model="dataset")
        context["action_list_datasets"] = [
            action for action in actions if action.action_object and action.action_object.group == self.group.group
        ][:15]
        action_list.extend(context["action_list_datasets"])
        actions = Action.objects.filter(public=True, action_object_content_type__model="map")[:15]
        context["action_list_maps"] = [
            action for action in actions if action.action_object and action.action_object.group == self.group.group
        ][:15]
        action_list.extend(context["action_list_maps"])
        actions = Action.objects.filter(public=True, action_object_content_type__model="document")[:15]
        context["action_list_documents"] = [
            action for action in actions if action.action_object and action.action_object.group == self.group.group
        ][:15]
        action_list.extend(context["action_list_documents"])
        context["action_list"] = sorted(action_list, key=getKey, reverse=True)
        return context


class GroupProfileAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        request = self.request
        user = request.user
        qs = models.GroupProfile.objects.all()

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        if not user.is_authenticated or user.is_anonymous:
            return qs.exclude(access="private")
        elif not user.is_superuser:
            return qs.filter(Q(pk__in=user.group_list_all()) | ~Q(access="private"))
        return qs


class GroupCategoryAutocomplete(SimpleSelect2View):
    model = models.GroupCategory
    filter_arg = "name__icontains"
