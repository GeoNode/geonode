from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

#@register.inclusion_tag('eula_text.html')(eula_text)
def eula_form(request):
    if request.method == 'POST':
        #Handle form
        return HttpResponse(
                content="successful login",
                status=200,
                mimetype="text/plain"
            )
    else:
        #Render form
        return render(request, 'eula_form.html')
