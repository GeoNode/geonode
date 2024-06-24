from geonode.upload.api.views import ResourceImporter, ImporterViewSet
from django.urls import re_path



from geonode.api.urls import router

from . import views

router.register(r"upload-size-limits", views.UploadSizeLimitViewSet, "upload-size-limits")
router.register(r"upload-parallelism-limits", views.UploadParallelismLimitViewSet, "upload-parallelism-limits")

urlpatterns = []

