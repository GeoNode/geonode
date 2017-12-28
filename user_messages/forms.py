from django import forms

from django.contrib.auth import get_user_model

from user_messages.models import Message


class MyModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name_long


class NewMessageForm(forms.Form):

    to_user = MyModelChoiceField(label="To",queryset=get_user_model().objects.exclude(username='AnonymousUser').order_by('username'))

    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(NewMessageForm, self).__init__(*args, **kwargs)
        if self.initial.get("to_user") is not None:
            qs = self.fields["to_user"].queryset.filter(pk=self.initial["to_user"])
            self.fields["to_user"].queryset = qs
    
    def save(self):
        data = self.cleaned_data
        return Message.objects.new_message(self.user, [data["to_user"]],
            data["subject"], data["content"])


class NewMessageFormMultiple(forms.Form):

    to_user = forms.ModelMultipleChoiceField(label="To",queryset=get_user_model().objects.exclude(username='AnonymousUser')) 
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(NewMessageFormMultiple, self).__init__(*args, **kwargs)
        if self.initial.get("to_user") is not None:
            qs = self.fields["to_user"].queryset.filter(pk__in=self.initial["to_user"])
            self.fields["to_user"].queryset = qs
    
    def save(self):
        data = self.cleaned_data
        return Message.objects.new_message(self.user, data["to_user"],
            data["subject"], data["content"])


class MessageReplyForm(forms.Form):
    
    content = forms.CharField(widget=forms.Textarea)
    
    def __init__(self, *args, **kwargs):
        self.thread = kwargs.pop("thread")
        self.user = kwargs.pop("user")
        super(MessageReplyForm, self).__init__(*args, **kwargs)
    
    def save(self):
        return Message.objects.new_reply(self.thread, self.user,
            self.cleaned_data["content"])


class SearchMessageForm(forms.Form):
    search = forms.CharField(label='Search', max_length=100)
