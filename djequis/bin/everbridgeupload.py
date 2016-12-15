import io
import os
import re
import sys
import ftplib
import csv
import argparse

from dateutil.relativedelta import relativedelta
from StringIO import StringIO

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

import django
django.setup()

from django.conf import settings
from django.template import loader, Context
from django.utils.encoding import smart_bytes

from djzbar.utils.informix import do_sql
from djtools.fields import NOW

EARL = settings.INFORMIX_EARL
NEXT_YEAR = NOW + relativedelta(years=1)

# set up command-line options
desc = """
    Terradotta Synchronization
"""
parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)

def paint_xml(data):

    t = loader.get_template('oclc/personas.xml')
    c = Context({ 'objs': data, 'next_year':NEXT_YEAR })
    output = t.render(c)
    #print output
    return output

def main():
    sql = '''
        SELECT UNIQUE
            TRIM(id_rec.firstname) firstname, id_rec.middlename[1,1] middleinitial, TRIM(id_rec.lastname) lastname, TRIM(id_rec.suffixname) suffix, id_rec.id::varchar(10) ExternalID,
            'United States' as Country, 'Carthage College' as BusinessName, 'Employee' as RecordType,
            CASE WHEN	NVL(ens_rec.opt_out, 1)	=	1	THEN	ens_rec.phone
                                                        ELSE	''
            END as Phone1, 'United States' as PhoneCountry1,
            CASE WHEN	school_rec.phone	=	'___-___-____'	THEN	''
                                                                ELSE	TRIM(school_rec.phone)
            END as Phone2, 'United States' as PhoneCountry2, TRIM(email_rec.line1) as EmailAddress1, TRIM(ens_rec.line1) || TRIM(ens_rec.line2) as EmailAddress2,
            CASE WHEN	NVL(ens_rec.opt_out, 1)	=	1	THEN	TRIM(ens_rec.phone)
                                                        ELSE	''
            END as SMS1, 'United States' as SMS1Country, 'Office Building' as CustomField1,
            CASE TRIM(UPPER(school_rec.line3[1,3]))
                WHEN    'ARE'   THEN    'Tarble Center'
                WHEN	'CC'	THEN	'Clausen Center'
                WHEN    'DIN'   THEN    ''
                WHEN	'DSC'	THEN	'David Straz Center'
                WHEN	'HL'	THEN	'Hedberg Library'
                WHEN	'JAC'   THEN	'Johnson Art Center'
                WHEN	'JOH'	THEN	'Johnson Hall'
                WHEN	'LH'    THEN	'Lentz Hall'
                WHEN    'LEN'   THEN    'Lentz Hall'
                WHEN	'MAD'   THEN	'Madrigrano Hall'
                WHEN	'PEC'	THEN	'Physical Education Center'
                WHEN	'SC'	THEN	'Siebert Chapel'
                WHEN	'SIE'	THEN	'Siebert Chapel'
                WHEN    'STR'   THEN    'David Straz Center'
                WHEN	'SU'	THEN	'Student Union'
                WHEN	'TAR'	THEN	'Tarble Center'
                WHEN	'TWC'	THEN	'Todd Wehr Center'
                WHEN	''		THEN	''
                                ELSE	'Bad match: ' || TRIM(REPLACE(school_rec.line3,',','[comma]'))
            END as CustomValue1, 'Standing' as CustomField2,
            CASE jenzcst_rec.status_code
                WHEN	'FAC'	THEN	'Faculty'
                WHEN	'STF'	THEN	'Staff'
            END as CustomValue2, 'Full/Part Time' as CustomField3,
            CASE hrstat.hrstat
                WHEN	'FT'	THEN	'Full-Time'
                WHEN	'PT'	THEN	'Part-Time'
            END AS CustomValue3
            ,'END' as END
        FROM
            id_rec	INNER JOIN	job_rec				ON	id_rec.id		=	job_rec.id
                    INNER JOIN	pos_table			ON	job_rec.tpos_no	=	pos_table.tpos_no
                    LEFT JOIN	aa_rec	school_rec	ON	id_rec.id		=	school_rec.id
                                                    AND	school_rec.aa	=	"SCHL"
                    LEFT JOIN	aa_rec	email_rec	ON	id_rec.id		=	email_rec.id
                                                    AND	email_rec.aa	=	"EML1"
                    LEFT JOIN	aa_rec	ens_rec		ON	id_rec.id		=	ens_rec.id
                                                    AND	ens_rec.aa		=	'ENS'
                    LEFT JOIN
                    (
                        SELECT	host_id, MIN(seq_no) seq_no
                        FROM	jenzcst_rec
                        WHERE	status_code IN ('FAC','STF')
                        GROUP BY	host_id
                    )	filter						ON	id_rec.id		=	filter.host_id
                    LEFT JOIN	jenzcst_rec			ON	filter.host_id	=	jenzcst_rec.host_id
                                                    AND	filter.seq_no	=	jenzcst_rec.seq_no
                    LEFT JOIN
                    (
                        SELECT	id, hrstat
                        FROM	job_rec
                        WHERE	TODAY	BETWEEN	beg_date	AND	NVL(end_date, TODAY)
                        AND		hrstat	IN		('FT','PT')
                        GROUP BY id, hrstat
                    )	hrstat						ON	id_rec.id		=	hrstat.id
        WHERE
            TODAY	BETWEEN	job_rec.beg_date		AND	NVL(job_rec.end_date, TODAY)
            AND
            TODAY	BETWEEN	pos_table.active_date	AND	NVL(pos_table.inactive_date, TODAY)
            AND
            job_rec.title_rank	IS	NOT NULL
        ORDER BY lastname, firstname
    '''
    if test:
        print sql
    sqlresult = do_sql(sql, earl=EARL)
    for s in sqlresult:
        print (s.uuuid, s.last_name, s.first_name, s.email, s.dob, s.gender, s.confidentiality_indicator, s.major_1, s.major_2,
               s.minor_1, s.minor_2, s.gpa, s.home_address_line1, s.home_address_line2, s.home_address_line3, s.home_address_city,
               s.home_address_state, s.home_address_zip, s.home_address_country, s.phone_number, s.class_standing, s.emergency_contact_name,
               s.emergency_contact_phone, s.emergency_contact_relationship, s.country_of_citizenship, s.ethnicity, s.pell_grant_status,
               s.hr_title, s.hr_campus_phone, s.hr_flag, s.place_holder_1, s.place_holder_2, s.place_holder_3, s.place_holder_4, s.place_holder_5,
               s.place_holder_6, s.place_holder_7, s.place_holder_8, s.place_holder_9, s.place_holder_10, s.place_holder_11, s.place_holder_12,
               s.place_holder_13, s.place_holder_14, s.place_holder_15)
    
if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())