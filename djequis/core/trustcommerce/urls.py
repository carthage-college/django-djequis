from django.conf.urls import url

from djequis.core.trustcommerce import views
from djequis.core.trustcommerce.views import home, details, index

urlpatterns = [
    # home
    url(r'^$', views.home, name='trustcommerce_home'),
    # Details
    # Details
    url(r'^(?P<activity>\d+) details$', views.details, name='trustcommerce_details')
    # url(r'^details$', views.details, name='trustcommerce_details')

]

