from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, get_object_or_404
from twilio.rest import Client

from djequis.core.admissions.forms import MyForm
from djtools.utils.mail import send_mail

#from django_twilio.decorators import twilio_view


# TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

def sendsms(request):

    if request.method=='POST':
        form = MyForm(request.POST, request.FILES)
        if form.is_valid():
            client = Client(
                settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
            )
            client.messages.create(
                #to = '+12627050681',
                to = settings.TWILIO_TEST_FON,
                from_ = '+12629474836',
                # use parentheses to prevent extra whitespace
                body = (
                    "test text message via Django after form submission, "
                    "template fix, and code formatting clean-up :)"
                )
            )
            #email = settings.DEFAULT_FROM_EMAIL
            #if data.email:
            #    email = data.email
            #subject = "[Submit] {} {}".format(data.first_name,data.last_name)
            #send_mail(
            #    request,TO_LIST, subject, email,"/email.html", data, BCC
            #)
            return HttpResponseRedirect(
                reverse_lazy("sendsms_success")
            )
    else:
        form = MyForm()
    return render(
        request, 'core/admissions/twilio/form.html',
        {"form": form,}
    )

def search(request):
    return render(
        request, 'core/admissions/twilio/search.html'
    )
