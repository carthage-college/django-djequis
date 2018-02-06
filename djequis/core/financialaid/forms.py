# -*- coding: utf-8 -*-

from django import forms


class WisAct284Form(forms.ModelForm):

    dispersed = forms.BooleanField(required=False)

