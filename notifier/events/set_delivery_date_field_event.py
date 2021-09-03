from datetime import datetime
from notifier.event_handler.event import Event


class SetDeliveryDateFieldEvent(Event):

    def __init__(self, job_notifier, delivery_date):
        self.job_notifier = job_notifier
        self.delivery_date = delivery_date

    @classmethod
    def get_type(cls):
        return "SetDeliveryDateFieldEvent"

    @classmethod
    def get_method(cls):
        return "process_set_delivery_date_event"

    def __str__(self):
        time = datetime.strptime(self.delivery_date, '%Y-%m-%d %H:%M:%S.%f%z')
        return time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + time.strftime('%z')
