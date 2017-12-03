# -*- coding: utf-8 -*-
import os, sys

# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

from django.conf import settings
from django.db import connections


def main():
    """
    mysql database connection example
    """

    print("Establish database connection\n")
    cursor = connections['admissions'].cursor()

    print("Raw SQL\n")
    sql = 'SELECT * FROM app_vouchers LIMIT 10'
    print(sql)

    print("Excecute SQL incantation\n")
    cursor.execute(sql)
    results = cursor.fetchall()

    print("Results row by row\n")
    columns = ['id','ctgry','code','description','createdate','expiration']
    for row in results:

        # for the ** operator, see:
        # https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-listsa
        # dict just creates a new dictionary
        # https://docs.python.org/2/library/functions.html#func-dict
        # if you want to see how zip works:
        # https://docs.python.org/2/library/functions.html#zip
        # uncomment the following line
        #print zip(columns, row)

        print "{id} {ctgry} {code} {description}".format(
            **dict(zip(columns, row))
        )


######################
# shell command line
######################

if __name__ == "__main__":

    sys.exit(main())
