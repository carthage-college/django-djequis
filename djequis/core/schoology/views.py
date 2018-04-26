from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from djequis.core.schoology.sql import SELECT_GRADE, UPDATE_GRADE

from djzbar.utils.informix import get_session

import json
import logging
logger = logging.getLogger('djequis')


@csrf_exempt
def trigger_grades(request):
    """
    Event trigger callback from API for updates to grades
    """

    if request.method=='POST':

        data = json.loads(request.body)

        session = get_session(settings.INFORMIX_EARL)

        for grade in data['data']:
            # 01234567890123456789012345678
            # 2018;RC;FRN 2010;01;UG17;UNDG
            # yr  sess crs_no  sec cat prog
            try:
                school_code = grade['section_school_code']

                if settings.DEBUG:
                    sql = SELECT_GRADE(
                        coursekey = school_code,
                        student_number = grade['school_uid']
                    )
                else:
                    sql = UPDATE_GRADE(
                        grade = grade['updated_overall_grade'],
                        coursekey = school_code,
                        student_number = grade['school_uid']
                    )

                logger.debug("sql = {}".format(sql))

                response = session.execute(sql)
            except:
                logger.debug('bad data = {}'.format(grade))

        session.close()

        msg = 'Success'
    else:
        # requires POST
        msg = "Requires POST"

    return HttpResponse(
        msg, content_type='text/plain; charset=utf-8'
    )
