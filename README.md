# django-djequis

An all purpose Django project for lightweight applications that interact
with the Jenzabar databases, and over time will replace maquettes in /jics.

## Cron Jobs

    # scrip safe
    #20 04 * * * (python /d2/django_projects/djzbar/bin/scrip_safe.py 2>&1 | mail -s "[scrip safe] SFTP process" larry@carthage.edu) >> /dev/null 2>&1
    # Terra Dotta: daily before 2h CDT, push out a copy of the Terra Dotta export
    30 01 * * * python /d2/django_projects/djequis/bin/terradotta.py >> /dev/null 2>&1
    # Everbridge: weekly, monday morning at midnight
    00 00 * * 1 (python /d2/django_projects/djequis/bin/everbridge.py 2>&1 | mail -s "[Everbridge] SFTP process" mkishline@carthage.edu) >> /dev/null 2>&1
    # OCLC: weekly, monday morning at 2h, push out a fresh copy of the OCLC xml
    00 02 * * 1 (python /d2/django_projects/djequis/bin/oclc.py 2>&1 | mail -s "[OCLC] FTP process" larry@carthage.edu) >> /dev/null 2>&1

