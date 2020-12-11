"""Models for the ``frequently`` app."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextField


@python_2_unicode_compatible
class EntryCategory(models.Model):
    """
    Model to gather answers in topic groups.

    :name: Name or title of the category.
    :nombre: Nombre o titulo de la categoria
    :slug: Slugified name of the category.
    :fixed_position: Set a position to avoid ordering by views.
    :last_rank: Last rank calculated at the category list view.

    """
    name = models.CharField(
        _('Name'),
        max_length=100,        
    )

    name_es = models.CharField(
        _('Name in spanish'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Nombre in spanish'))

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug'),
    )

    fixed_position = models.PositiveIntegerField(
        verbose_name=_('Fixed position'),
        blank=True, null=True,
    )

    last_rank = models.FloatField(
        default=0,
        verbose_name=_('Last calculated rank'),
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['fixed_position', 'name']

    def get_entries(self):
        return self.entries.filter(published=True).annotate(
            null_position=models.Count('fixed_position')).order_by(
            '-null_position', 'fixed_position', '-amount_of_views')


@python_2_unicode_compatible
class Entry(models.Model):
    """
    Entry model. Can be added to a category group.

    :owner: Foreign key to django auth user.
    :category: Entry can appear in different categories.
    :question: Title or question of the entry.
    :slug: Slugified question of the category.
    :answer: Answer or content of the entry.
    :creation_date: Date of entry creation.
    :last_view_date: Date of the last click/view.
    :amount_of_views: Amount of views/clicks.
    :fixed_position: Set a position to avoid ordering by views.
    :upvotes: Positive vote amount for this entry.
    :downvotes: Negative vote amount for this entry.
    :published: Shows/hides entries.

    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Owner'),
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    category = models.ManyToManyField(
        EntryCategory,
        verbose_name=_('Category'),
        related_name='entries',
    )

    question = models.TextField(
        max_length=2000,
        verbose_name=_('Question'),
    )

    question_es = models.CharField(
        _('Question Spanish'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Question Spanish'))

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_('Slug'),
    )

    answer = RichTextField(
        verbose_name=_('Answer'),
        blank=True,
    )

    answer_es = RichTextField(
        _('Answer Spanish'),
        blank=True,
    )

    creation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Creation date'),
    )

    last_view_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date of last view'),
    )

    amount_of_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Amount of views'),
    )

    fixed_position = models.PositiveIntegerField(
        verbose_name=_('Fixed position'),
        blank=True, null=True,
    )

    upvotes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Upvotes'),
    )

    downvotes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Downvotes'),
    )

    published = models.BooleanField(
        default=False,
        verbose_name=_('is published'),
    )

    submitted_by = models.EmailField(
        max_length=100,
        verbose_name=_('Submitted by'),
        blank=True,
    )

    class Meta:
        ordering = ['fixed_position', 'question']

    def __str__(self):
        return self.question

    def get_absolute_url(self):
        return reverse('frequently_entry_detail', kwargs={'slug': self.slug, })

    def rating(self):
        return self.upvotes - self.downvotes


@python_2_unicode_compatible
class Feedback(models.Model):
    """
    Feedback model to save and store user feedback related to an entry.

    This model can also be used to store general feedback.

    :user: Stores user if authenticated at submission.
    :entry: Related entry.
    :remark: User's feedback text.
    :submission_date: Date of feedback creation.
    :validation: Is this a positive or negative feedback.

    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('User'),
        blank=True, null=True,
        on_delete=models.SET_NULL,
    )

    entry = models.ForeignKey(
        Entry,
        verbose_name=_('Related entry'),
        blank=True, null=True,
        on_delete=models.CASCADE,
    )

    remark = models.TextField(
        verbose_name=_('Remark'),
        blank=True,
    )

    submission_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Submission date'),
    )

    validation = models.CharField(
        max_length=1,
        choices=(('P', _('Positive')), ('N', _('Negative'))),
        verbose_name=_('Validation mood'),
    )

    def __str__(self):
        return "%s - %s" % (self.entry, self.submission_date)


is_ready = getattr(settings, 'FREQUENTLY_READY_FOR_V1', True)
if not is_ready:  # pragma: nocover
    raise Exception(
        'ERROR: There are backwards incompatible changes in django-frequently.'
        ' Please visit http://github.com/bitmazk/cmsplugin-frequently/ to'
        ' find out more')
