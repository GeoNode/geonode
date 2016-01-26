# -*- coding: utf-8 -*-
import errno
import logging
import urllib

from urlparse import urlparse, urljoin
from socket import error as socket_error

from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings

from geonode import GeoNodeException

from geonode.base.models import ResourceBase
from geonode.base.models import Link
from geonode.layers.utils import create_thumbnail
from geonode.people.models import Profile


logger = logging.getLogger("geonode.qgis_server.signals")


def qgis_server_pre_delete(instance, sender, **kwargs):
    """Removes the layer from Local Storage
    """
    logger.debug('QGIS Server Pre Delete')


def qgis_server_pre_save(instance, sender, **kwargs):
    """Send information to QGIS Server.

       The attributes sent include:

        * Title
        * Abstract
        * Name
        * Keywords
        * Metadata Links,
        * Point of Contact name and url
    """
    logger.debug('QGIS Server Pre Save')


def qgis_server_post_save(instance, sender, **kwargs):
    """Save keywords to QGIS Server

       The way keywords are implemented requires the layer
       to be saved to the database before accessing them.
    """
    logger.debug('QGIS Server Post Save')


def qgis_server_pre_save_maplayer(instance, sender, **kwargs):
    logger.debug('QGIS Server Pre Save Map Layer')


def qgis_server_post_save_map(instance, sender, **kwargs):

    logger.debug('QGIS Server Post Save Map')
