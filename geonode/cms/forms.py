from django import forms
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

from suit.widgets import HTML5Input


from models import SliderImages, SectionManagementModel, IndexPageImagesModel
from geonode.cms.models import FooterSectionDescriptions


class SliderImageUpdateForm(forms.ModelForm):

    class Meta:
        model = SliderImages
        fields = ['title', 'descripton', 'image', 'is_active']

    def clean_image(self):
         image = self.cleaned_data.get('image',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 1920 or h != 600:
                   raise ValidationError("Please upload image with dimension(w * h = 1920 * 600)")
             return image
         else:
             raise ValidationError("Couldn't read uploaded image")


class IndexPageImageUploadForm(forms.ModelForm):
    """

    """
    class Meta:
        model = IndexPageImagesModel
        fields = ['title', 'descripton', 'image']


class SliderSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['background_color']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(SliderSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'



class FeatureHighlightsSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'section_sub_title', 'description', 'background_color', 'image1', 'image2', 'image3', 'image4', 'image5']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(FeatureHighlightsSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'

    def clean_image1(self):
         image = self.cleaned_data.get('image1',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 300 or h != 330:
                   raise ValidationError("Please upload image with dimension(w * h = 300 * 300)")
             return image
         else:
             raise ValidationError("Please select an image")

    def clean_image2(self):
         image = self.cleaned_data.get('image2',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 300 or h != 330:
                   raise ValidationError("Please upload image with dimension(w * h = 300 * 300)")
             return image
         else:
             raise ValidationError("Please select an image")

    def clean_image3(self):
         image = self.cleaned_data.get('image3',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 300 or h != 330:
                   raise ValidationError("Please upload image with dimension(w * h = 300 * 300)")
             return image
         else:
             raise ValidationError("Please select an image")

    def clean_image4(self):
         image = self.cleaned_data.get('image4',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 300 or h != 330:
                   raise ValidationError("Please upload image with dimension(w * h = 300 * 300)")
             return image
         else:
             raise ValidationError("Please select an image")

    def clean_image5(self):
         image = self.cleaned_data.get('image5',False)
         if image:
             w, h = get_image_dimensions(image)
             if w != 300 or h != 330:
                   raise ValidationError("Please upload image with dimension(w * h = 300 * 300)")
             return image
         else:
             raise ValidationError("Please select an image")



class InterPortabilitySectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'description', 'background_color', 'image1']
        widgets = {
            'background_color': HTML5Input(input_type='color', attrs={'size': 10}),
        }
    def __init__(self, *args, **kwargs):
        super(InterPortabilitySectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'

    def clean_image1(self):
         image = self.cleaned_data.get('image1',False)
         if not image:
             raise ValidationError("Please select an image")
         return image




class PrettyMapsSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'description', 'background_color', 'image1']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(PrettyMapsSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'

    def clean_image1(self):
         image = self.cleaned_data.get('image1',False)
         if not image:
             raise ValidationError("Please select an image")
         return image


class Maps3DSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'description', 'background_color', 'image1']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(Maps3DSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'

    def clean_image1(self):
         image = self.cleaned_data.get('image1',False)
         if not image:
             raise ValidationError("Please select an image")
         return image


class ShareMapSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'description', 'background_color', 'image1']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(ShareMapSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'

    def clean_image1(self):
         image = self.cleaned_data.get('image1',False)
         if not image:
             raise ValidationError("Please select an image")
         return image


class OurPartnersSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'background_color']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(OurPartnersSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'


class OurPartnersImagesUploadForm(forms.ModelForm):
    class Meta:
        model = SliderImages
        fields = ['image', 'is_active', 'logo_url']


class CounterSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'background_color']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(CounterSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'


class FooterSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['title', 'background_color']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(FooterSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'


class FooterImagesUploadForm(forms.ModelForm):
    class Meta:
        model = SliderImages
        fields = ['image', 'is_active', 'logo_url']


class LatestNewsUpdateSectionManagementForm(forms.ModelForm):

    class Meta:
        model = SectionManagementModel
        fields = ['background_color']
        widgets = {
            'background_color': HTML5Input(input_type='color'),
        }
    def __init__(self, *args, **kwargs):
        super(LatestNewsUpdateSectionManagementForm, self).__init__(*args, **kwargs)
        self.fields['background_color'].widget.attrs['style'] = 'width:70px; height:40px;'


class FooterSubSectionsUpdateForm(forms.ModelForm):

    class Meta:
        model = FooterSectionDescriptions
        fields = ['title', 'description']
