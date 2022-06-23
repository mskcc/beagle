import logging
from ..event_handler import EventHandler
from notifier.email.email_client import EmailClient


class EmailEventHandler(EventHandler):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()

    def process_send_email_event(self, event):
        self.logger.info("Email sent")
        client = EmailClient(event.email_to, event.email_from, event.subject, str(event))
        client.send()
