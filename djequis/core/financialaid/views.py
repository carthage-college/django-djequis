from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse_lazy

from djequis.core.financialaid.forms import WisAct284Form
from djequis.sql.wisact284 import WIS_ACT_284_SQL
from djequis.core.financialaid.utils import csv_gen

from djzbar.decorators.auth import portal_auth_required
from djzbar.utils.informix import do_sql

import csv
import time
import logging
logger = logging.getLogger(__name__)

EARL = settings.INFORMIX_EARL
DEBUG = settings.INFORMIX_DEBUG


@portal_auth_required(
    group='carthageStaffStatus', session_var='DJEQUIS_AUTH',
    redirect_url=reverse_lazy('access_denied')
)
def wisact284(request):

    sql = None
    objects = None
    if request.method=='POST':
        form = WisAct284Form(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            stat = '"AA","AD","AP","EA"'
            if data['dispersed']:
                stat = '"AD"'
            sql = WIS_ACT_284_SQL(amt_stat = stat)
            logger.debug("wisact284 sql = {}".format(sql))
            objects = do_sql(sql, earl=EARL)

            datetimestr = time.strftime("%Y%m%d%H%M%S")
            # College Cost Meter file name
            ccmfile = (
                'CCM-{}.csv'.format(datetimestr)
            )

            response = HttpResponse(content_type="text/csv; charset=utf-8")
            content = 'attachment; filename={}'.format(ccmfile)
            response['Content-Disposition'] = content

            writer = csv.writer(response)
            csv_gen(objects, writer)

            return response

    else:
        form = WisAct284Form()

    return render(
        request, 'core/financialaid/wisact284.html',
        {'form':form, 'objects':objects, 'sql':sql}
    )
