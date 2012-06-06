from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import simplejson as json

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

def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            mimetype='text/plain'
        )
    users = User.objects.filter(username__startswith=request.POST['query'])
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )
