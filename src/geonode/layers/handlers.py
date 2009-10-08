from piston.handler import BaseHandler, AnonymousBaseHandler
from geonode.layers.model import Layer
from geonode.layers.model import LayerUploadForm
from django import forms


class LayerHandler(BaseHandler):
    fields = 'id', 'title', 'created_on', 'remote_addr', ('author', ('username',)),
    model = Layer
    anonynmous = 'AnonLayerHandler'

    def read(self):
        pass

    @forms.validate(LayerUploadForm)
    def create(self):
        # save file to tmp dir
        # introspect / validate
        # push up to geoserver
        # return status

        # should there be a metadata representation in the body if not
        # using form encoding?
        pass

    def remove(self):
        # warn
        # purge remotely
        # if successful purge locally 
        pass

    @forms.validate(LayerUploadForm, 'PUT')
    def update(self):
        # warn of replacement if file uploaded
        # do create over
        # or
        # edit metadata
        pass 
    

class AnonLayerHandler(BaseHandler, AnonymousBaseHandler):
    fields = 'id', 'title', 'created_on', 'remote_addr',

