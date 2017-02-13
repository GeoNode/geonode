import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib.auth.decorators import permission_required

from announcements import signals
from announcements.forms import AnnouncementForm
from announcements.models import Announcement


@require_POST
def dismiss(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if announcement.dismissal_type == Announcement.DISMISSAL_SESSION:
        excluded = request.session.get("excluded_announcements", set())
        excluded.add(announcement.pk)
        request.session["excluded_announcements"] = excluded
        status = 200
    elif announcement.dismissal_type == Announcement.DISMISSAL_PERMANENT and \
         request.user.is_authenticated():
        announcement.dismissals.create(user=request.user)
        status = 200
    else:
        status = 409
    return HttpResponse(json.dumps({}), status=status, mimetype="application/json")


def detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    return TemplateResponse(request, "announcements/detail.html", {
        "announcement": announcement
    })


class ProtectedView(View):
    
    @method_decorator(permission_required("announcements.can_manage"))
    def dispatch(self, *args, **kwargs):
        return super(ProtectedView, self).dispatch(*args, **kwargs)


class CreateAnnouncementView(ProtectedView, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        signals.announcement_created.send(
            sender=self.object,
            announcement=self.object,
            request=self.request
        )
        return super(CreateAnnouncementView, self).form_valid(form)
    
    def get_success_url(self):
        return reverse("announcements_list")


class UpdateAnnouncementView(ProtectedView, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    
    def form_valid(self, form):
        response = super(UpdateAnnouncementView, self).form_valid(form)
        signals.announcement_updated.send(
            sender=self.object,
            announcement=self.object,
            request=self.request
        )
        return response
    
    def get_success_url(self):
        return reverse("announcements_list")


class DeleteAnnouncementView(ProtectedView, DeleteView):
    model = Announcement
    
    def form_valid(self, form):
        response = super(DeleteAnnouncementView, self).form_valid(form)
        signals.announcement_deleted.send(
            sender=self.object,
            announcement=self.object,
            request=self.request
        )
        return response
    
    def get_success_url(self):
        return reverse("announcements_list")


class AnnouncementListView(ProtectedView, ListView):
    model = Announcement
    queryset = Announcement.objects.all().order_by("-creation_date")
    paginate_by = 50
