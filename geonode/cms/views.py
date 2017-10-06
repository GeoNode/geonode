import tempfile
import os


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import Http404
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from actstream.models import Action

from geonode.base.libraries.decorators import superuser_check
from models import SectionManagementTable
from models import SliderImages
from forms import SliderImageUpdateForm
from geonode.news.models import News
from geonode.layers.models import Layer
from models import SectionManagementModel
from forms import SliderSectionManagementForm, FeatureHighlightsSectionManagementForm, InterPortabilitySectionManagementForm, \
    PrettyMapsSectionManagementForm, Maps3DSectionManagementForm, ShareMapSectionManagementForm, OurPartnersSectionManagementForm, \
    CounterSectionManagementForm, FooterSectionManagementForm, LatestNewsUpdateSectionManagementForm
from models import IndexPageImagesModel
from forms import IndexPageImageUploadForm, OurPartnersImagesUploadForm, FooterImagesUploadForm
from geonode.maps.models import Map
from geonode.groups.models import GroupProfile
from geonode.cms.models import FooterSectionDescriptions
from geonode.cms.forms import FooterSubSectionsUpdateForm



terms_and_condition_description = "Add terms and conditions here"
privacy_policy_description = "privacy policy"
terms_of_use_description = "terms of use"



# Create your views here.

