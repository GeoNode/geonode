# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :

# Copyright (C) 2008  Neogeo Technologies
#
# This file is part of Opencarto project
#
# Opencarto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Opencarto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Opencarto.  If not, see <http://www.gnu.org/licenses/>.
#
from django import db
from django.contrib.gis.gdal import DataSource, SpatialReference, OGRGeometry
from django.utils.text import slugify


def get_model_field_name(field):
    """Get the field name usable without quotes.
    """
    # Remove spaces and strange characters.
    field = slugify(field)

    # Use underscores instead of dashes.
    field = field.replace('-', '_')

    # Use underscores instead of semicolons.
    field = field.replace(':', '_')

    # Do not let it be called id
    if field in ('id',):
        field += '_'

    # Avoid postgres reserved keywords.
    if field.upper() in PG_RESERVED_KEYWORDS:
        field += '_'

    # Do not let it end in underscore
    if field[-1:] == '_':
        field += 'field'

    # Make sure they are not numbers
    try:
        int(field)
        float(field)
        field = "_%s" % field
    except ValueError:
        pass

    return field


def transform_geom(wkt, srid_in, srid_out):

    proj_in = SpatialReference(int(srid_in))
    proj_out = SpatialReference(int(srid_out))
    ogr = OGRGeometry(wkt)
    if hasattr(ogr, 'srs'):
        ogr.srs = proj_in
    else:
        ogr.set_srs(proj_in)

    ogr.transform_to(proj_out)

    return ogr.wkt


def get_extent_from_text(points, srid_in, srid_out):
    """Transform an extent from srid_in to srid_out."""
    proj_in = SpatialReference(srid_in)

    proj_out = SpatialReference(srid_out)

    if srid_out == 900913:
        if int(float(points[0])) == -180:
            points[0] = -179
        if int(float(points[1])) == -90:
            points[1] = -89
        if int(float(points[2])) == 180:
            points[2] = 179
        if int(float(points[3])) == 90:
            points[3] = 89

    wkt = 'POINT(%f %f)' % (float(points[0]), float(points[1]))
    wkt2 = 'POINT(%f %f)' % (float(points[2]), float(points[3]))

    ogr = OGRGeometry(wkt)
    ogr2 = OGRGeometry(wkt2)

    if hasattr(ogr, 'srs'):
        ogr.srs = proj_in
        ogr2.srs = proj_in
    else:
        ogr.set_srs(proj_in)
        ogr2.set_srs(proj_in)

    ogr.transform_to(proj_out)
    ogr2.transform_to(proj_out)

    wkt = ogr.wkt
    wkt2 = ogr2.wkt

    mins = wkt.replace('POINT (', '').replace(')', '').split(' ')
    maxs = wkt2.replace('POINT (', '').replace(')', '').split(' ')
    mins.append(maxs[0])
    mins.append(maxs[1])

    return mins


def merge_geometries(geometries_str, sep='$'):
    """Take a list of geometries in a string, and merge it."""
    geometries = geometries_str.split(sep)
    if len(geometries) == 1:
        return geometries_str
    else:
        pool = OGRGeometry(geometries[0])
        for geom in geometries:
            pool = pool.union(OGRGeometry(geom))
        return pool.wkt


