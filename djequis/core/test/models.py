# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models, connection
from django.contrib.auth.models import User

# Requires a get_slug() method on the model
from djtools.fields.helpers import upload_to_path
from djtools.fields.validators import MimetypeValidator


class FooBar(models.Model):
    '''
    Model: FooBar
    '''
    created_by = models.ForeignKey(
        User,
        verbose_name='Created by',
        related_name='foobar_created_by',
        editable=False
    )
    updated_by = models.ForeignKey(
        User,
        verbose_name='Updated by',
        related_name='foobar_updated_by',
        editable=False, null=True, blank=True
    )
    created_at = models.DateTimeField(
        'Date Created', auto_now_add=True,
        editable=False
    )
    updated_at = models.DateTimeField(
        'Date Updated', auto_now=True,
        editable=False
    )
    title = models.CharField(
        max_length=16,
    )
    description = models.TextField(
        help_text="""
            Describe your foobar (~500 characters)
        """
    )
    phile = models.FileField(
        upload_to=upload_to_path,
        validators=[MimetypeValidator('application/pdf')],
        help_text="PDF format",
        max_length = '768',
    )
    status = models.BooleanField(
        "Foobar status",
        default=False
    )

    class Meta:
        ordering  = ['-created_at']
        get_latest_by = 'created_at'
        # uncomment if you want to force a table name different from default,
        # which is app_modelname
        db_table = 'core_test_foobar'

    def __unicode__(self):
        '''
        Default data for display
        '''
        return self.created_by.username

    @models.permalink
    def get_absolute_url(self):
        return ('foobar_detail', [str(self.id)])

    def get_slug(self):
        return 'foobar/'

