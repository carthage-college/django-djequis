# -*- coding: utf-8 -*-

from django import forms

from localflavor.us.forms import USPhoneNumberField


class SendForm(forms.Form):

    phone = USPhoneNumberField(
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'required'})
    )
    message = forms.CharField(
        widget=forms.Textarea,
        help_text = '<span id="chars">140</span> characters remaining'
    )
