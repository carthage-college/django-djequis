from django.conf.urls import url

from djequis.core.schoology import views


urlpatterns = [
    # trigger: grades
    url(
        r'^trigger/grades/$',
        views.trigger_grades, name='trigger_grades'
    )
]
