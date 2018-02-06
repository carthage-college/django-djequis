from django.conf.urls import url
from django.views.generic import TemplateView

from djequis.core.admissions import views


urlpatterns = [
    url(
        r'^sendsms/$',
        views.sendsms, name='sendsms'
    ),
    url(
        r'^search/$',
        views.search, name='sendsms_search'
    ),
    url(
        r'^sendsms/success/$',
        TemplateView.as_view(
            template_name='core/admissions/twilio/success.html'
        ),
        name='sendsms_success'
    ),
]
