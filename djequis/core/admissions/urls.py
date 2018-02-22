from django.conf.urls import include, url


urlpatterns = [
    url(
        r'^sms/', include('djequis.core.admissions.sms.urls')
    ),
]
