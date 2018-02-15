# -*- coding: utf-8 -*-

from django import forms


class WisAct284Form(forms.Form):

    dispersed = forms.BooleanField(required=False)
    headers = forms.BooleanField(
        label="Include headers", required=False
    )

