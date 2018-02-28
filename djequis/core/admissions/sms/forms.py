# -*- coding: utf-8 -*-

from django import forms

from localflavor.us.forms import USPhoneNumberField


class SendForm(forms.Form):

    phone_to = USPhoneNumberField(
        label = "To",
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'required'}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'required'}),
        help_text = '<span id="chars">160</span> characters remaining'
    )

    def clean_phone(self):
        '''
        0 or 1 or Y/N ?
        opt_out Y/N logic is backwards from what may be intuitive;
        opt_out = "Y" should mean "do not send text".

        opt_out = 1 means you can receive sms at this number
        opt_out = 0 means you cannot receive sms
        '''
        opt_out = False
        #opt_out = True
        cd = self.cleaned_data
        phone = cd.get('phone')
        if opt_out:
            raise forms.ValidationError(
                """
                This student has chosen to opt-out of phone contact
                """
            )
        return cd['phone']
