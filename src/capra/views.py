from django.template import Context, loader
from django.http import HttpResponse
from django.shortcuts import render_to_response

# Create your views here.
view(request, page):
    return render_to_response('capra/' + page + '.html')
