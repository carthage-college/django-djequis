import smtplib
import email.utils
from email.mime.text import MIMEText

def sendmail(to, frum, body, subject, debug=False):

    # Create the message
    msg = MIMEText(body)
    msg['To'] = email.utils.formataddr(('Recipient', to))
    msg['From'] = email.utils.formataddr(('DJ Equis', frum))
    msg['Subject'] = subject

    server = smtplib.SMTP('localhost')
    # show communication with the server
    if debug:
        server.set_debuglevel(True)
    try:
        server.sendmail(frum, to, msg.as_string())
    finally:
        server.quit()
