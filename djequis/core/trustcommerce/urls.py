from django.conf.urls import url

from djequis.core.trustcommerce import views


urlpatterns = [
    # home
    url(
        r'^$',
        views.home, name='trustcommerce_home'
    )
]
