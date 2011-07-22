from django.utils.translation import ugettext as _

from django.db import models

from django.contrib.auth.models import User
from model_utils.managers import InheritanceManager

# Create your models here.
class Datastory(models.Model):
	"""
	Model to store a data story, a step-by-step walk through data exploration.
	"""
	title = models.CharField(_('Title'), max_length=100)
	slug  = models.SlugField(max_length=100)
	abstract = models.TextField(_('Abstract'), blank=True, null=True)
	
	# FIXME: allow ordering of pages
	pages = models.ManyToManyField('Page')
	
	owner = models.ForeignKey(User, verbose_name=_('owner'))
	
	last_modified = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return '%s by %s' % (self.title, (self.owner.username if self.owner else "<Anonymous>"))
		
	class Meta:
		unique_together = (('title', 'owner'),)
		verbose_name_plural = "Datastories"
		
class Page(models.Model):
	"""
	A page is part of a data story.
	Default page is a Textpage.
	"""
	title = models.CharField(_('Title'), max_length=100)
	abstract = models.TextField(_('Abstract'), blank=True, null=True)
	
	owner = models.ForeignKey(User, verbose_name=_('owner'))
	
	last_modified = models.DateTimeField(auto_now_add=True)
	
	objects = InheritanceManager()
	
	def __unicode__(self):
		return '%s by %s' % (self.title, (self.owner.username if self.owner else "<Anonymous>"))
	
		
class Visualizationpage(Page):
	"""
	A page showing a Weave visualization.
	"""
	visualization = models.ForeignKey('weave.Visualization')
	
	@models.permalink
	def get_absolute_url(self):
		return ('geonode.weave.views.edit', None, { 'visid': self.visualization.id, })
	
class Mappage(Page):
	"""
	A page showing a Map.
	"""
	map = models.ForeignKey('maps.Map')
	
	@models.permalink
	def get_absolute_url(self):
		return ('geonode.maps.views.view', None, { 'mapid': self.map.id, })