def file2pgtable(infile, table_name, srid=4326):
    """Create table and fill it from file."""
    table_name = table_name.lower()
    datasource = DataSource(infile)
    layer = datasource[0]

    # création de la requête de création de table
    geo_type = str(layer.geom_type).upper()
    coord_dim = 0
    # bizarre, mais les couches de polygones MapInfo ne sont pas détectées
    if geo_type == 'UNKNOWN' and (
            infile.endswith('.TAB') or infile.endswith('.tab') or
            infile.endswith('.MIF') or infile.endswith('.mif')):
        geo_type = 'POLYGON'

    sql = 'BEGIN;'

    # Drop table if exists
    sql += 'DROP TABLE IF EXISTS %s;' % (table_name)

    sql += "CREATE TABLE %s(" % (table_name)
    first_feature = True
    # Mapping from postgis table to shapefile fields.
    mapping = {}
    for feature in layer:
        # Getting the geometry for the feature.
        geom = feature.geom
        if geom.geom_count > 1:
            if not geo_type.startswith('MULTI'):
                geo_type = 'MULTI' + geo_type
        if geom.coord_dim > coord_dim:
            coord_dim = geom.coord_dim
            if coord_dim > 2:
                coord_dim = 2

        if first_feature:
            first_feature = False
            fields = []
            fields.append('id' + " serial NOT NULL PRIMARY KEY")
            fieldnames = []
            for field in feature:
                field_name = get_model_field_name(field.name)
                if field.type == 0:  # integer
                    fields.append(field_name + " integer")
                    fieldnames.append(field_name)
                elif field.type == 2:  # float
                    fields.append(field_name + " double precision")
                    fieldnames.append(field_name)
                elif field.type == 4:
                    fields.append(field_name + " character varying(%s)" % (
                        field.width))
                    fieldnames.append(field_name)
                elif field.type == 8 or field.type == 9 or field.type == 10:
                    fields.append(field_name + " date")
                    fieldnames.append(field_name)

                mapping[field_name] = field.name

    sql += ','.join(fields)
    sql += ');'

    sql += "SELECT AddGeometryColumn('public','%s','geom',%d,'%s',%d);" % \
           (table_name, srid, geo_type, coord_dim)

    sql += 'END;'

    # la table est créée il faut maintenant injecter les données
    fieldnames.append('geom')
    mapping['geom'] = geo_type

    # Running the sql
    execute(sql)

    return mapping


def execute(sql):
    """Turns out running plain SQL within Django is very hard.
       The following code is really weak but gets the job done.
    """
    cursor = db.connections['datastore'].cursor()
    try:
        cursor.execute(sql)
    except:
        raise
    finally:
        cursor.close()

# Obtained from
# http://www.postgresql.org/docs/9.2/static/sql-keywords-appendix.html
PG_RESERVED_KEYWORDS = ('ALL',
                        'ANALYSE',
                        'ANALYZE',
                        'AND',
                        'ANY',
                        'ARRAY',
                        'AS',
                        'ASC',
                        'ASYMMETRIC',
                        'AUTHORIZATION',
                        'BOTH',
                        'BINARY',
                        'CASE',
                        'CAST',
                        'CHECK',
                        'COLLATE',
                        'COLLATION',
                        'COLUMN',
                        'CONSTRAINT',
                        'CREATE',
                        'CROSS',
                        'CURRENT_CATALOG',
                        'CURRENT_DATE',
                        'CURRENT_ROLE',
                        'CURRENT_SCHEMA',
                        'CURRENT_TIME',
                        'CURRENT_TIMESTAMP',
                        'CURRENT_USER',
                        'DEFAULT',
                        'DEFERRABLE',
                        'DESC',
                        'DISTINCT',
                        'DO',
                        'ELSE',
                        'END',
                        'EXCEPT',
                        'FALSE',
                        'FETCH',
                        'FOR',
                        'FOREIGN',
                        'FREEZE',
                        'FROM',
                        'FULL',
                        'GRANT',
                        'GROUP',
                        'HAVING',
                        'ILIKE',
                        'IN',
                        'INITIALLY',
                        'INTERSECT',
                        'INTO',
                        'IS',
                        'ISNULL',
                        'JOIN',
                        'LEADING',
                        'LEFT',
                        'LIKE',
                        'LIMIT',
                        'LOCALTIME',
                        'LOCALTIMESTAMP',
                        'NATURAL',
                        'NOT',
                        'NOTNULL',
                        'NULL',
                        'OFFSET',
                        'ON',
                        'ONLY',
                        'OR',
                        'ORDER',
                        'OUTER',
                        'OVER',
                        'OVERLAPS',
                        'PLACING',
                        'PRIMARY',
                        'REFERENCES',
                        'RETURNING',
                        'RIGHT',
                        'SELECT',
                        'SESSION_USER',
                        'SIMILAR',
                        'SOME',
                        'SYMMETRIC',
                        'TABLE',
                        'THEN',
                        'TO',
                        'TRAILING',
                        'TRUE',
                        'UNION',
                        'UNIQUE',
                        'USER',
                        'USING',
                        'VARIADIC',
                        'VERBOSE',
                        'WHEN',
                        'WHERE',
                        'WINDOW',
                        'WITH',)
