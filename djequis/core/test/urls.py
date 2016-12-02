from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from djequis.core.test.models import FooBar


urlpatterns = patterns('djequis.core.test.views',
    # foobar crud
    url(
        r'^foobar/$', 'create_form', name='foobar_create_form'
    ),
    # foobar succes view after submit
    url(
        r'^foobar/success/$',
        TemplateView.as_view(
            template_name='foobar/done.html'
        ),
        name='foobar_success'
    ),
    # foobar update
    url(
        r'^foobar/(?P<fid>\d+)/update/$',
        'update_form', name='foobar_update_form'
    ),
    # foobar detail
    url(
        r'^foobar/(?P<fid>\d+)/detail/$',
        'detail', name='foobar_detail'
    ),
    # archives
    url(
        r'^foobar/archives/$',
        TemplateView.as_view(
            template_name='foobar/archives.html',
        ),
        {"data":FooBar.objects.all()},
        name="foobar_archives"
    ),
)
