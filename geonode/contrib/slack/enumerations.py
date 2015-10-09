# -*- coding: utf-8 -*-
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

SLACK_MESSAGE_TEMPLATES = {
    "layer_new": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "A new {type} {title} has been added to {sitename} by {owner_name}.  {url_detail}",
            "text": "A new {type} <{url_detail}|{title}> has been added to "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "Zipped Shapefile",
                 "value": "<{url_shp}|Download>",
                 "short": True
             },
             {
                 "title": "GeoJSON",
                 "value": "<{url_geojson}|Download>",
                 "short": True
             },
             {
                 "title": "View in Google Earth",
                 "value": "<{url_netkml}|Download>",
                 "short": True
             },
             {
                 "title": "View on Map",
                 "value": "<{url_map}|View>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "layer_edit": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "The {type} {title} has been modified on {sitename} by {owner_name}.  {url_detail}",
            "text": "The {type} <{url_detail}|{title}> has been modified on "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "Zipped Shapefile",
                 "value": "<{url_shp}|Download>",
                 "short": True
             },
             {
                 "title": "GeoJSON",
                 "value": "<{url_geojson}|Download>",
                 "short": True
             },
             {
                 "title": "View in Google Earth",
                 "value": "<{url_netkml}|Download>",
                 "short": True
             },
             {
                 "title": "View on Map",
                 "value": "<{url_map}|View>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "layer_delete": {
        "attachments": [{
            "title": "{title}",
            "fallback": "The {type} {title} has been deleted from {sitename}.  {baseurl}",
            "text": "The {type} {title} has been deleted from <{baseurl}|{sitename}>.",
            "color": "#FF0000"
        }]
    },
    "map_new": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "A new {type} {title} has been added to {sitename} by {owner_name}.  {url_detail}",
            "text": "A new {type} <{url_detail}|{title}> has been added to "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "View Map",
                 "value": "<{url_view}|View>",
                 "short": True
             },
             {
                 "title": "Download Map",
                 "value": "<{url_download}|Download>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "map_edit": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "The {type} {title} has been modified on {sitename} by {owner_name}.  {url_detail}",
            "text": "The {type} <{url_detail}|{title}> has been modified on "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "View Map",
                 "value": "<{url_view}|View>",
                 "short": True
             },
             {
                 "title": "Download Map",
                 "value": "<{url_download}|Download>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "map_delete": {
        "attachments": [{
            "title": "{title}",
            "fallback": "The {type} {title} has been deleted from {sitename}.  {baseurl}",
            "text": "The {type} {title} has been deleted from <{baseurl}|{sitename}>.",
            "color": "#FF0000"
        }]
    },
    "document_new": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "A new {type} {title} has been added to {sitename} by {owner_name}.  {url_detail}",
            "text": "A new {type} <{url_detail}|{title}> has been added to "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "Download Document",
                 "value": "<{url_download}|Download>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "document_edit": {
        "attachments": [{
            "title": "{title}",
            "title_link": "{url_detail}",
            "fallback": "The {type} {title} has been modified on {sitename} by {owner_name}.  {url_detail}",
            "text": "The {type} <{url_detail}|{title}> has been modified on "
                    "<{baseurl}|{sitename}> by <{owner_url}|{owner_name}>.",
            "thumb_url": "{thumbnail_url}",
            "fields": [{
                 "title": "Download Document",
                 "value": "<{url_download}|Download>",
                 "short": True
             }],
            "color": "#000099"
        }]
    },
    "document_delete": {
        "attachments": [{
            "title": "{title}",
            "fallback": "The {type} {title} has been deleted from {sitename}.  {baseurl}",
            "text": "The {type} {title} has been deleted from <{baseurl}|{sitename}>.",
            "color": "#FF0000"
        }]
    }
}
