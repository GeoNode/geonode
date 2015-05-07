from django.shortcuts import render

#@register.inclusion_tag('eula_text.html')(eula_text)
def eula_form(request):
    if request.method == 'POST':
        #Handle form
    else:
        #Render form
        return render(request, 'eula_form.html')
