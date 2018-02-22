from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from djequis.core.admissions.sms.forms import SendForm

from djzbar.decorators.auth import portal_auth_required

from twilio.rest import Client


@portal_auth_required(
    #group='Admissions SMS', session_var='DJEQUIS_AUTH',
    session_var='DJEQUIS_AUTH',
    redirect_url=reverse_lazy('access_denied')
)
@csrf_exempt
def send(request):

    if request.method=='POST':
        form = SendForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            client = Client(
                settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
            )
            client.messages.create(
                to = data['phone'],
                from_ = settings.TWILIO_FROM_PHONE,
                # use parentheses to prevent extra whitespace
                body = (data['message'])
            )
            return HttpResponseRedirect(
                reverse_lazy('sms_send_success')
            )
    else:
        form = SendForm()
    return render(
        request, 'core/admissions/sms/form.html',
        {'form': form,}
    )


def send_bulk(request):
    return render(
        request, 'core/admissions/sms/form_bulk.html',
        {'form': form,}
    )


def search(request):
    return render(
        request, 'core/admissions/sms/search.html'
    )
