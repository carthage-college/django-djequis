from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.db import connections
from djtools.utils.mail import send_mail
from djtools.utils.database import dictfetchall
from djzbar.decorators.auth import portal_auth_required
from djequis.core.trustcommerce.sql import *
from django.views import generic
# from djequis.core.trustcommerce.summaries import *
from itertools import chain
from operator import attrgetter, itemgetter
from .forms import ContactForm


@portal_auth_required(
    session_var='DJEQUIS_AUTH', redirect_url=reverse_lazy('access_denied')
)


def download2(request):
    return render(request, 'core/trustcommerce/download.html' )


def details(request, activity):
    tcpayflow = connections['tcpayflow'].cursor()
    djforms = connections['djforms'].cursor()
    tcpayflow.execute(PCE_TRANSACTIONS_ACTIVITY.format(activity))
    tcpayflow_results = tcpayflow.fetchall()
    djforms.execute(PSM_TRANSACTIONS_ACTIVITY.format(activity))
    djforms_results = djforms.fetchall()
    objects = sorted(
        chain(tcpayflow_results, djforms_results),
        key=lambda instance: instance[5]
        #key=attrgetter('datecreated')
    )

    return render(
        request, 'core/trustcommerce/details.html',
        {'objects': objects, 'activity': activity}
    )

def download(request, id, activity):
    tcpayflow = connections['tcpayflow'].cursor()
    djforms = connections['djforms'].cursor()
    tcpayflow.execute(PCE_TRANSACTIONS_CHECKED.format(id, activity))
    tcpayflow_results = tcpayflow.fetchall()
    djforms.execute(PSM_TRANSACTIONS_CHECKED.format(id, activity))
    djforms_results = djforms.fetchall()
    objects = sorted(
        chain(tcpayflow_results, djforms_results),
        key=lambda instance: instance[5]
        #key=attrgetter('datecreated')
    )

    return render(
        request, 'core/trustcommerce/download.html',
        {'objects': objects, 'id': id, 'activity': activity}
    )

def home(request):
    tcpayflow = connections['tcpayflow'].cursor()
    djforms = connections['djforms'].cursor()

    tcpayflow.execute(PCE_SUMMARY)
    tcpayflow_summary = tcpayflow.fetchall()
    djforms.execute(PSM_SUMMARY)
    djforms_summary = djforms.fetchall()

    objects = sorted(
        chain(tcpayflow_summary, djforms_summary),
        key=lambda instance: instance[2]
        # key=attrgetter('datecreated')
    )
    return render(
        request, 'core/trustcommerce/home.html',
        {'objects': objects, }
    )



def index(request):
    return HttpResponseRedirect("Hello, hello")


# def contact(request):
#     # if request.method == "POST":
#     form = ContactForm(request.POST)
#     # if form.is_valid():
#     # s_name = form.cleaned_data[' name ']
#     # s_results = SomeTable.objects.filter(name=s_name)
#     # return render(request, 'testForms.html', {'form': form, 's_results': s_results})
#     # else:
#     #     form = SearchForm()
#     return render(request, 'core/trustcommerce/testForms.html', {'form': form, })
