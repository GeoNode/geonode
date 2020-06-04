# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

"""Utilities for managing GeoNode base models
"""

# Standard Modules
import os
import logging

# Django functionality
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage as storage

# Geonode functionality
from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Link
from geonode.geoserver.helpers import ogc_server_settings

logger = logging.getLogger('geonode.base.utils')

_names = ['Zipped Shapefile', 'Zipped', 'Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
          'GeoJSON', 'Excel', 'Legend', 'GeoTIFF', 'GZIP', 'Original Dataset',
          'ESRI Shapefile', 'View in Google Earth', 'KML', 'KMZ', 'Atom', 'DIF',
          'Dublin Core', 'ebRIM', 'FGDC', 'ISO', 'ISO with XSL']

# embrapa #
from datetime import datetime
from geonode.base.models import Embrapa_Last_Updated
from django.db.models.functions import (ExtractDay, ExtractMonth, ExtractYear, ExtractHour, ExtractMinute, 
ExtractSecond)
import requests

def choice_purpose():
    current_year = get_only_year()

    unity_id = settings.EMBRAPA_UNITY_DEFAULT

    # Chamada para ação gerencial
    acao_gerencial_endpoint = 'https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/lista/acoesgerenciais/poridunidadeembrapaano/{0}/{1}'.format(unity_id, current_year)

    response = requests.get(acao_gerencial_endpoint)

    data = response.json()

    data_acao_gerencial = data["acaoGerencial"]

    # Chamada para projeto
    projeto_endpoint = 'https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/projeto/lista/poridunidadeembrapa?id_unidadeembrapa={0}'.format(unity_id)
    
    response = requests.get(projeto_endpoint)

    data = response.json()

    data_projeto_id_titulo = data["projeto"]

    tamanho_acao_gerencial = [i for i in range(len(data_acao_gerencial))]

    tamanho_projeto = [i for i in range(len(data_projeto_id_titulo))]

    embrapa_acao_gerencial_projeto_ids = [i for i in range(len(tamanho_acao_gerencial + tamanho_projeto))]

    for i in range(len(tamanho_acao_gerencial)):
        embrapa_acao_gerencial_projeto_ids[i] = data_acao_gerencial[i]["acaoGerencialId"] + ' - ' + data_acao_gerencial[i]["titulo"]

    j = len(tamanho_acao_gerencial)

    for i in range(len(tamanho_projeto)):
        embrapa_acao_gerencial_projeto_ids[j] = data_projeto_id_titulo[i]["id"] + ' - ' + data_projeto_id_titulo[i]["titulo"]
        j = j + 1

    return embrapa_acao_gerencial_projeto_ids


def choice_unity():
    response = requests.get('https://sistemas.sede.embrapa.br/corporativows/rest/corporativoservice/unidades/lista/todas')
    data = response.json()
    data_ids = data["unidadesEmbrapa"]
    embrapa_only_ids = [i for i in range(len(data_ids))]

    for i in range(len(data_ids)):
        embrapa_only_ids[i] = data_ids[i]["id"]

    embrapa_only_ids_tuples = list(zip(embrapa_only_ids,embrapa_only_ids))

    return embrapa_only_ids

def get_last_update():
    data_banco = Embrapa_Last_Updated.objects.annotate(
        day=ExtractDay('last_updated'),
        month=ExtractMonth('last_updated'),
        year=ExtractYear('last_updated'),
        hour=ExtractHour('last_updated'),
        minute=ExtractMinute('last_updated'),
        second=ExtractSecond('last_updated'),).values(
        'day', 'month', 'year', 'hour', 'minute', 'second'
    ).get()
    print(data_banco)
    day = data_banco["day"]
    month = data_banco["month"]
    year = data_banco["year"]
    hour = data_banco["hour"]
    minute = data_banco["minute"]
    second = data_banco["second"]

    result_in_seconds_from_database = day * 86400 + month * 2592000 + year * 31104000 + hour * 3600 + minute * 60 + second

    print("resultado do banco em segundos:")
    print(result_in_seconds_from_database)
    date_current = datetime.now()

    format_date = str(date_current)

    format_year = format_date[0:4]
    format_year = int(format_year)

    format_month = format_date[5:7]
    format_month = int(format_month)

    format_day = format_date[8:10]
    format_day = int(format_day)

    format_hour = format_date[11:13]
    format_hour = int(format_hour)

    format_minute = format_date[14:16]
    format_minute = int(format_minute)

    format_second = format_date[17:19]
    format_second = int(format_second)

    result_all_in_seconds_current = format_day * 86400 + format_month * 2592000 + format_year * 31104000 + format_hour * 3600 + format_minute * 60 + format_second

    print(result_all_in_seconds_current)

    return [result_all_in_seconds_current, result_in_seconds_from_database]


def get_only_year():

    time = datetime.now()

    format_time = str(time)

    format_time = format_time[0:4]

    return format_time

def delete_orphaned_thumbs():
    """
    Deletes orphaned thumbnails.
    """
    if isinstance(storage, FileSystemStorage):
        documents_path = os.path.join(settings.MEDIA_ROOT, 'thumbs')
    else:
        documents_path = os.path.join(settings.STATIC_ROOT, 'thumbs')
    if os.path.exists(documents_path):
        for filename in os.listdir(documents_path):
            fn = os.path.join(documents_path, filename)
            model = filename.split('-')[0]
            uuid = filename.replace(model, '').replace('-thumb.png', '')[1:]
            if ResourceBase.objects.filter(uuid=uuid).count() == 0:
                print('Removing orphan thumb %s' % fn)
                logger.debug('Removing orphan thumb %s' % fn)
                try:
                    os.remove(fn)
                except OSError:
                    print('Could not delete file %s' % fn)
                    logger.error('Could not delete file %s' % fn)


def remove_duplicate_links(resource):
    """
    Makes a scan of Links related to the resource and removes the duplicates.
    It also regenerates the Legend link in case this is missing for some reason.
    """
    for _n in _names:
        _links = Link.objects.filter(resource__id=resource.id, name=_n)
        _cnt = _links.count()
        while _cnt > 1:
            _links.last().delete()
            _cnt -= 1

    if isinstance(resource, Layer):
        # fixup Legend links
        layer = resource
        legend_url_template = ogc_server_settings.PUBLIC_LOCATION + \
            'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
            '{alternate}&STYLE={style_name}' + \
            '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'
        if layer.default_style and not layer.get_legend_url(style_name=layer.default_style.name):
            Link.objects.update_or_create(
                resource=layer.resourcebase_ptr,
                name='Legend',
                extension='png',
                url=legend_url_template.format(
                    alternate=layer.alternate,
                    style_name=layer.default_style.name),
                mime='image/png',
                link_type='image')
