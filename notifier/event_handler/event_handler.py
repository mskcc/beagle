import logging
import sys, inspect
from notifier.event_handler.event import Event


class EventHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.events = dict()
        for name, obj in inspect.getmembers(sys.modules['notifier.events']):
            if inspect.isclass(obj):
                self.events[obj.get_type()] = obj.get_method()

    def process(self, event):
        self.logger.debug("Event received")
        e = Event.from_dict(event)
        try:
            self.logger.info("[%s]: %s", e.get_type(), str(e))
            return getattr(self, self.events[e.get_type()])(e)
        except Exception as ex:
            self.logger.info("Failed to process event: %s with error %s", str(e), str(ex))
        self.logger.debug("Event processed")
