"""
Forms for the ``django-frequently`` application.

"""
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from .models import Entry


class EntryForm(forms.ModelForm):
    """
    Form to submit a new entry.

    """
    class Meta:
        model = Entry
        fields = ('question', 'submitted_by', )

    def __init__(self, owner=None, *args, **kwargs):
        self.owner = owner
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['submitted_by'].label = _('Email')
        self.fields['submitted_by'].required = True
        if not getattr(settings, 'FREQUENTLY_REQUIRE_EMAIL', True):
            self.fields.pop('submitted_by')

    def save(self, *args, **kwargs):
        # Create unique slug
        self.instance.slug = slugify(self.cleaned_data['question'])[:100]
        while True:
            try:
                Entry.objects.get(slug=self.instance.slug)
            except Entry.DoesNotExist:
                break
            else:
                self.instance.slug = '{0}-1'.format(self.instance.slug)

        submitted_by = self.cleaned_data.get('submitted_by')
        if self.owner:
            self.instance.owner = self.owner
            if not getattr(settings, 'FREQUENTLY_REQUIRE_EMAIL', True):
                self.instance.submitted_by = self.owner.email
                submitted_by = self.instance.submitted_by

        obj = super(EntryForm, self).save(*args, **kwargs)
        try:
            settings.FREQUENTLY_RECIPIENTS
            ctx_dict = {
                'submitted_by': submitted_by,
                'question': self.cleaned_data['question'],
                'instance': obj,
            }
            subject = render_to_string(
                'frequently/email/new_question_subject.txt', ctx_dict)
            subject = ''.join(subject.splitlines())
            message = render_to_string(
                'frequently/email/new_question_body.txt', ctx_dict)
            to = [item[1] for item in settings.FREQUENTLY_RECIPIENTS]
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, to)
        except AttributeError:
            pass
        return obj
