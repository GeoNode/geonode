from django.shortcuts import render_to_response
from django.template import RequestContext

def analytic_list(request, template='analytics/analysis_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'analysis'})
    request.POST = post
    return search_page(request, template=template)


#### NEW ANALYSES ####

def new_analysis(request, template='analytics/analysis_view.html'):
    return render_to_response(template, RequestContext(request, { }))
