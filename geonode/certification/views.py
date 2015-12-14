# Create your views here.
from django.db.models.loading import get_model
from geonode.certification.models import Certification
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

@login_required
def uncertify(request, modelid, modeltype):
    ''' Delete a certification '''
    
    model = get_model(*modeltype.split('.',1))
    model_obj = model.objects.get(pk=modelid)
    
    model_title = modelid
    
    if hasattr(model_obj, 'title'):
        model_title = model_obj.title
    
    if request.method == 'GET':
        return render_to_response("certification/certification_remove.html", RequestContext(request, {
            "modeltype": modeltype,
            "modelid": modelid,
            "title": model_title
        }))
    elif request.method == 'POST':
        certification = Certification.objects.uncertify(request.user,model_obj)
        redirecturl = model_obj.get_absolute_url()
        if modeltype == "maps.Map":
            redirecturl = model_obj.get_absolute_url() + "/info"
        return HttpResponseRedirect(redirecturl)
    
@login_required
def certify(request, modeltype, modelid):
    ''' Certify a map or layer'''
    model = get_model(*modeltype.split('.',1))
    model_obj = model.objects.get(pk=modelid)
    
    model_title = modelid
    
    if hasattr(model_obj, 'title'):
        model_title = model_obj.title
    
    if request.method == 'GET':
        return render_to_response("certification/certification_add.html", RequestContext(request, {
            "modeltype": modeltype,
            "modelid": modelid,
            "title": model_title
        }))
    elif request.method == 'POST':
        certification = Certification.objects.certify(request.user,model_obj)
        redirecturl = model_obj.get_absolute_url()
        if modeltype == "maps.Map":
            redirecturl = model_obj.get_absolute_url() + "/info"
        return HttpResponseRedirect(redirecturl)
        
    