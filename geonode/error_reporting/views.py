from django.views.generic.list import ListView
from django_db_logger.models import StatusLog
from django.utils.html import format_html


# Create your views here.
class ErrorReportingListView(ListView):

    template_name = 'error_reporting/error_reporting.html'
    model = StatusLog
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super(ErrorReportingListView, self).get_context_data(**kwargs)

        """
        CRITICAL = 50
        FATAL = CRITICAL
        ERROR = 40
        WARNING = 30
        WARN = WARNING
        INFO = 20
        DEBUG = 10
        NOTSET = 0
        """

        error_object = {
            50: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='red',
                weight='bold',
                msg='CRITICAL'
            ),
            40: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='red',
                weight='bold',
                msg='ERROR'
            ),
            30: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='orange',
                weight='bold',
                msg='WARNING'
            ),
            20: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='green',
                weight='bold',
                msg='INFO'
            ),
            10: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='orange',
                weight='bold',
                msg='DEBUG'
            ),
            0: format_html(
                "<span style='color:{color}; font-weight:{weight}'>{msg}</span>",
                color='green',
                weight='bold',
                msg='NOTSET'
            ),
        }

        if context['object_list']:
            for error in context['object_list']:
                error.level = error_object[int(error.level)]

        return context
