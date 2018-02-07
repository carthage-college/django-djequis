from django.conf import settings
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy

from djequis.core.financialaid.forms import WisAct284Form
from djequis.sql.wisact284 import WIS_ACT_284_SQL

from djzbar.utils.informix import do_sql

import logging
logger = logging.getLogger(__name__)

EARL = settings.INFORMIX_EARL
DEBUG = settings.INFORMIX_DEBUG


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
    else:
        form = WisAct284Form()

    return render(
        request, 'core/financialaid/wisact284.html',
        {'form':form, 'objects':objects, 'sql':sql}
    )
