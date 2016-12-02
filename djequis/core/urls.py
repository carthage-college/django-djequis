from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # admissions
    url(
        r'^admissions/', include("djequis.core.admissions.urls")
    ),
    # registrar
    url(
        r'^registrar/', include("djequis.core.registrar.urls")
    ),
    # test app
    url(
        r'^test/', include("djequis.core.test.urls")
    ),
)
