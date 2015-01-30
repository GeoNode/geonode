from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView

from actstream.models import Action

from geonode.groups.forms import GroupInviteForm, GroupForm, GroupUpdateForm, GroupMemberForm
from geonode.groups.models import GroupProfile, GroupInvitation, GroupMember


@login_required
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
            group.join(request.user, role="manager")
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
    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            group = form.save(commit=False)
            group.save()
            form.save_m2m()
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
        return self.group.member_queryset()

    def get(self, request, *args, **kwargs):
        self.group = get_object_or_404(GroupProfile, slug=kwargs.get('slug'))
        return super(GroupDetailView, self).get(request, *args, **kwargs)

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
            "manager"):
        ctx["invite_form"] = GroupInviteForm()

    if group.user_is_role(request.user, "manager"):
        ctx["member_form"] = GroupMemberForm()

    ctx.update({
        "group": group,
        "members": group.member_queryset(),
        "is_member": group.user_is_member(request.user),
        "is_manager": group.user_is_role(request.user, "manager"),
    })
    ctx = RequestContext(request, ctx)
    return render_to_response("groups/group_members.html", ctx)


@require_POST
@login_required
def group_members_add(request, slug):
    group = get_object_or_404(GroupProfile, slug=slug)

    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()

    form = GroupMemberForm(request.POST)

    if form.is_valid():
        role = form.cleaned_data["role"]
        for user in form.cleaned_data["user_identifiers"]:
            group.join(user, role=role)

    return redirect("group_detail", slug=group.slug)


@login_required
def group_member_remove(request, slug, username):
    group = get_object_or_404(GroupProfile, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if not group.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()
    else:
        GroupMember.objects.get(group=group, user=user).delete()
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
                role=form.cleaned_data["invite_role"])

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

    template_name = 'groups/activity.html'
    group = None

    def get_queryset(self):
        if not self.group:
            return None
        else:
            members = ([(member.user.id) for member in self.group.member_queryset()])
            return Action.objects.filter(public=True, actor_object_id__in=members, )[:15]

    def get(self, request, *args, **kwargs):
        self.group = None
        group = get_object_or_404(GroupProfile, slug=kwargs.get('slug'))

        if not group.can_view(request.user):
            raise Http404()

        self.group = group

        return super(GroupActivityView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupActivityView, self).get_context_data(**kwargs)
        context['group'] = self.group
        # Additional Filtered Lists Below
        members = ([(member.user.id) for member in self.group.member_queryset()])
        context['action_list_layers'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__name='layer')[:15]
        context['action_list_maps'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__name='map')[:15]
        context['action_list_comments'] = Action.objects.filter(
            public=True,
            actor_object_id__in=members,
            action_object_content_type__name='comment')[:15]
        return context
