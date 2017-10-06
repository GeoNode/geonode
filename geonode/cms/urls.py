from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from views import SliderImageList, SliderImageCreate, SliderImageUpdate, SliderImageDelete, \
    SectionList, SectionUpdate, IndexPageImageCreateView, IndexPageImageListView, IndexPageImageDelete, \
    IndexPageImageUpdate, TermsAndConditionView, TermsAndConditionUpdateView

urlpatterns = patterns(
    'geonode.cms.views',
    url(r'^section-management-table$', 'section_list', name='section-list-table'),
    url(r'^section-update$', 'section_update', name='section-update'),


    #home page section management with image and texts
    url(r'^slider-image/list$', SliderImageList.as_view(), name='slider-image-list'),
    url(r'^slider-image/(?P<section_pk>[0-9]+)/create$', SliderImageCreate.as_view(), name='slider-image-create'),
    url(r'^slider-image/(?P<image_pk>[0-9]+)/(?P<section_pk>[0-9]+)/update$', SliderImageUpdate.as_view(), name='slider-image-update'),
    url(r'^slider-image/(?P<image_pk>[0-9]+)/(?P<section_pk>[0-9]+)/delete$', SliderImageDelete.as_view(), name='slider-image-delete'),
    # url(r'^slider-image/(?P<news_pk>[0-9]+)/details$', NewsDetails.as_view(), name='news-details'),


    #tests
    url(r'^section/list$', SectionList.as_view(), name='section-list'),
    # url(r'^section/create$', SectionCreate.as_view(), name='slider-image-create'),
    url(r'^section/(?P<section_pk>[0-9]+)/update$', SectionUpdate.as_view(), name='section-update-view'),
    # url(r'^section/(?P<section_pk>[0-9]+)/delete$', SliderImageDelete.as_view(), name='slider-image-delete'),
    # url(r'^slider-image/(?P<news_pk>[0-9]+)/details$', NewsDetails.as_view(), name='news-details'),


    url(r'^index-page-image/list$', IndexPageImageListView.as_view(), name='index-page-image-list'),
    url(r'^index-page-image/(?P<section_pk>[0-9]+)/create$', IndexPageImageCreateView.as_view(), name='index-page-image-create'),
    url(r'^index-page-image/(?P<image_pk>[0-9]+)/(?P<section_pk>[0-9]+)/delete$', IndexPageImageDelete.as_view(), name='Index-page-image-delete'),
    url(r'^index-page-image/(?P<image_pk>[0-9]+)/(?P<section_pk>[0-9]+)/update$', IndexPageImageUpdate.as_view(), name='index-page-image-update'),
    url(r'^index-page-image/(?P<image_pk>[0-9]+)/(?P<section_pk>[0-9]+)/active-deactive$', 'activateimage', name='active-inactive-indexpage-image'),


    # crud for terms and condition in footer section
    url(r'^footer-section/(?P<slug>[-\w]+)/$', TermsAndConditionView.as_view(), name='footer-section-view'),
    url(r'^footer-section/(?P<slug>[-\w]+)/update$', TermsAndConditionUpdateView.as_view(), name='footer-section-update'),



)
