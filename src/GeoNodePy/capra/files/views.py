from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
from capra.files.models import AMEFile

try:
    import json
except ImportError:
    import simplejson as json


def index(request):
    """
    index of general files uploaded to the geonode
    """
    return render_to_response('files/index.html')

def index_json(request):
    """
    info about files uploaded to the geonode used by 
    the javascript ame list view.
    """
    
    info = []
    for file in AMEFile.objects.all():
        file_info = {}
        file_info['name'] = file.name
        file_info['scenario'] = file.scenario
        file_info['country'] = file.country
        file_info['filename'] = file.filename
        file_info['download_url'] = file.download_url
        file_info['edit_url'] = reverse('capra.files.views.dispatch', args=[file.id])
        info.append(file_info)

    res = HttpResponse(json.dumps(info))
    res.content_type = 'application/json'
    return res

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = AMEFile

@login_required
def upload(request):
    """
    view that handles uploading a new file
    """
    if request.method == 'POST':  
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('capra.files.views.index'))
    else:
        form = UploadFileForm()

    return render_to_response('files/upload.html', {'form': form})

def dispatch(request, id):
    """
    dispatch method based on http method
    """
    if 'remove' in request.GET: 
        return delete(request, id)
    elif 'replace' in request.GET:
        return replace(request, id)
    else:
        return detail(request, id)

def detail(request, fileid):
    """
    view that handles viewing a file's details
    """
    f = get_object_or_404(AMEFile, pk=fileid)
    return render_to_response('files/detail.html', {'file': f})

class EditFileForm(forms.ModelForm):
    class Meta:
        model = AMEFile
        fields = ['title', 'scenario', 'country']
    
@login_required
def edit(request, id):
    """
    view that handles editing a file's metadata
    """
    obj = get_object_or_404(AMEFile, pk=id)
    if request.method == 'POST':
        form = EditFileForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('capra.files.views.dispatch', args=[obj.id]))
    elif request.method == 'GET':
        form = EditFileForm(instance=obj)
    
    return render_to_response('files/edit.html', {'form': form, 'file': obj})


class ReplaceFileForm(forms.ModelForm):
    class Meta:
        model = AMEFile
        fields = ['file', 'title']

@login_required
def replace(request, id):
    obj = get_object_or_404(AMEFile, pk=id)
    if request.method == 'POST':
        form = ReplaceFileForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            # remove the old file which is being replaced.
            if obj.file: 
                obj.file.delete()
            form.save()
            return HttpResponseRedirect(reverse('capra.files.views.dispatch', args=[obj.id]))            
    elif request.method == 'GET':
        form = ReplaceFileForm(instance=obj)

    return render_to_response('files/replace.html', {'form': form, 'file': obj})

@login_required
def delete(request, fileid):
    """
    handles deleting a file
    """
    f = get_object_or_404(AMEFile, pk=fileid)
    f.delete()
    return HttpResponseRedirect(reverse('capra.files.views.index'))
