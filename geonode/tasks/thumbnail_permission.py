import subprocess


def update_thumb_perms(layer):

    print layer.name, ': Setting thumbnail permissions...'
    thumbnail_str = 'layer-' + str(layer.uuid) + '-thumb.png'
    thumb_url = '/var/www/geonode/uploaded/thumbs/' + thumbnail_str
    subprocess.call(['sudo', '/bin/chown', 'www-data:www-data', thumb_url])
    subprocess.call(['sudo', '/bin/chmod', '666', thumb_url])
