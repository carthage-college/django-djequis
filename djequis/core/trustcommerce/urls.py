from django.conf.urls import url
from djequis.core.trustcommerce import views
from djequis.core.trustcommerce.views import home, details, index, download

app_name = 'trust_commerce'
urlpatterns = [

    # Download CSV
    url(r'^$', views.download, name='download'),

    # home
    url(r'^$', views.home, name='trustcommerce_home'),

    # Details
    url(r'^(?P<activity>\d+) details$', views.details, name='trustcommerce_details'),


]

