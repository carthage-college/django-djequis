import io
import os
import re
import sys
import pysftp
import csv
import time
import argparse
import shutil

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

def main():
    sql = '''
        SELECT
            DIR.id AS UUUID, TRIM(DIR.lastname) AS Last_Name, TRIM(DIR.firstname) AS First_Name,
            TRIM(DIR.middlename) AS Middle_Name, TRIM(DIR.email) AS Email, TO_CHAR(PRO.birth_date,
            '%m-%d-%Y') AS DOB, PRO.sex AS Gender, '' AS Confidentiality_Indicator,
            TRIM(NVL(MAJ1.txt,'')) AS Major_1, TRIM(NVL(MAJ2.txt,'')) AS Major_2,
            TRIM(NVL(MIN1.txt,'')) AS Minor_1, TRIM(NVL(MIN2.txt,'')) AS Minor_2,
            SSR.cum_gpa::char(5) AS GPA, TRIM(DIR.addr_line1) AS Home_Address_Line1,
            TRIM(DIR.addr_line2) AS Home_Address_Line2, TRIM(IR.addr_line3) AS Home_Address_Line3,
            TRIM(DIR.city) AS Home_Address_City, TRIM(DIR.st) AS Home_Address_State,
            TRIM(DIR.zip) AS Home_Address_Zip, TRIM(INITCAP(NVL(CT.txt,'')))
            AS Home_Address_Country, DIR.phone AS Phone_Number, PER.cl AS Class_Standing,
            TRIM(CASE
                WHEN    ICE1.aa_no    IS    NOT NULL    AND LEN(ICE1.line1)    >    0    THEN    ICE1.line1
                WHEN    ICE2.aa_no    IS    NOT NULL    AND    LEN(ICE2.line1)    >    0    THEN    ICE2.line1
            END) AS Emergency_Contact_Name,
            CASE
                WHEN    ICE1.aa_no    IS    NOT NULL    AND    LEN(ICE1.phone)    >    0    THEN    ICE1.phone
                WHEN    ICE1.aa_no    IS    NOT NULL    AND LEN(ICE1.line2)    >    0    THEN    ICE1.line2
                WHEN    ICE2.aa_no    IS    NOT NULL    AND    LEN(ICE2.phone)    >    0    THEN    ICE2.phone
                WHEN    ICE2.aa_no    IS    NOT NULL    AND    LEN(ICE2.line2)    >    0    THEN    ICE2.line2
                                                                                ELSE    ''
            END AS Emergency_Contact_Phone,
            TRIM(CASE
                WHEN    ICE1.aa_no    IS    NOT NULL                                THEN    RT1.txt
                WHEN    ICE2.aa_no    IS    NOT NULL                                THEN    RT2.txt
                                                                                ELSE    'N/A'
            END) AS Emergency_Contact_Relationship,
            TRIM(INITCAP(NVL(CITZ.txt,''))) AS Country_of_Citizenship, TRIM(NVL(ETH.txt,'')) AS Ethnicity,
            NVL(NAF.pell_elig,'') AS Pell_Grant_Status, '' AS HR_Title, '' AS HR_Campus_Phone, 'N' AS HR_Flag,
            --Missing contact name
            TRIM(CASE
                WHEN    MIS1.aa_no    IS    NOT NULL    AND LEN(MIS1.line1)    >    0    THEN    MIS1.line1
                WHEN    MIS2.aa_no    IS    NOT NULL    AND    LEN(MIS2.line1)    >    0    THEN    MIS2.line1
            END) AS Place_Holder_1,
            --Missing contact phone
            CASE
                WHEN    MIS1.aa_no    IS    NOT NULL    AND    LEN(MIS1.phone)    >    0    THEN    MIS1.phone
                WHEN    MIS1.aa_no    IS    NOT NULL    AND LEN(MIS1.line2)    >    0    THEN    MIS1.line2
                WHEN    MIS2.aa_no    IS    NOT NULL    AND    LEN(MIS2.phone)    >    0    THEN    MIS2.phone
                WHEN    MIS2.aa_no    IS    NOT NULL    AND    LEN(MIS2.line2)    >    0    THEN    MIS2.line2
                                                                                ELSE    ''
            END AS Place_Holder_2,
            --Missing contact relationship
            TRIM(CASE
                WHEN    MIS1.aa_no    IS    NOT NULL                                THEN    RT1.txt
                WHEN    MIS2.aa_no    IS    NOT NULL                                THEN    RT2.txt
                                                                                ELSE    'N/A'
            END) AS Place_Holder_3,
            '' AS Place_Holder_4, '' AS Place_Holder_5, '' AS Place_Holder_6, '' AS Place_Holder_7, '' AS Place_Holder_8,
            '' AS Place_Holder_9, '' AS Place_Holder_10, '' AS Place_Holder_11, '' AS Place_Holder_12, '' AS Place_Holder_13,
            '' AS Place_Holder_14, '' AS Place_Holder_15
        FROM
            directory_vw    DIR    INNER JOIN    profile_rec        PRO        ON    DIR.id                =    PRO.id
                                INNER JOIN    prog_enr_rec    PER        ON    DIR.id                =    PER.id
                                                                    AND    PER.prog            =    'UNDG'
                                LEFT JOIN    major_table        MAJ1    ON    PER.major1            =    MAJ1.major
                                LEFT JOIN    major_table        MAJ2    ON    PER.major2            =    MAJ2.major
                                LEFT JOIN    minor_table        MIN1    ON    PER.minor1            =    MIN1.minor
                                LEFT JOIN    minor_table        MIN2    ON    PER.minor2            =    MIN2.minor
                                LEFT JOIN    stu_stat_rec    SSR        ON    DIR.id                =    SSR.id
                                                                    AND    SSR.prog            =    'UNDG'
                                INNER JOIN    id_rec            IR        ON    DIR.id                =    IR.id
                                LEFT JOIN    ctry_table        CT        ON    DIR.ctry            =    CT.ctry
                                                                    AND    TODAY            BETWEEN    CT.active_date    AND    NVL(CT.inactive_date, TODAY)
                                LEFT JOIN    (
                                    SELECT
                                        ICEsub.id, MAX(ICEsub.aa_no) AS aa_no
                                    FROM
                                        aa_rec    ICEsub
                                    WHERE
                                        ICEsub.aa    =    'ICE'
                                    AND
                                        TODAY BETWEEN ICEsub.beg_date AND NVL(ICEsub.end_date, TODAY)
                                    GROUP BY
                                        ICEsub.id
                                )                            ICE1alt    ON    DIR.id                =    ICE1alt.id
                                LEFT JOIN    aa_rec            ICE1    ON    ICE1alt.aa_no        =    ICE1.aa_no
                                LEFT JOIN    (
                                    SELECT
                                        ICEsub.id, MAX(ICEsub.aa_no) AS aa_no
                                    FROM
                                        aa_rec    ICEsub
                                    WHERE
                                        ICEsub.aa    =    'ICE2'
                                    AND
                                        TODAY BETWEEN ICEsub.beg_date AND NVL(ICEsub.end_date, TODAY)
                                    GROUP BY
                                        ICEsub.id
                                )                            ICE2alt    ON    DIR.id                =    ICE2alt.id
                                LEFT JOIN    aa_rec            ICE2    ON    ICE2alt.aa_no        =    ICE2.aa_no
                                LEFT JOIN    (
                                    SELECT
                                        MISsub.id, MAX(MISsub.aa_no) AS aa_no
                                    FROM
                                        aa_rec    MISsub
                                    WHERE
                                        MISsub.aa    =    'MIS1'
                                    AND
                                        TODAY BETWEEN MISsub.beg_date AND NVL(MISsub.end_date,TODAY)
                                    GROUP BY
                                        MISsub.id
                                )                            MIS1alt    ON    DIR.id                =    MIS1alt.id
                                LEFT JOIN    aa_rec            MIS1    ON    MIS1alt.aa_no        =    MIS1.aa_no
                                LEFT JOIN    (
                                    SELECT
                                        MISsub.id, MAX(MISsub.aa_no) AS aa_no
                                    FROM
                                        aa_rec    MISsub
                                    WHERE
                                        MISsub.aa    =    'MIS2'
                                    AND
                                        TODAY BETWEEN MISsub.beg_date AND NVL(MISsub.end_date,TODAY)
                                    GROUP BY
                                        MISsub.id
                                )                            MIS2alt    ON    DIR.id                =    MIS2alt.id
                                LEFT JOIN    aa_rec            MIS2    ON    MIS2alt.aa_no        =    MIS2.aa_no
                                LEFT JOIN    rel_table        RT1        ON    ICE1.cell_carrier    =    RT1.rel
                                LEFT JOIN    rel_table        RT2        ON    ICE2.cell_carrier    =    RT2.rel
                                LEFT JOIN    race_table        ETH        ON    PRO.race            =    ETH.race
                                LEFT JOIN    (
                                    SELECT
                                        id, MAX(eff_date) AS eff_date
                                    FROM
                                        naf_vw
                                    GROUP BY
                                        id
                                )                            NAFalt    ON    DIR.id                =    NAFalt.id
                                LEFT JOIN    naf_vw            NAF        ON    NAFalt.id            =    NAF.id
                                                                    AND    NAFalt.eff_date        =    NAF.eff_date
                                LEFT JOIN    ctry_table        CITZ    ON    PRO.citz            =    CITZ.ctry
        WHERE
            DIR.grouping    =    'Student'
        UNION
        SELECT
            DIR.id AS UUUID, TRIM(DIR.lastname) AS Last_Name, TRIM(DIR.firstname) AS First_Name,
            TRIM(DIR.middlename) AS Middle_Name, TRIM(DIR.email) AS Email, '' AS DOB,
            '' AS Gender, '' AS Confidentiality_Indicator, '' AS Major_1, '' AS Major_2,
            '' AS Minor_1, '' AS Minor_2, '' AS GPA, '' AS Home_Address_Line1, '' AS Home_Address_Line2,
            '' AS Home_Address_Line3, '' AS Home_Address_City, '' AS Home_Address_State,
            '' AS Home_Address_Zip, '' AS Home_Address_Country, '' AS Phone_Number, '' AS Class_Standing,
            '' AS Emergency_Contact_Name, '' AS Emergency_Contact_Phone, '' AS Emergency_Contact_Relationship,
            '' AS Country_of_Citizenship, '' AS Ethnicity, '' AS Pell_Grant_Status,
            TRIM(NVL(JOB.job_title,'')) AS HR_Title, NVL(SCH.phone,'') AS HR_Campus_Phone, 'Y' AS HR_Flag,
            '' AS Place_Holder_1, '' AS Place_Holder_2, '' AS Place_Holder_3, '' AS Place_Holder_4, '' AS Place_Holder_5,
            '' AS Place_Holder_6, '' AS Place_Holder_7, '' AS Place_Holder_8, '' AS Place_Holder_9, '' AS Place_Holder_10,
            '' AS Place_Holder_11, '' AS Place_Holder_12, '' AS Place_Holder_13, '' AS Place_Holder_14, '' AS Place_Holder_15
        FROM
            directory_vw    DIR    LEFT JOIN    aa_rec    SCH        ON    DIR.id        =    SCH.id
                                                            AND    SCH.aa        =    'SCHL'
                                INNER JOIN    (
                                    SELECT
                                        J.id, MIN(NVL(J.title_rank,'9')) AS title_rank
                                    FROM
                                        job_rec    J
                                    WHERE
                                        TODAY BETWEEN J.beg_date AND NVL(J.end_date, TODAY)
                                    AND
                                        J.title_rank > '0'
                                    GROUP BY
                                        J.id
                                )                   JOBalt    ON    DIR.id            =    JOBalt.id
                                INNER JOIN    job_rec    JOB        ON    JOB.id            =    JOBalt.id
                                                            AND    JOB.title_rank    =    JOBalt.title_rank
                                                            AND TODAY        BETWEEN    JOB.beg_date AND NVL(JOB.end_date, TODAY)
        WHERE
            DIR.grouping    IN    ('Faculty','Staff')
        ORDER BY
            Last_Name, First_Name, Middle_Name
    '''
    sqlresult = do_sql(sql, earl=EARL)

    datetimestr = time.strftime("%Y%m%d-%H%M%S")
    filename=('{}terradotta_{}.csv'.format(settings.TERRADOTTA_CSV_OUTPUT,datetimestr))
    new_filename=('{}sis_hr_user_info.txt'.format(settings.TERRADOTTA_CSV_OUTPUT))

    phile=open(filename,"w");
    output=csv.writer(phile, dialect='excel-tab')

    sqlresult = do_sql(sql, earl=EARL)
    output.writerow(["UUUID", "Last Name", "First Name", "Middle Name", "Email",
                     "DOB", "Gender", "Confidentiality Indicator", "Major 1",
                     "Major 2", "Minor 1", "Minor 2", "GPA", "Home Address 1",
                     "Home Address 2", "Home Address 3", "Home Address City",
                     "Home Address State", "Home Address Zip",
                     "Home Address Country", "Phone Number", "Class Standing",
                     "Emergency Contact Name", "Emergency Contact Phone",
                     "Emergency Contact Relationship", "Country of Citizenship",
                     "Ethnicity", "Pell Grant Status", "HR Title", "HR Campus Phone",
                     "HR Flag", "Place Holder 1", "Place Holder 2",
                     "Place Holder 3", "Place Holder 4", "Place Holder 5",
                     "Place Holder 6", "Place Holder 7", "Place Holder 8",
                     "Place Holder 9", "Place Holder 10", "Place Holder 11",
                     "Place Holder 12", "Place Holder 13", "Place Holder 14",
                     "Place Holder 15"])
    for row in sqlresult:
        output.writerow(row)
    phile.close()

    # go to our storage directory on this server
    os.chdir(settings.TERRADOTTA_CSV_OUTPUT)
    shutil.copy(filename, new_filename)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    XTRNL_CONNECTION = {
        'host':settings.TERRADOTTA_HOST,
        'username':settings.TERRADOTTA_USER,
        'private_key':settings.TERRADOTTA_PKEY,
        'private_key_pass':settings.TERRADOTTA_PASS,
        'cnopts':cnopts
    }
    # transfer the CSV to scripsafe
    with pysftp.Connection(**XTRNL_CONNECTION) as sftp:
        sftp.put("sis_hr_user_info.txt", preserve_mtime=True)

    print "Done"

if __name__ == "__main__":
    args = parser.parse_args()

    sys.exit(main())
