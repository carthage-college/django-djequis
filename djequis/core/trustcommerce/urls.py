from django.conf.urls import url
from djequis.core.trustcommerce import views
from djequis.core.trustcommerce.views import home, details, download,\
    download2

urlpatterns = [

    # home
    url(r'^$', views.home, name='trustcommerce_home'),

    # Download2
    url(r'^download2$', views.download2,
        name='trustcommerce_download2'),


    # Download
    url(r'^(?P<id>\d+)(?P<activity>\d{1,2}) download$', views.download,
        name='trustcommerce_download'),


    # # Forms Experiment
    # url(r'^$', views.contact, name='contact'),


    # Details
    url(r'^(?P<activity>\d+) details$', views.details, name='trustcommerce_details'),



]