class IndexClass(ListView):
    """
    Renders Index.html and Returns recent public activity.
    """
    context_object_name = 'action_list'
    queryset = Action.objects.filter(public=True)[:15]
    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ListView, self).get_context_data(*args, **kwargs)

        # add sections to index page when start the application
        if SectionManagementTable.objects.all().count() == 0:
            add_sections_to_index_page()

        contenttypes = ContentType.objects.all()
        for ct in contenttypes:
            if ct.name == 'layer':
                ct_layer_id = ct.id
            if ct.name == 'map':
                ct_map_id = ct.id
            if ct.name == 'comment':
                ct_comment_id = ct.id

        context['action_list_layers'] = Action.objects.filter(
            public=True,
            action_object_content_type__id=ct_layer_id)[:15]
        context['action_list_maps'] = Action.objects.filter(
            public=True,
            action_object_content_type__id=ct_map_id)[:15]
        context['action_list_comments'] = Action.objects.filter(
            public=True,
            action_object_content_type__id=ct_comment_id)[:15]
        context['latest_news_list'] = News.objects.all().order_by('-date_created')[:5]
        context['featured_layer_list'] = Layer.objects.filter(featured=True)

        #home page counters
        context['layer_counter'] = Layer.objects.filter(status='ACTIVE').count()
        context['map_counter'] = Map.objects.filter(status='ACTIVE').count()
        context['group_counter'] = GroupProfile.objects.all().count()
        if self.request.user.is_superuser:
            context['user_counter'] = get_user_model().objects.exclude(username='AnonymousUser').count()
        else:
            context['user_counter'] = get_user_model().objects.exclude(
                username='AnonymousUser').exclude(is_staff=True).filter(is_active=True).count()


        sections = SectionManagementTable.objects.all()
        for section in sections:
            if section.slug == 'slider-section':
                context['is_slider'] = section.is_visible
                context['slider_section'] = SectionManagementModel.objects.get(slug=section.slug)
                context['sliders'] = SliderImages.objects.filter(is_active=True, section=section)
            if section.slug == 'counter-section':
                context['is_counter_section'] = section.is_visible
                context['counter_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'featured-layers-section':
                context['is_featured_layers'] = section.is_visible
                context['featured_layers_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'latest-news-and-updates-section':
                context['is_latest_news'] = section.is_visible
                context['latest_news_update_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'feature-highlights-of-geodash-section':
                context['is_feature_highlights'] = section.is_visible
                context['feature_highlights_of_geodash_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'interportability-section':
                context['is_interportability'] = section.is_visible
                context['is_interportability_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'make-pretty-maps-with-geodash-section':
                context['is_pretty'] = section.is_visible
                context['make_pretty_maps_with_geodash_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'view-your-maps-in-3d-section':
                context['is_3dmap'] = section.is_visible
                context['view_your_maps_in_3d_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'share-your-map-section':
                context['is_share_map'] = section.is_visible
                context['share_your_map_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'how-it-works-section':
                context['is_how_it_works'] = section.is_visible
                context['how_it_works_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'what-geodash-offer-section':
                context['is_what_geodash_offer'] = section.is_visible
                context['what_geodash_offers_section'] = SectionManagementModel.objects.get(slug=section.slug)
            if section.slug == 'our-partners-section':
                context['is_our_partners'] = section.is_visible
                context['our_partners_section'] = SectionManagementModel.objects.get(slug=section.slug)
                context['our_partners_section_images'] = SliderImages.objects.filter(is_active=True, section=section)

        return context


@login_required
@user_passes_test(superuser_check)
def section_list(request, template='section_table.html'):
    """
    This view is for updating section sho/hide table from web. Only super admin can manage this table.
    """
    context_dict = {
        "section_list": SectionManagementTable.objects.all().order_by('date_created'),
    }
    return render_to_response(template, RequestContext(request, context_dict))


@login_required
@user_passes_test(superuser_check)
def section_update(request):
    """
    This view is for updating section table from web. Only super admin can manage this table.
    """

    if request.method == 'POST':
        raw_section_ids = request.POST.getlist('section_id')
        section_ids = []
        for id in raw_section_ids:
            section_ids.append(int(id))
        sections = SectionManagementTable.objects.all()
        for section in sections:
            if section.id in section_ids:
                section.is_visible = True
            else:
                section.is_visible = False
            section.save()
        messages.success(request, 'Sections changed successfully')
        return HttpResponseRedirect(reverse('section-list-table'))
    else:
        return HttpResponseRedirect(reverse('section-list-table'))


def add_sections_to_index_page():
    list_of_sections = [
        'slider-section',
        'counter-section',
        'how-it-works-section',
        'featured-layers-section',
        'latest-news-and-updates-section',
        'feature-highlights-of-geodash-section',
        'interportability-section',
        'make-pretty-maps-with-geodash-section',
        'view-your-maps-in-3d-section',
        'share-your-map-section',
        'what-geodash-offer-section',
        'our-partners-section',
    ]
    # if len(list_of_sections) != SectionManagementTable.objects.all().count():
        # SectionManagementTable.objects.all().delete()
        # SectionManagementModel.objects.all().delete()
    created_sections = [section.slug for section in SectionManagementTable.objects.all()]
    for section in list_of_sections:
        if section not in created_sections:
            new_section_table = SectionManagementTable(slug=section, title=section)
            if section in ['slider-section', 'feature-highlights-of-geodash-section', 'interportability-section',
                           'make-pretty-maps-with-geodash-section', 'view-your-maps-in-3d-section', 'latest-news-and-updates-section',
                           'share-your-map-section', 'our-partners-section', 'counter-section']:
                new_section_table.should_update = True
            new_section_table.save()
            new_section = SectionManagementModel(slug=section, title=section)
            new_section.save()


class SliderImageList(ListView):
    """
    This view lists all the slider images
    """
    template_name = 'slider_image_list.html'
    model = SliderImages

    def get_queryset(self):
        return SliderImages.objects.all().order_by('-date_created')[:15]


class SliderImageCreate(CreateView):
    """
    This view is for creating new news
    """
    template_name = 'slider_image_crate.html'
    model = SliderImages

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.section = SectionManagementTable.objects.get(pk=self.kwargs['section_pk'])
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})


    def get_form_class(self):
        slug = SectionManagementTable.objects.get(pk=self.kwargs['section_pk']).slug
        if slug == 'slider-section':
            return SliderImageUpdateForm
        elif slug == 'our-partners-section':
            return OurPartnersImagesUploadForm


class SliderImageUpdate(UpdateView):
    """
    This view is for updating an existing news
    """
    template_name = 'slider_image_crate.html'
    model = SliderImages

    def get_object(self):
        return SliderImages.objects.get(pk=self.kwargs['image_pk'])

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})

    def get_form_class(self):
        slug = SectionManagementTable.objects.get(pk=self.kwargs['section_pk']).slug
        if slug == 'slider-section':
            return SliderImageUpdateForm
        elif slug == 'our-partners-section':
            return OurPartnersImagesUploadForm




class SliderImageDelete(DeleteView):
    """
    This view is for deleting an existing news
    """
    template_name = 'slider_image_delete.html'
    model = SliderImages

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})

    def get_object(self):
        return SliderImages.objects.get(pk=self.kwargs['image_pk'])

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class SectionList(ListView):
    """
    This view lists all the slider images
    """
    template_name = 'slider_image_list.html'
    model = SectionManagementModel

    def get_queryset(self):
        return SectionManagementModel.objects.all().order_by('-date_created')[:15]


class SectionUpdate(UpdateView):
    """
    This view is for updating an existing news
    """
    template_name = 'section_update.html'
    model = SectionManagementModel
    # import pdb; pdb.set_trace()

    def get_form_class(self):
        slug = SectionManagementTable.objects.get(pk=self.kwargs['section_pk']).slug
        if slug == 'slider-section':
            return SliderSectionManagementForm
        elif slug == 'feature-highlights-of-geodash-section':
            return FeatureHighlightsSectionManagementForm
        elif slug == 'interportability-section':
            return InterPortabilitySectionManagementForm
        elif slug == 'make-pretty-maps-with-geodash-section':
            return PrettyMapsSectionManagementForm
        elif slug == 'view-your-maps-in-3d-section':
            return Maps3DSectionManagementForm
        elif slug == 'share-your-map-section':
            return ShareMapSectionManagementForm
        elif slug == 'our-partners-section':
            return OurPartnersSectionManagementForm
        elif slug == 'counter-section':
            return CounterSectionManagementForm
        elif slug == 'latest-news-and-updates-section':
            return LatestNewsUpdateSectionManagementForm


    def get_object(self):
        slug = SectionManagementTable.objects.get(pk=self.kwargs['section_pk']).slug
        return SectionManagementModel.objects.get(slug=slug)

    def get_success_url(self):
        return reverse('section-list-table')

    def get_context_data(self, **kwargs):
        context = super(SectionUpdate, self).get_context_data(**kwargs)
        section = SectionManagementTable.objects.get(pk=self.kwargs['section_pk'])
        context['section'] = section
        slug = section.slug
        base_section = SectionManagementModel.objects.get(slug=slug)
        context['base_section'] = base_section
        context['images'] = SliderImages.objects.filter( section=section)

        return context


class IndexPageImageCreateView(CreateView):
    """
    This view is for creating new news
    """
    template_name = 'slider_image_crate.html'
    model = IndexPageImagesModel
    form_class = IndexPageImageUploadForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        section = SectionManagementTable.objects.get(pk=self.kwargs['section_pk'])
        self.object.section = section
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})


class IndexPageImageListView(ListView):
    """
    This view lists all the slider images
    """
    template_name = 'slider_image_list.html'
    model = IndexPageImagesModel

    def get_queryset(self):
        return IndexPageImagesModel.objects.all().order_by('-date_created')[:15]


class IndexPageImageDelete(DeleteView):
    """
    This view is for deleting an image
    """
    model = IndexPageImagesModel

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})

    def get_object(self):
        return IndexPageImagesModel.objects.get(pk=self.kwargs['image_pk'])

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class IndexPageImageUpdate(UpdateView):
    """

    """
    model = IndexPageImagesModel

    def get_success_url(self):
        return reverse('section-update-view', kwargs={'section_pk': self.kwargs['section_pk']})

    def get_object(self):
        return IndexPageImagesModel.objects.get(pk=self.kwargs['image_pk'])


