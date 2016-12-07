import io
import os
import re
import sys
import pysftp
import argparse

sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djequis.settings")

from django.conf import settings
from djzbar.utils.informix import do_sql

# set up command-line options
desc = """
    OCLC Synchronization
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "--test",
    action='store_true',
    help="Dry run?",
    dest="test"
)
'''
def paint_pdf(phile):

    buf = io.BytesIO()

    # Setup the document with paper size and margins
    doc = SimpleDocTemplate(
        buf,
        rightMargin=0.25*inch,
        leftMargin=0.075*inch,
        topMargin=.40*inch,
        bottomMargin=.40*inch,
        pagesize = portrait(letter)
    )

    # Styling
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CodeSmall', parent=styles['Code'], fontSize=7.5, leading=10
    ))

    lines = []
    # line break at Page n of n
    reg = re.compile("(Page) (\d+) (of) (\d+)")
    for line in phile.readlines():
        if reg.search(line):
            lines.append(PageBreak())
        lines.append(
            #Preformatted(line, styles['SmallFont'])
            Preformatted(line, styles['CodeSmall'])
        )
    doc.build(lines)

    # Write the PDF to a file
    with open('{}.pdf'.format(phile.name), 'w') as fd:
        fd.write(buf.getvalue())

    return
'''
def main():
    sql = '''
        SELECT
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st, ctry, zip, phone, email,
                MAX(
                    CASE grouping
                        WHEN    'Faculty'   THEN    3
                        WHEN    'Staff'     THEN    2
                        WHEN    'Student'   THEN    1
                                            ELSE    0
                    END
                    ) AS groupIndex
        FROM
            directory_vw
        GROUP BY
            lastname, firstname, middlename, id, addr_line1, addr_line2,
            city, st, ctry, zip, phone, email
        ORDER BY
            lastname, firstname, email
    '''
    print sql
    sqlresult = do_sql(sql)
    '''
    # go to our storage directory on this server
    os.chdir(settings.LOCAL_PATH)
    # obtain a list of file names from transcript spool
    philes = []
    with pysftp.Connection(**settings.LOCAL_CONNECTION) as sftp:
        sftp.cwd(settings.LOCAL_SPOOL)
        for attr in sftp.listdir_attr():
            phile = attr.filename
            if phile.startswith(settings.FILE_PREFIX, 0):
                try:
                    sftp.get(phile, preserve_mtime=True)
                    # generate PDFs
                    fo = open(phile, "r") # safer than w mode
                    paint_pdf(fo)
                    fo.close()
                    philes.append(phile)
                    # delete original since we have a copy
                    sftp.remove(phile)
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    #e = sys.exc_info()[0]

    # transfer the PDFs to scripsafe
    with pysftp.Connection(**settings.XTRNL_CONNECTION) as sftp:
        for f in philes:
            sftp.put("{}.pdf".format(f), preserve_mtime=True)

    # backup and cleanup
    with pysftp.Connection(**settings.LOCAL_CONNECTION) as sftp:
        for f in philes:
            sftp.cwd(settings.LOCAL_BACKUP)
            # copy transcripts to archive
            try:
                sftp.put(f, preserve_mtime=True)
            except:
                print "failed to transfer file to local backup: {}".format(f)

            # remove files fetched from local server and generated PDFs
            try:
                os.remove(f)
                os.remove("{}.pdf".format(f))
                print "removed files: {}, {}.pdf".format(f,f)
            except OSError:
                print """
                    failed to remove files from local file system: {}
                """.format(f)

    print "files sent to script safe:\n{}".format(philes)
    '''
    print "end"

if __name__ == "__main__":
    args = parser.parse_args()
    test = args.test

    sys.exit(main())
