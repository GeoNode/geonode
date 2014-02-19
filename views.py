from django.shortcuts import render
from django.template import RequestContext

def analytic_list(request, template='analytics/analysis_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'analysis'})
    request.POST = post
    return search_page(request, template=template)


#### NEW ANALYSES ####

def new_analysis(request, template='analytics/analysis_view.html'):
    return render(request, template, { })

def analysis_detail(request, analysisid, template='analytics/analysis_detail.html'):
    return render(request, template, { })