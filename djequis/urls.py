from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView, TemplateView

from django.contrib import admin

admin.autodiscover()
admin.site.site_header = 'Carthage College'

handler404 = 'djtools.views.errors.four_oh_four_error'
handler500 = 'djtools.views.errors.server_error'

urlpatterns = patterns('',
    url(
        r'^admin/', include(admin.site.urls)
    ),
    # core app
    url(
        r'^core/', include("djequis.core.urls")
    ),
    url(
        r'^denied/$',
        TemplateView.as_view(
            template_name="denied.html"
        ), name="access_denied"
    ),
    # redirect
    #url(
    #    r'^$', RedirectView.as_view(url="/foobar/")
    #),
)
