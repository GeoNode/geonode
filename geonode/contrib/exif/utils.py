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

import os

from slugify import Slugify
from datetime import datetime

custom_slugify = Slugify(separator='_')

ABSTRACT_TEMPLATE_MODEL_DATE_LATLON = "Image shot by {model} on {date} at {lat}, {lon} (latitude, longitude)"
ABSTRACT_TEMPLATE_MODEL_DATE = "Image shot by {model} on {date}"
ABSTRACT_TEMPLATE_MODEL = "Image shot by {model}"
ABSTRACT_TEMPLATE_DATE = "Image shot on {date}"


def convertExifDateToDjangoDate(date):
    a = list(date.replace(" ", "T"))
    a[4] = "-"
    a[7] = "-"
    a[10] = "T"

    return datetime(
        int("".join(a[0:4])),
        int("".join(a[5:7])),
        int("".join(a[8:10])),
        int("".join(a[11:13])),
        int("".join(a[14:16]))
    )


def convertExifLocationToDecimalDegrees(location, direction):
    if location:
        dd = 0.0
        d, m, s = location
        dd += float(d[0]) / float(d[1])
        dd += (float(m[0]) / float(m[1])) / 60.0
        dd += (float(s[0]) / float(s[1])) / 3600.0

        if direction:
            if direction.lower() == 's' or direction.lower() == 'w':
                dd = dd * -1.0
        return dd
    else:
        return None


def exif_extract_dict(doc):

    if not doc:
        return None

    if not doc.doc_file:
        return None

    if os.path.splitext(doc.doc_file.name)[1].lower()[1:] in ["jpg", "jpeg"]:
        from PIL import Image, ExifTags
        img = Image.open(doc.doc_file.path)
        exif_data = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items() if k in ExifTags.TAGS
        }

        exif_dict = {
            'width': exif_data.get('ExifImageWidth', None),
            'height': exif_data.get('ExifImageHeight', None),
            'make': exif_data.get('Make', None),
            'model': exif_data.get('Model', None),
            'date': None,
            'lat': None,
            'lon': None,
            'flash': exif_data.get('Flash', 0),
            'speed': exif_data.get('ISOSpeedRatings', 0)
        }

        date = None
        if "DateTime" in exif_data:
            date = exif_data["DateTime"]
        elif "DateTimeOriginal" in exif_data:
            date = exif_data["DateTimeOriginal"]
        elif "DateTimeDigitized" in exif_data:
            date = exif_data["DateTimeDigitized"]

        if date:
            try:
                date = convertExifDateToDjangoDate(date)
            except:
                print "Could not parse exif date"
                date = None

        if date:
            exif_dict['date'] = date

        if "GPSInfo" in exif_data:
            gpsinfo = {}
            for key in exif_data["GPSInfo"].keys():
                decode = ExifTags.GPSTAGS.get(key, key)
                gpsinfo[decode] = exif_data["GPSInfo"][key]
            if "GPSLatitude" in gpsinfo and "GPSLongitude" in gpsinfo:
                lat = convertExifLocationToDecimalDegrees(gpsinfo["GPSLatitude"], gpsinfo.get('GPSLatitudeRef', 'N'))
                lon = convertExifLocationToDecimalDegrees(gpsinfo["GPSLongitude"], gpsinfo.get('GPSLongitudeRef', 'E'))
                exif_dict['lat'] = lat
                exif_dict['lon'] = lon

        return exif_dict

    else:
        return None


def exif_extract_metadata_doc(doc):

    if not doc:
        return None

    if not doc.doc_file:
        return None

    if os.path.splitext(doc.doc_file.name)[1].lower()[1:] in ["jpg", "jpeg"]:
        from PIL import Image, ExifTags
        img = Image.open(doc.doc_file.path)
        exif_data = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items() if k in ExifTags.TAGS
        }

        model = None
        date = None
        keywords = []
        bbox = None
        lat = None
        lon = None
        abstract = None

        if "DateTime" in exif_data:
            date = exif_data["DateTime"]
        elif "DateTimeOriginal" in exif_data:
            date = exif_data["DateTimeOriginal"]
        elif "DateTimeDigitized" in exif_data:
            date = exif_data["DateTimeDigitized"]

        if date:
            try:
                date = convertExifDateToDjangoDate(date)
            except:
                print "Could not parse exif date"
                date = None

        if "Make" in exif_data:
            keywords.append(custom_slugify(exif_data["Make"]))

        if "Model" in exif_data:
            model = exif_data.get("Model", None)
            keywords.append(custom_slugify(model))

        if "GPSInfo" in exif_data:
            gpsinfo = {}
            for key in exif_data["GPSInfo"].keys():
                decode = ExifTags.GPSTAGS.get(key, key)
                gpsinfo[decode] = exif_data["GPSInfo"][key]
            if "GPSLatitude" in gpsinfo and "GPSLongitude" in gpsinfo:
                lat = convertExifLocationToDecimalDegrees(gpsinfo["GPSLatitude"], gpsinfo.get('GPSLatitudeRef', 'N'))
                lon = convertExifLocationToDecimalDegrees(gpsinfo["GPSLongitude"], gpsinfo.get('GPSLongitudeRef', 'E'))
                bbox = (lon, lon, lat, lat)

        abstract = exif_build_abstract(model=model, date=date, lat=lat, lon=lon)

        return {'date': date, 'keywords': keywords, 'bbox': bbox, 'abstract': abstract}

    else:
        return None


def exif_build_abstract(model=None, date=None, lat=None, lon=None):

    if model and date and lat and lon:
        return ABSTRACT_TEMPLATE_MODEL_DATE_LATLON.format(model=model, date=date, lat=lat, lon=lon)
    elif model and date:
        return ABSTRACT_TEMPLATE_MODEL_DATE.format(model=model, date=date)
    elif model:
        return ABSTRACT_TEMPLATE_MODEL.format(model=model)
    elif date:
        return ABSTRACT_TEMPLATE_DATE.format(date=date)
    else:
        return None
