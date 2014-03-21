from django.shortcuts import render
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from geonode.utils import resolve_object
from geonode.security.views import _perms_info
from geonode.documents.models import get_related_documents
from geonode.analytics.models import Analysis
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

ANALYSIS_LEV_NAMES = {
    Analysis.LEVEL_NONE  : _('No Permissions'),
    Analysis.LEVEL_READ  : _('Read Only'),
    Analysis.LEVEL_WRITE : _('Read/Write'),
    Analysis.LEVEL_ADMIN : _('Administrative')
}

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this analysis.")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this analysis.')
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this analysis")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this analysis' metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this analysis.")

def analytic_list(request, template='analytics/analysis_list.html'):
    from geonode.search.views import search_page
    post = request.POST.copy()
    post.update({'type': 'analysis'})
    request.POST = post
    return search_page(request, template=template)


#### NEW ANALYSES ####

def new_analysis(request, template='analytics/analysis_view.html'):
    return render(request, template, { })

def analysis_view(request, analysisid, template='analytics/analysis_view.html'):
    analysis_obj = _resolve_analysis(request, analysisid, 'analysis.view_analysis', _PERMISSION_MSG_VIEW)

    return render(request, template, {
        'analysis' : analysis_obj
    })

def analysis_detail(request, analysisid, template='analytics/analysis_detail.html'):
    analysis_obj = _resolve_analysis(request, analysisid, 'analysis.view_analysis', _PERMISSION_MSG_VIEW)
    analysis_obj.popular_count += 1
    analysis_obj.save()

    return render(request, template, {
        'analysis' : analysis_obj,
        'documents' : get_related_documents(analysis_obj),
        'permission_json' : json.dumps(_perms_info(analysis_obj, ANALYSIS_LEV_NAMES)),
    })

def _resolve_analysis(request, id, permission='analysis.change_analysis',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the Analysis by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Analysis, {'pk':id}, permission=permission,
                          permission_msg=msg, **kwargs)

def new_analysis_json(request):
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponse(
                'You must be logged in to save new maps',
                mimetype="text/plain",
                status=401
            )
        analysis_obj = Analysis(owner=request.user, title=request.POST.get('title'), abstract=request.POST.get('abstract'))
        analysis_obj.save()
        return redirect('analysis_view', analysisid=analysis_obj.id)
    else:
        return HttpResponse(status=405)

@login_required
def analysis_remove(request, analysisid, template='analytics/analysis_remove.html'):
    ''' Delete an analysis. '''
    analysis_obj = _resolve_analysis(request, analysisid, 'analyses.delete_analysis',
                           _PERMISSION_MSG_DELETE, permission_required=True)

    if request.method == 'GET':
        return render(request, template, {
            "analysis": analysis_obj
        })

    elif request.method == 'POST':
        analysis_obj.delete()

        return redirect("analytics_browse")
