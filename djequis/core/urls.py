from django.conf.urls import include, url


urlpatterns = [
    # admissions
    #url(
        #r'^admissions/', include('djequis.core.admissions.urls')
    #),
    url(
        r'^financial-aid/', include('djequis.core.financialaid.urls')
    ),
    url(
        r'^trustcommerce/', include('djequis.core.trustcommerce.urls')
    ),
]
