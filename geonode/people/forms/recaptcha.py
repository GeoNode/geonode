from django import forms
from allauth.account.forms import LoginForm

try:
    from captcha.fields import ReCaptchaField
except ImportError:
    from django_recaptcha.fields import ReCaptchaField


class AllauthReCaptchaSignupForm(forms.Form):
    captcha = ReCaptchaField(label=False)
    
    def signup(self, request, user):
        """Required, or else it thorws deprecation warnings"""
        pass


class AllauthRecaptchaLoginForm(LoginForm):
    captcha = ReCaptchaField(label=False)

    def login(self, *args, **kwargs):
        return super(AllauthRecaptchaLoginForm, self).login(*args, **kwargs)
