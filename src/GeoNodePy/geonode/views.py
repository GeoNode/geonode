from django.conf import settings
from geonode.maps.models import Map
from django import forms
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request): 
    return render_to_response('index.html', RequestContext(request))

def static(request, page):
    return render_to_response(page + '.html', RequestContext(request, {
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
    }))

def community(request):
    return render_to_response('community.html', RequestContext(request))

def lang(request): 
    return render_to_response('lang.js', mimetype="text/javascript")

class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()

def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
                content="ajax login requires HTTP POST",
                status=405,
                mimetype="text/plain"
            )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                    content="bad credentials or disabled user",
                    status=400,
                    mimetype="text/plain"
                )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                    content="successful login",
                    status=200,
                    mimetype="text/plain"
                )
    else:
        return HttpResponse(
                "The form you submitted doesn't look like a username/password combo.",
                mimetype="text/plain",
                status=400
            )
