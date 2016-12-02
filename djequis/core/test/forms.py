# -*- coding: utf-8 -*-

from django import forms

from djequis.core.test.models import FooBar


class FooBarForm(forms.ModelForm):

    class Meta:
        model = FooBar
        # either fields or exclude is required
        #fields = '__all__'
        exclude = ['status']

