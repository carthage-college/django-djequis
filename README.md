# django-djequis

An all purpose Django project for lightweight applications that interact
with the Jenzabar databases, and over time will replace maquettes in /jics.

## Cron Jobs

    # scrip safe
    45 * * * * (python /d2/django_projects/djequis/bin/scrip_safe.py 2>&1 | mail -s "[scrip safe] SFTP process" larry@carthage.edu) >> /dev/null 2>&1
    # Terra Dotta: daily before 2h CDT, push out a copy of the Terra Dotta export
    30 01 * * * (python /d2/django_projects/djequis/bin/terradotta.py 2>&1 | mail -s "[TerraDotta] SFTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    #30 01 * * * python /d2/django_projects/djequis/bin/terradotta.py >> /dev/null 2>&1
    # Everbridge: weekly, monday morning at midnight
    00 00 * * 1 (python /d2/django_projects/djequis/bin/everbridge.py --database=cars 2>&1 | mail -s "[Everbridge] SFTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    # OCLC: weekly, monday morning at 2h, push out a fresh copy of the OCLC xml
    00 02 * * 1 (python /d2/django_projects/djequis/bin/oclc.py 2>&1 | mail -s "[OCLC] FTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    # maxient
    00 03 * * * (python /d2/django_projects/djequis/bin/maxient.py 2>&1 | mail -s "[Maxient] SFTP carthage user data" larry@carthage.edu) >> /dev/null 2>&1
    # Request Tracker
    */10 * * * * python /d2/django_projects/djequis/rt/users.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/users.py 2>&1 | mail -s "[RT] Users" larry@carthage.edu) >> /dev/null 2>&1
    */10 * * * * python /d2/django_projects/djequis/rt/tickets.py >> /dev/null 2>&1
    #*/10 * * * * (python /d2/django_projects/djequis/rt/tickets.py 2>&1 | mail -s "[RT] Tickets" larry@carthage.edu) >> /dev/null 2>&1
    # JX scripts
    11 11 * * * (python /d2/django_projects/djequis/bin/class_year.py --action=update --database=jxlive) >> /dev/null 2>&1
    #11 11 * * * (python /d2/django_projects/djequis/bin/class_year.py --action=update --database=jxlive 2>&1 | mail -s "[DJ Equis] Class Year" larry@carthage.edu) >> /dev/null 2>&1
    # common app
    00 04 * * 0-5 (python /d2/django_projects/djequis/bin/commonapp.py --database=cars 2>&1 | mail -s "[CommonApp] Fetching data via SFTP" larry@carthage.edu) >> /dev/null 2>&1
    # barnes and noble
    18 08-18 * * 1-6 (python /d2/django_projects/djequis/bin/barnesandnoble.py) >> /dev/null 2>&1
    # Papercut: monthly, 2nd day of every month at 23:55h, create .csv file for Papercut charge backs
    55 23 2 * * (python /d2/django_projects/djequis/bin/papercut.py 2>&1 | mail -s "[PaperCut] Papercut charge backs data" larry@carthage.edu) >> /dev/null 2>&1
    # Papercut GL: monthly, 3rd day of every month at 2:45h, create .csv file of Papercut GL accounts
    #45 02 3 * * (python /d2/django_projects/djequis/bin/papercut_glrec.py 2>&1 | mail -s "[PaperCut] Papercut GL accounts data" larry@carthage.edu) >> /dev/null 2>&1
    # Loan Dispursements (every four hours or once a day at 4:20h)
    05 00 * * * (python /d2/django_projects/djequis/bin/loan_disbursement.py --database=cars 2>&1 | mail -s "[Financial Aid] Loan Disbursement Notification" larry@carthage.edu) >> /dev/null 2>&1
    # provisioning
    00 08 * * * python /d2/django_projects/djvision/bin/provisioning.py --database=cars --filetype=csv >> /dev/null 2>&1
    00 12 * * * python /d2/django_projects/djvision/bin/provisioning.py --database=cars --filetype=csv >> /dev/null 2>&1
    00 16 * * * python /d2/django_projects/djvision/bin/provisioning.py --database=cars --filetype=csv >> /dev/null 2>&1
    # package concierge
    00 02 * * SUN (python /d2/django_projects/djequis/bin/concierge.py --database=cars 2>&1 | mail -s "[Package Concierge] SFTP carthage data" larry@carthage.edu) >> /dev/null 2>&1
    # Schoology: daily, create .csv files for import into Schoology LMS
    01 10,22 * * * (python /d2/django_projects/djequis/bin/schoology.py --database=cars 2>&1 | mail -s "[Schoology] Fetching data for SFTP" larry@carthage.edu) >> /dev/null 2>&1
    #01 */11 * * * (python /d2/django_projects/djequis/bin/schoology.py --database=cars 2>&1 | mail -s "[Schoology] Fetching data for SFTP" larry@carthage.edu) >> /dev/null 2>&1

## Database import

    mysql -u username -p rt4 < rt4.sql
    mysql -u username -p rt4 < rt/views.sql

## URLs

### TerraDotta
    https://studyabroad.carthage.edu/index.cfm?FuseAction=SIS.Admin

### Smarty Streets for Address Verification
    https://smartystreets.com/docs/sdk/python
