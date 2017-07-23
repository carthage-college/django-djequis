# -*- coding: utf-8 -*-

from django import forms

from djequis.core.admissions.models import MyModel

class MyForm(forms.ModelForm):

    class Meta:
        model = MyModel
        # either fields or exclude is required
        fields = '__all__'

