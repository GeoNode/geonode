from django.shortcuts import render
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from geonode.news.models import News
from geonode.news.forms import NewsUpdateForm
from geonode.base.libraries.decorators import superuser_check

# Create your views here.

# @login_required
# @user_passes_test(superuser_check)
# def news_create(request):
#     if request.method == 'POST':
#         form = NewsUpdateForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(reverse('news-list'))
#     else:
#         form = NewsUpdateForm()
#     return render(request, "news_create.html", {'form': form, })
#
#
# def news_lsit(request, template='news_list.html'):
#     context_dict = {
#         "news_list": News.objects.all()[:15],
#     }
#     return render_to_response(template, RequestContext(request, context_dict))
#
#
# def news_details(request, news_pk, template='news_details.html'):
#     context_dict = {
#         "news": News.objects.get(id=news_pk)
#     }
#     return render_to_response(template, RequestContext(request, context_dict))


class NewsList(ListView):
    """
    This view lists all the news
    """
    template_name = 'news_list.html'
    model = News

    def get_queryset(self):
        return News.objects.all().order_by('-publish_date')[:15]

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)
        context['latest_news_list'] = News.objects.all().order_by('-publish_date')[:5]
        return context


class NewsCreate(CreateView):
    """
    This view is for creating new news
    """
    template_name = 'news_create.html'
    model = News
    form_class = NewsUpdateForm

    def dispatch(self, request, *args, **kwargs):
        response = super(NewsCreate, self).dispatch(request, *args, **kwargs)
        if not self.request.user.is_superuser:
            return HttpResponseRedirect(reverse('news-list'))
        else:
            return response

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.publish_date = form.data['publish_date']
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


    def get_success_url(self):
        return reverse('news-details', kwargs={'news_pk': self.object.id})


class NewsUpdate(UpdateView):
    """
    This view is for updating an existing news
    """
    template_name = 'news_create.html'
    model = News
    form_class = NewsUpdateForm

    def dispatch(self, request, *args, **kwargs):
        response = super(NewsUpdate, self).dispatch(request, *args, **kwargs)
        if not self.request.user.is_superuser:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return response

    def get_object(self):
        return News.objects.get(pk=self.kwargs['news_pk'])

    def get_success_url(self):
        return reverse('news-details', kwargs={'news_pk': self.object.id})


class NewsDelete(DeleteView):
    """
    This view is for deleting an existing news
    """
    template_name = 'news_delete.html'
    model = News

    def dispatch(self, request, *args, **kwargs):
        response = super(NewsDelete, self).dispatch(request, *args, **kwargs)
        if not self.request.user.is_superuser:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return response

    def get_success_url(self):
        return reverse('news-list')

    def get_object(self):
        return News.objects.get(pk=self.kwargs['news_pk'])


class NewsDetails(DetailView):
    """
    This view gives the details of a news
    """
    template_name = 'news_details.html'

    def get_object(self):
        return News.objects.get(pk=self.kwargs['news_pk'])