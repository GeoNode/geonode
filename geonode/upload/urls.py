from django.urls import include, re_path

urlpatterns = [  # 'geonode.upload.views',
    re_path(r"^", include("geonode.upload.api.urls")),
]