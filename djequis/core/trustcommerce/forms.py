from django import forms
from django.db import models


class DownloadForm(forms.Form):
    fields = ('record', 'activity', )


class ContactForm(forms.Form):
    name = forms.CharField(label='Your name', required=False)
    comment = forms.CharField(label='Comment', required=False)

##############################################################
# This is just a test concept...
# class CountryForm(forms.Form):
#     OPTIONS = (
#         ("AUT", "Austria"),
#         ("DEU", "Germany"),
#         ("NLD", "Neitherlands"),
#     )
#     Countries = forms.MultipleChoiceField(
#         widget=forms.CheckboxSelectMultiple,
#         choices=OPTIONS)
##############################################################


# activity = forms.CharField(max_length=50)
    # record = forms.CharField(max_length=20)
    # datasource = forms.CharField(max_length=50)
    # selWTCode = forms.CharField(max_length=10)
    # precamp = forms.CharField(max_length=3)
    # term = forms.CharField(max_length=5)
    # CheckedVal = forms.CharField(max_length=2)
    #
    # source = forms.CharField(       # A hidden input for internal use
    #     max_length=50,              # tell from which page the user sent the message
    #     widget=forms.HiddenInput()
    # )

    # def clean(self):
    #     cleaned_data = super(ContactForm, self).clean()
    #     activity = cleaned_data.get('activity')
    #     record_id = cleaned_data.get('record_id')
    #     CheckedVal = cleaned_data.get('CheckedVal')
    #     if not name and not email and not message:
    #         raise forms.ValidationError('You have to write something!')
