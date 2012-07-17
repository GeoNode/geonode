from geonode.catalogue.backends.generic import CatalogueBackend as GenericCatalogueBackend

class CatalogueBackend(GenericCatalogueBackend):
    def __init__(self, *args, **kwargs):
        super(CatalogueBackend, self).__init__(*args, **kwargs)
        self.catalogue.type = 'geonetwork'
