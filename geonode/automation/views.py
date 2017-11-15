from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse_lazy
from pprint import pprint
from geonode.base.enumerations import CHARSETS
from django.utils.encoding import smart_str
from .forms import MetaDataJobForm
from .models import AutomationJob
# Create your views here.


def create_obj():
    pass


@login_required
@user_passes_test(lambda u: u.is_superuser)
def metadata_job(request):
    """Fetches process job for AutomationJob.

    Shows form MetaDataJobForm to create a worker.

    Args:
        request (:obj: `request object`): HTTP request upon access of URL.

    Returns:
        A dictionary mapping of the request to the corresponding fetched data from
        MetadataJobForm.

    **URL:**
        `\/automation\/input\/`

    **Template:**
        input_job.html
    """
    print 'METHOD IS ', request.method
    if request.method == 'POST':
        print 'Method: ', str(request.method)
        form = MetaDataJobForm(request.POST)
        if form.is_valid():
            print 'Valid'
            print 'Input Directory', smart_str(form.cleaned_data['input_dir'])
            print 'Processor', smart_str(form.cleaned_data['processor'])
            print 'Datatype', smart_str(form.cleaned_data['datatype'])
            print 'Saving...'
            obj = form.save(commit=False)
            for each_idir in obj.input_dir.split(';'):
                if each_idr:
                    obj.input_dir = each_idir
                    obj.save()
            return render(request, "update_task.html")

    else:
        print 'Method:', str(request.method)
        form = MetaDataJobForm()

    return render(request, 'input_job.html', {'input_job_form': form})
