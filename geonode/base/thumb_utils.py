import os

from django.conf import settings
from geonode.storage.manager import storage_manager


def thumb_path(filename):
    """Return the complete path of the provided thumbnail file accessible
    via Django storage API"""
    return os.path.join(settings.THUMBNAIL_LOCATION, filename)


def thumb_exists(filename):
    """Determine if a thumbnail file exists in storage"""
    return storage_manager.exists(thumb_path(filename))


def thumb_size(filepath):
    """Determine if a thumbnail file size in storage"""
    if storage_manager.exists(filepath):
        return storage_manager.size(filepath)
    elif os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0


def thumb_open(filename):
    """Returns file handler of a thumbnail on the storage"""
    return storage_manager.open(thumb_path(filename))


def get_thumbs():
    """Fetches a list of all stored thumbnails"""
    if not storage_manager.exists(settings.THUMBNAIL_LOCATION):
        return []
    subdirs, thumbs = storage_manager.listdir(settings.THUMBNAIL_LOCATION)
    return thumbs


def remove_thumb(filename):
    """Delete a thumbnail from storage"""
    storage_manager.delete(thumb_path(filename))


def remove_thumbs(name):
    """Removes all stored thumbnails that start with the same name as the
    file specified"""
    for thumb in get_thumbs():
        if thumb.startswith(name):
            remove_thumb(thumb)
