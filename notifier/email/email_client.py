import codecs
import logging
import smtplib
from string import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailClient(object):
    logger = logging.getLogger(__name__)

    def __init__(self, email_to, email_from, subject, content):
        self.to = email_to
        self.subject = subject
        self.content = content
        self.email_from = email_from
        self.domain = 'mskcc.org'
        self.SMTP_server = 'localhost'

    def send(self):
        server = None
        try:
            server = smtplib.SMTP(self.SMTP_server)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.subject
            msg['From'] = self.email_from
            msg['To'] = self.to

            html_content = MIMEText(self.content, 'html')
            msg.attach(html_content)

            server.sendmail(self.email_from, self.to, msg.as_string())
        except Exception as e:
            return False, str(e)
        else:
            self.logger.info('Email successfully sent to %s', self.to)
        finally:
            if server:
                server.quit()
