
from django.conf.urls import url, include

from .views import ErrorReportingListView

urlpatterns = [

    url(r'^', ErrorReportingListView.as_view(), name='error_reporting'),

]
