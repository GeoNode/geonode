# Create your views here.

def analytic_list(request, template='analytics/analytic_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'map'})
    request.POST = post
    return search_page(request, template=template)

