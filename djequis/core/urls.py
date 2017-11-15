from django.conf.urls import include, url


urlpatterns = [
    # admissions
    url(
        r'^admissions/', include('djequis.core.admissions.urls')
    ),
    # test app
    url(
        r'^test/', include('djequis.core.test.urls')
    ),
]
