from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage

from djequis.core.test.models import FooBar

class FooBarAdmin(admin.ModelAdmin):
    class Media:
        '''
        css = {
            'all': ('https://www.carthage.edu/static/vendor/summernote/summernote.css',)
        }
        js = (
            'https://www.carthage.edu/static/vendor/summernote/summernote.min.js',
            '/static/jx/js/admin.js'
        )
        '''
        js = [
            'https://www.carthage.edu/static/djtinue/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            'https://www.carthage.edu/static/djtinue/grappelli/tinymce_setup/tinymce_setup.js',
        ]


    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

admin.site.register(FooBar, FooBarAdmin)


class FlatPageCustom(FlatPageAdmin):
    '''
    Override the FlatPage admin so we can insert the js/css for WYSIWYG editor
    '''

    class Media:
        '''
        css = {
            'all': ('https://www.carthage.edu/static/vendor/summernote/summernote.css',)
        }
        js = (
            'https://www.carthage.edu/static/vendor/summernote/summernote.min.js',
            '/static/jx/js/admin.js'
        )
        '''
        js = [
            'https://www.carthage.edu/static/djtinue/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            'https://www.carthage.edu/static/djtinue/grappelli/tinymce_setup/tinymce_setup.js',
        ]

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageCustom)
