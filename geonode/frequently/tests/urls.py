"""
This ``urls.py`` is only used when running the tests via ``runtests.py``.
As you know, every app must be hooked into yout main ``urls.py`` so that
you can actually reach the app's views (provided it has any views, of course).

"""
from django.urls import include, path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView


admin.autodiscover()


urlpatterns = [
    path(r'^admin/', admin.site.urls),
    path(r'^faq/', include('frequently.urls')),
    path(r'^test/$', TemplateView.as_view(template_name=('tag_test.html'))),
]

urlpatterns += staticfiles_urlpatterns()
