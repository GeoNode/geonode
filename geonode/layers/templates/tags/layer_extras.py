from django import template
register = template.Library()

def get_layer_download_url(link, layer_name): # Only one argument.
    print ">>>NEW URL"+link.replace("geoserver","layer/geonode%3A{1}/geoserver".format(layer_name))
    return link.replace("geoserver","layer/geonode%3A{1}/geoserver".format(layer_name))
    
register.filter('get_layer_download_url', get_layer_download_url)
