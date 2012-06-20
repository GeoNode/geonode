from django.contrib.sitemaps import Sitemap
from geonode.maps.models import Layer, Map 

class LayerSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Layer.objects.all()

    def lastmod(self, obj):
        return obj.date

class MapSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Map.objects.all()
