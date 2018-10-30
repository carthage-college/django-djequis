from django.conf.urls import url
from djequis.core.trustcommerce import views
from djequis.core.trustcommerce.views import home, details, download

urlpatterns = [
    # home
    url(r'^$', views.home, name='trustcommerce_home'),

    # Details
    url(r'^(?P<activity>\d+) details$', views.details, name='trustcommerce_details'),

    # Download
    url(r'^(?P<value>\d+)(?P<activity>\d+) download$', views.download, name='trustcommerce_download'),

]

