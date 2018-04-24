from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import logging
logger = logging.getLogger('djequis')


@csrf_exempt
def trigger_grades(request):
    """
    Event trigger callback from API for updates to grades
    """

    if request.method=='POST':
        data = request.POST
        logger.debug('uid = {}'.format(data['uid']))
        logger.debug('timestamp = {}'.format(data['timestamp']))
        logger.debug('type = {}'.format(data['type']))
        logger.debug('data = {}'.format(data['data']))
        msg = data['data']
    else:
        # requires POST
        msg = "Requires POST"

    return HttpResponse(
        msg, content_type='text/plain; charset=utf-8'
    )
