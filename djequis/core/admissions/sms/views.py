from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

from djequis.core.admissions.sms.forms import SendForm
from djequis.core.admissions.sms.manager import Message
from djequis.core.admissions.sms.client import twilio_client as client

from djzbar.decorators.auth import portal_auth_required

MESSAGING_SERVICE_SID = settings.TWILIO_TEST_MESSAGING_SERVICE_SID


@portal_auth_required(
    #group='Admissions SMS', session_var='DJEQUIS_AUTH',
    session_var='DJEQUIS_AUTH',
    redirect_url=reverse_lazy('access_denied')
)
@csrf_exempt
def send(request):

    initial = {}

    if request.method=='POST':
        form = SendForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            response = client.messages.create(
                to = data['phone_to'],
                #from_ = settings.TWILIO_TEST_PHONE_FROM,
                messaging_service_sid = MESSAGING_SERVICE_SID,
                # use parentheses to prevent extra whitespace
                body = (data['message'])
            )

            message = Message()
            sid = response.sid
            delivered = message.status(sid, 'delivered')

            if delivered == 'delivered':
                messages.add_message(
                    request,messages.SUCCESS,"Your message has been sent.",
                    extra_tags='success'
                )
            else:
                messages.add_message(
                    request, messages.ERROR,
                    """
                    Some recipients did not receive your message.
                    """,
                    extra_tags='error'
                )

            return HttpResponseRedirect(
                reverse_lazy('sms_send')
            )

    else:
        if settings.DEBUG:
            initial = {
                'phone_to': settings.TWILIO_TEST_PHONE_TO,
                'message': settings.TWILIO_TEST_MESSAGE
            }
        form = SendForm(initial=initial)

    return render(
        request, 'core/admissions/sms/form.html', {'form': form}
    )


def send_bulk(request):
    return render(
        request, 'core/admissions/sms/form_bulk.html'
    )


def detail(request, sid):
    return render(
        request, 'core/admissions/sms/detail.html'
    )


def search(request):
    return render(
        request, 'core/admissions/sms/search.html'
    )
