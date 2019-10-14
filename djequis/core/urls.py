from django.conf.urls import include, url


urlpatterns = [
    url(
        r'^schoology/', include('djequis.core.schoology.urls')
    ),
    url(
        r'^trustcommerce/', include('djequis.core.trustcommerce.urls')
    ),
]
