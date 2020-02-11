from django.conf.urls import url
from djequis.core.trustcommerce import views


urlpatterns = [
    # home
    url(r'^$', views.home, name='trustcommerce_home'),
    # Download
    url(r'^(?P<id>\d+)(?P<activity>\d+) download$', views.download,
        name='trustcommerce_download'),
    # Details
    url(
        r'^(?P<activity>\d+) details$', views.details,
        name='trustcommerce_details'
    ),
]

