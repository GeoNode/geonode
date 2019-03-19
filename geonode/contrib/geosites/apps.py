from django.apps import AppConfig
from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _


def create_default_site_relations(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, apps=global_apps,
                                  **kwargs):
    try:
        Site = apps.get_model('sites', 'Site')
        SiteResources = apps.get_model('geosites', 'SiteResources')
        SitePeople = apps.get_model('geosites', 'SitePeople')
        SiteGroups = apps.get_model('geosites', 'SiteGroups')
    except LookupError:
        return

    if not router.allow_migrate_model(using, SiteResources):
        return

    for site in Site.objects.all():
        SiteResources.objects.get_or_create(site=site)
        SitePeople.objects.get_or_create(site=site)
        SiteGroups.objects.get_or_create(site=site)


class GeositesConfig(AppConfig):
    name = 'geonode.contrib.geosites'
    verbose_name = _("Geosites")

    def ready(self):
        post_migrate.connect(create_default_site_relations, sender=self)