def activateimage(request, image_pk, section_pk):
    """

    :param request:
    :return:
    """
    if request.method == 'POST':
        section = SectionManagementTable.objects.get(pk=section_pk)
        images = IndexPageImagesModel.objects.filter(section=section)
        for image in images:
            if image.id == image_pk:
                image.is_active = True
            else:
                image.is_active = False
            image.save()

        return HttpResponseRedirect(reverse('section-update-view', args=(section_pk,)))


class TermsAndConditionView(ListView):
    """
    This view returns terms and conditions for geodash.
    """
    template_name = 'termsandcondition.html'
    model = FooterSectionDescriptions

    def get_queryset(self):
        if FooterSectionDescriptions.objects.all().count() == 0:
            terms_and_condition = FooterSectionDescriptions(title='TERMS AND CONDITIONS', slug='terms-and-condition',
                                                           description=terms_and_condition_description)
            privacy_policy = FooterSectionDescriptions(title='PRIVACY POLICY', slug='privacy-policy',
                                                           description=privacy_policy_description)
            terms_of_use = FooterSectionDescriptions(title='TERMS OF USE', slug='terms-of-use',
                                                           description=terms_of_use_description)
            terms_and_condition.save()
            privacy_policy.save()
            terms_of_use.save()

        return FooterSectionDescriptions.objects.get(slug=self.kwargs['slug'])



class TermsAndConditionUpdateView(UpdateView):
    """
    This view is for update sections in footer section
    """
    template_name = 'termsandcondition_update.html'
    model = FooterSectionDescriptions

    def dispatch(self, request, *args, **kwargs):
        response = super(TermsAndConditionUpdateView, self).dispatch(request, *args, **kwargs)
        if not self.request.user.is_superuser:
            return HttpResponseRedirect(reverse('footer-section-view', kwargs={'slug': self.kwargs['slug']} ))
        else:
            return response

    def get_success_url(self):
        return reverse('footer-section-view', kwargs={'slug': self.kwargs['slug']})

    def get_object(self):
        return FooterSectionDescriptions.objects.get(slug=self.kwargs['slug'])

    def get_form_class(self):
        return FooterSubSectionsUpdateForm