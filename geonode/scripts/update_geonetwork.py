import urllib2

from geonode.maps.models import Layer

def update_geonetwork():
    layers = Layer.objects.all().order_by('id')

    for layer in layers:
        print layer.id, layer.name
        url = 'http://worldmap.harvard.edu/geonetwork/srv/en/csw?outputschema=http://www.isotc211.org/2005/gmd&service=CSW&request=GetRecordById&version=2.0.2&elementsetname=full&id=%s' % layer.uuid
        response = urllib2.urlopen(url)
        xml = response.read()
        if layer.name.encode() not in xml:
            print '***** Need to update metadata for layer id %s, named %s *****' % (layer.id, layer.name)
            try:
                layer.save_to_geonetwork()
            except:
                print '*** Error syncing metadata for this layer!'
