from django.utils.translation import ugettext as _

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, Permission

from geonode.core.models import PermissionLevelMixin
from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS

from jsonfield.fields import JSONField
import simplejson

try:
	from south.modelsinspector import add_introspection_rules
	add_introspection_rules([], ['^jsonfield\.fields\.JSONField'])
except ImportError:
	pass

class Visualization(models.Model, PermissionLevelMixin):
	"""
	Model to store Weave session state, based on GeoNode's Map model
	"""

	title = models.CharField(_('Title'), max_length=100, blank=True, null=True)
	"""
	A display name suitable for search results and page headers
	"""

	abstract = models.TextField(_('Abstract'), blank=True, null=True)
	"""
	A longer description of the themes in the visualization.
	"""

	owner = models.ForeignKey(User, verbose_name=_('owner'))
	"""
	The user that created/owns this map.
	"""

	last_modified = models.DateTimeField(auto_now_add=True)
	"""
	The last time the map was modified.
	"""

	# TODO: cleanup Booleans from Python 'True' to JavaScript 'true'
	# sessionstate = JSONField(_('Session State'))
	sessionstate = models.TextField(_('Session State'))
	"""
	The configuration that specifies all aspects of a visualization.
	"""

	def __unicode__(self):
			return '%s by %s' % (self.title, (self.owner.username if self.owner else "<Anonymous>"))

	class Meta:
		unique_together = (('name', 'user'),)

	def update_from_viewer(self, conf):
		"""
		Update this Visualization's details by parsing a JSON object as produced by
		a Weave Flash instance.	 

		This method automatically persists to the database!
		"""
		self.title = conf['title']
		self.abstract = conf['abstract']
		self.sessionstate = conf['sessionstate']

		self.save()

	def get_absolute_url(self):
		return '/visualizations/%i' % self.id

	class Meta:
		# custom permissions, 
		# change and delete are standard in django
		permissions = (('view_visualization', 'Can view'), 
					   ('change_visualization_permissions', "Can change permissions"), )

	# Permission Level Constants
	# LEVEL_NONE inherited
	LEVEL_READ	= 'visualization_readonly'
	LEVEL_WRITE = 'visualization_readwrite'
	LEVEL_ADMIN = 'visualization_admin'

	def set_default_permissions(self):
		self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
		self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)

		# remove specific user permissions
		current_perms =	 self.get_all_level_info()
		for username in current_perms['users'].keys():
			user = User.objects.get(username=username)
			self.set_user_level(user, self.LEVEL_NONE)

		# assign owner admin privs
		if self.owner:
			self.set_user_level(self.owner, self.LEVEL_ADMIN)  
