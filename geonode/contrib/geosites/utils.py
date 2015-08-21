import os
import shutil
from django.contrib.sites.models import Site
from django.conf import settings
from .models import SiteResources, SitePeople


def resources_for_site():
    return SiteResources.objects.get(site=Site.objects.get_current()).resources.all()


def users_for_site():
    return SitePeople.objects.get(site=Site.objects.get_current()).people.all()


def sed(filename, change_dict):
    """ Update file replacing key with value in provided dictionary """
    f = open(filename, 'r')
    data = f.read()
    f.close()

    for key, val in change_dict.items():
        data = data.replace(key, val)

    f = open(filename, 'w')
    f.write(data)
    f.close()


def dump_model(model, filename):
    from django.core import serializers
    data = serializers.serialize("json", model.objects.all(), indent=4)
    f = open(filename, "w")
    f.write(data)
    f.close()


def add_site(name, domain):
    """ Add a site to database, create directory tree """

    # get latest SITE id
    sites = Site.objects.all()
    used_ids = [v[0] for v in sites.values_list()]
    site_id = max(used_ids) + 1

    # current settings is one of the sites
    project_dir = os.path.realpath(os.path.join(settings.SITE_ROOT, '../'))
    site_dir = os.path.join(project_dir, 'site%s' % site_id)
    site_template = os.path.join(os.path.dirname(__file__), 'site_template')
    shutil.copytree(site_template, site_dir)

    # update configuration and settings files
    change_dict = {
        '$SITE_ID': str(site_id),
        '$SITE_NAME': name,
        '$DOMAIN': domain,
        '$SITE_ROOT': site_dir,
        '$SERVE_PATH': settings.SERVE_PATH,
        '$PORTNUM': '8%s' % str(site_id).zfill(3),
        '$GEOSERVER_URL': settings.GEOSERVER_URL,
        '$PROJECT_NAME': os.path.basename(os.path.dirname(settings.PROJECT_ROOT)),
    }

    sed(os.path.join(site_dir, 'conf/gunicorn'), change_dict)
    sed(os.path.join(site_dir, 'conf/nginx'), change_dict)
    sed(os.path.join(site_dir, 'settings.py'), change_dict)
    sed(os.path.join(site_dir, 'local_settings_template.py'), change_dict)
    sed(os.path.join(site_dir, 'wsgi.py'), change_dict)

    # add site to database
    site = Site(id=site_id, name=name, domain=domain)
    site.save()
    dump_model(Site, os.path.join(project_dir, 'sites.json'))
