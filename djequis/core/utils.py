import smtplib
import email.utils
from email.mime.text import MIMEText

def sendmail(to, frum, body, subject):

    # Create the message
    msg = MIMEText(body)
    msg['To'] = email.utils.formataddr(('Recipient', to))
    msg['From'] = email.utils.formataddr(('DJEquis', frum))
    msg['Subject'] = subject

    server = smtplib.SMTP('localhost')
    server.set_debuglevel(True) # show communication with the server
    try:
        server.sendmail(frum, to, msg.as_string())
    finally:
        server.quit()
