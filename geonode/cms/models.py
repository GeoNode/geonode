from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class SectionManagementTable(models.Model):
    """
    This model is for managing sections in index page. Only super-admin can
    manage this.
    """

    title = models.CharField(max_length=50, default='')
    slug = models.SlugField(max_length=100, null=True, blank=True)
    is_visible = models.BooleanField(default=True)
    should_update = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.slug


class SliderImages(models.Model):
    """
    This model is for slider images management
    """
    title = models.CharField(max_length=100)
    descripton = models.TextField(max_length=300)
    is_active = models.BooleanField(default=False)
    image = models.ImageField(upload_to="index_page/slider_images")
    logo_url = models.URLField(blank=True, null=True)
    section = models.ForeignKey('SectionManagementTable', null=True, blank=True)
    connect_section = models.ForeignKey('SectionManagementTable', related_name='linksection', null=True, blank=True, verbose_name=_('Connect section'))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class IndexPageImagesModel(models.Model):
    """
    This model is for landing page images management
    """
    title = models.CharField(max_length=100, null=True, blank=True)
    descripton = models.TextField(max_length=300, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    image = models.ImageField()
    section = models.ForeignKey('SectionManagementTable', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class SectionManagementModel(models.Model):
    """
    This model is for managing sections in index page. Only super-admin can
    manage this.
    """
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    section_sub_title = models.CharField(max_length=500)
    description = models.TextField(max_length=1000, blank=True, null=True)
    image1 = models.ImageField(blank=True, null=True, upload_to="index_page/section_images")
    image2 = models.ImageField(blank=True, null=True, upload_to="index_page/section_images")
    image3 = models.ImageField(blank=True, null=True, upload_to="index_page/section_images")
    image4 = models.ImageField(blank=True, null=True, upload_to="index_page/section_images")
    image5 = models.ImageField(blank=True, null=True, upload_to="index_page/section_images")
    is_active = models.BooleanField(default=True)
    background_image = models.ImageField(null=True, blank=True)
    background_color = models.CharField(max_length=20, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class FooterSectionDescriptions(models.Model):
    """
    This model keeps descriptons for every options in footer section
    """
    title = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=100, null=True, blank=True)
    description = models.TextField(default='this is good', blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)