"""
Views for the ``django-frequently`` application.

"""

import logging

from math import fsum

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView

from django_libs.views_mixins import AccessMixin

from .forms import EntryForm
from .models import Entry, EntryCategory, Feedback

logger = logging.getLogger(__name__)

class EntryMixin(object):
    """
    Mixin to handle and arrange the entry list.

    """

    def get_ordered_entries(self, queryset=False):
        """
        Custom ordering. First we get the average views and rating for
        the categories's entries. Second we created a rank by multiplying
        both. Last, we sort categories by this rank from top to bottom.

        Example:
        - Cat_1
            - Entry_1 (500 Views, Rating 2)
            - Entry_2 (200 Views, Rating -4)
            - Entry_3 (100 Views, Rating 3)
        - Cat_2
            - Entry_1 (200 Views, Rating 7)
            - Entry_2 (50 Views, Rating 2)

        Result:
        Cat_1 has a rank by: 88.88 (avg. views: 266.66, avg. rating: 0.33)
        Cat_2 has a rank by: 562.5 (avg. views: 125, avg. rating: 4.5)

        Cat_2 will be displayed at the top. The algorithm is quality-oriented,
        as you can see.

        """
        if queryset:
            self.queryset = queryset
        else:
            self.queryset = EntryCategory.objects.all()
        if self.queryset:
            for category in self.queryset:
                entries = category.get_entries()
                if entries:
                    amount_list = [e.amount_of_views for e in entries]
                    rating_list = [e.rating() for e in entries]
                    views_per_entry = fsum(amount_list) / len(amount_list)
                    rating_per_entry = fsum(rating_list) / len(rating_list)
                    category.last_rank = views_per_entry * rating_per_entry
                    category.save()
                else:
                    self.queryset = self.queryset.exclude(pk=category.pk)
            self.queryset = sorted(self.queryset, key=lambda c: c.last_rank,
                                   reverse=True)
        return self.queryset

    def post(self, request, *args, **kwargs):
        if "get_answer" in request.POST.keys():
            entry = Entry.objects.get(pk=request.POST['get_answer'])
            entry.last_view_date = timezone.now()
            entry.amount_of_views += 1
            entry.save()
            return TemplateResponse(
                request,
                'frequently/partials/answer.html',
                {
                    'entry': entry,
                    'rated_entries': self.request.session.get(
                        'rated_entries', False),
                    'request' : self.request
                },
            )
        self.feedback = Feedback()
        if "user_id" in request.POST.keys():
            try:
                user_id = int(request.POST.get('user_id'))
                try:
                    self.feedback.user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    pass
            except ValueError:
                pass
        if 'rating_id' in request.POST.keys() and request.is_ajax():
            try:
                entry_id = int(request.POST.get('rating_id').replace(
                    'rating_id', ''))
                try:
                    entry = Entry.objects.get(pk=entry_id)
                    return HttpResponse(entry.rating())
                except Entry.DoesNotExist:
                    raise Http404
            except ValueError:
                raise Http404
        for key in request.POST.keys():
            if key.startswith('up') or key.startswith('down'):
                try:
                    entry_id = int(key.replace('up', '').replace('down', ''))
                    try:
                        entry = Entry.objects.get(pk=entry_id)
                    except Entry.DoesNotExist:
                        raise Http404
                except ValueError:
                    raise Http404
                if not request.session.get('rated_entries', False):
                    request.session['rated_entries'] = []
                if entry.pk not in request.session['rated_entries']:
                    request.session['rated_entries'].append(entry.pk)
                    request.session.modified = True
                    self.feedback.entry = entry
                    if key.startswith('up'):
                        entry.upvotes += 1
                        self.feedback.validation = "P"
                    if key.startswith('down'):
                        entry.downvotes += 1
                        self.feedback.validation = "N"
                    entry.save()
                    self.feedback.save()
                    if request.is_ajax():
                        return TemplateResponse(
                            request,
                            'frequently/partials/feedback_form.html',
                            {
                                'feedback_entry': entry.pk,
                                'feedback': self.feedback,
                            },
                        )
            elif key.startswith('feedback'):
                try:
                    feedback_id = int(key.replace('feedback', ''))
                    try:
                        self.feedback = Feedback.objects.get(pk=feedback_id)
                    except Feedback.DoesNotExist:
                        raise Http404
                except ValueError:
                    raise Http404
                self.feedback.remark = request.POST.get("remark")
                self.feedback.save()
                if request.is_ajax():
                    return TemplateResponse(
                        request,
                        'frequently/partials/feedback_form.html',
                        {'feedback_send': True},
                    )
        return self.get(self, request, *args, **kwargs)


class EntryCategoryListView(AccessMixin, EntryMixin, ListView):
    """
    Main view to display all categories and their entries.

    """
    model = EntryCategory
    template_name = "frequently/entry_list.html"
    access_mixin_setting_name = 'FREQUENTLY_ALLOW_ANONYMOUS'
    logger.debug(template_name)

    def get_queryset(self):
        """
        Customized to get the ordered categories and entries from the Mixin.

        """
        self.queryset = super(EntryCategoryListView, self).get_queryset()
        return self.get_ordered_entries(self.queryset)


class EntryDetailView(AccessMixin, EntryMixin, DetailView):
    """
    Main view to display one entry.

    """
    model = Entry
    template_name = "frequently/entry_list.html"
    access_mixin_setting_name = 'FREQUENTLY_ALLOW_ANONYMOUS'

    def get_object(self, **kwargs):
        obj = super(EntryDetailView, self).get_object(**kwargs)
        obj.last_view_date = timezone.now()
        obj.amount_of_views += 1
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        context.update({
            'rated_entries': self.request.session.get('rated_entries', False),
            'object_list': self.get_ordered_entries(),
        })
        for key in self.request.POST.keys():  # pragma: nocover
            if key.startswith('down') or key.startswith('up'):
                context.update({
                    'feedback_entry': int(
                        key.replace('up', '').replace('down', '')),
                    'feedback': self.feedback,
                })
                return context
        return context


class EntryCreateView(AccessMixin, CreateView):
    """
    Feedback submission form view.

    """
    model = Entry
    form_class = EntryForm
    access_mixin_setting_name = 'FREQUENTLY_ALLOW_ANONYMOUS'

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _(
            'Your question has been posted. Our team will review it as soon'
            ' as possible and get back to you with an answer.'))
        return super(EntryCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(EntryCreateView, self).get_form_kwargs()
        if self.request.user.is_authenticated:
            kwargs.update({
                'owner': self.request.user,
            })
        return kwargs

    def get_success_url(self):
        return reverse('frequently_list')
