from django.shortcuts import render
from django.views.generic.list import ListView
from .models import ErrorLoggingAndReporting
from django_db_logger.models import StatusLog


# Create your views here.
class ErrorReportingListView(ListView):

    template_name = 'error_reporting/error_reporting.html'
    model = StatusLog
    paginate_by = 2

    """
    def get_context_data(self, **kwargs):
        context = super(ErrorReportingListView, self).get_context_data(**kwargs)
        # import pdb;pdb.set_trace()
        return context
    """