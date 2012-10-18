#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
'''
This is an optional module that will be activated if geodjango is present.
It needs testing still...
'''

from django.conf import settings
from django.db.models import signals

from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.maps.models import map_changed_signal
from geonode.search import util

from logging import getLogger

_logger = getLogger(__name__)

def _index_for_model(model):
    if model == Layer:
        index = LayerIndex
    elif model == Map:
        index = MapIndex
    else:
        raise Exception('no index for model', model)
    return index


def filter_by_extent(model, q, extent, user=None):
    env = Envelope(extent)
    index = _index_for_model(model)
    extent_ids = index.objects.filter(extent__contained=env.wkt)
    if user:
        extent_ids = extent_ids.values('indexed__owner')
        return q.filter(user__in=extent_ids)
    else:
        extent_ids = extent_ids.values('indexed')
        return q.filter(id__in=extent_ids)


def filter_by_period(model, q, start, end, user=None):
    index = _index_for_model(model)
    q = index.objects.all()
    if start:
        q = q.filter(time_start__gte = util.iso_str_to_jdate(start))
    if end:
        q = q.filter(time_end__lte = util.iso_str_to_jdate(end))
    if user:
        period_ids = q.values('indexed__owner')
        q = q.filter(user__in=period_ids)
    else:
        period_ids = q.values('indexed')
        q = q.filter(id__in=period_ids)
    return q


def index_object(obj, update=False):
    if type(obj) == Layer:
        index = LayerIndex
        func = index_layer
    elif type(obj) == Map:
        index = MapIndex
        func = index_map
    else:
        raise Exception('cannot index %s' % obj)

    created = False
    try:
        index_obj = index.objects.get(indexed=obj)
    except index.DoesNotExist:
        _logger.debug('created index for %s',obj)
        index_obj = index(indexed=obj)
        created = True

    if not update or created:
        _logger.debug('indexing %s',obj)
        try:
            func(index_obj, obj)
        except:
            _logger.exception('Error indexing object %s', obj)
    else:
        _logger.debug('skipping %s',obj)


def index_layer(index, obj):
    start = end = None
    try:
        start, end = obj.get_time_extent()
    except:
        _logger.warn('could not get time info for %s', obj.typename)

    if start:
        index.time_start = util.iso_str_to_jdate(start)
    if end:
        index.time_end = util.iso_str_to_jdate(end)

    try:
        wms_metadata = obj.metadata()
    except:
        _logger.warn('could not get WMS info for %s', obj.typename)
        return

    min_x, min_y, max_x, max_y = wms_metadata.boundingBoxWGS84

    if wms_metadata.boundingBoxWGS84 != (0.0,0.0,-1.0,-1.0):
        try:
            index.extent = Envelope(min_x,min_y,max_x,max_y).wkt;
        except Exception,ex:
            _logger.warn('Error computing envelope: %s, bounding box was %s', str(ex),wms_metadata.boundingBoxWGS84)
    else:
        #@todo might be better to have a nullable extent
        _logger.warn('Bounding box empty, adding default envelope')
        index.extent = Envelope(-180,-90,180,90).wkt

    index.save()


def index_map(index, obj):
    time_start = None
    time_end = None
    extent = Envelope(0,0,0,0)
    for l in obj.local_layers:
        start = end = None
        try:
            start, end = l.get_time_extent()
        except:
            _logger.warn('could not get time info for %s', l.typename)

        if start:
            start = util.iso_str_to_jdate(start)
            if time_start is None:
                time_start = start
            else:
                time_start = min(time_start, start)
        if end:
            end = util.iso_str_to_jdate(end)
            if time_end is None:
                time_end = start
            else:
                time_end = max(time_end, end)

        try:
            wms_metadata = l.metadata()
            extent.expand_to_include(wms_metadata.boundingBoxWGS84)
        except:
            _logger.warn('could not get WMS info for %s', l.typename )

    if time_start:
        index.time_start = time_start
    if time_end:
        index.time_end = time_end
    index.extent = extent.wkt
    index.save()


def object_created(instance, sender, **kw):
    if kw['created']:
        index_object(instance)


def map_updated(sender, **kw):
    if kw['what_changed'] == 'layers':
        index_object(sender)


def object_deleted(instance, sender, **kw):
    if type(instance) == Layer:
        index = LayerIndex
    elif type(instance) == Map:
        index = MapIndex
    try:
        index.objects.get(indexed=instance).delete()
    except index.DoesNotExist:
        pass

# work around code coverage failures
if 'django.contrib.gis' in settings.INSTALLED_APPS:
    from django.contrib.gis.db import models
    from django.contrib.gis.gdal import Envelope
    class SpatialTemporalIndex(models.Model):
        time_start = models.BigIntegerField(null=True)
        time_end = models.BigIntegerField(null=True)
        extent = models.PolygonField()
        objects = models.GeoManager()

        class Meta:
            abstract = True

        def __unicode__(self):
            return '<SpatialTemporalIndex> for %s, %s, %s - %s' % (
                self.indexed,
                self.extent.extent,
                util.jdate_to_approx_iso_str(self.time_start),
                util.jdate_to_approx_iso_str(self.time_end)
            )

    class LayerIndex(SpatialTemporalIndex):
        indexed = models.OneToOneField(Layer,related_name='spatial_temporal_index')

    class MapIndex(SpatialTemporalIndex):
        indexed = models.OneToOneField(Map,related_name='spatial_temporal_index')
        
    signals.post_save.connect(object_created, sender=Layer)

    signals.pre_delete.connect(object_deleted, sender=Map)
    signals.pre_delete.connect(object_deleted, sender=Layer)

    map_changed_signal.connect(map_updated)