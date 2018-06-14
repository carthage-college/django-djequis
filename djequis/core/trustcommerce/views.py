from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.db import connections

from djtools.utils.mail import send_mail
from djtools.utils.database import dictfetchall

from djzbar.decorators.auth import portal_auth_required

from djequis.core.trustcommerce.sql import *

from itertools import chain
from operator import attrgetter, itemgetter


@portal_auth_required(
    session_var='DJEQUIS_AUTH', redirect_url=reverse_lazy('access_denied')
)
def home(request):
    '''
    '''

    tcpayflow = connections['tcpayflow'].cursor()
    djforms = connections['djforms'].cursor()

    tcpayflow.execute(PCE_TRANSACTIONS)
    tcpayflow_results = tcpayflow.fetchall()
    djforms.execute(PSM_TRANSACTIONS)
    djforms_results = djforms.fetchall()

    objects = sorted(
        chain(tcpayflow_results, djforms_results),
        key=lambda instance: instance[5]
        #key=attrgetter('datecreated')
    )
    #objects = list(chain(tcpayflow_results, djforms_results))

    return render(
        request, 'core/trustcommerce/home.html',
        {'objects': objects,}
    )
