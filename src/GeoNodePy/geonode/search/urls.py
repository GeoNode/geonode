from django.conf.urls.defaults import patterns, url

urlpatterns = patterns("",
    url(r"^$", "geonode.search.views.search", name="search"),
    url(r"^api/$", "geonode.search.views.search_api", name="search_api"),
)
