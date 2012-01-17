from django.conf.urls.defaults import patterns, url

urlpatterns = patterns("",
    url(r"^api/$", "geonode.search.views.search_api", name="search_api"),
)
