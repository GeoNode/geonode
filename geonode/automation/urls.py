from django.conf.urls import url, patterns, include
import views

urlpatterns = patterns('',
                       url(r'^input/$', views.metadata_job,
                           name='metadata_job'),
                       url(r'^/', include('geonode.cephgeo.urls')),
                       )
