from celery import shared_task
from django.conf import settings
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.events import ETLImportEvent


def event_handler():
    if settings.NOTIFIER == "JIRA":
        return JiraEventHandler()


def event_prepare(func):
    @shared_task
    def decorator(event):
        print("Prepare event")
        event_json = event.to_dict()
        print(event_json)
        return func(event_json)
    return decorator


@shared_task
def send_notification(event):
    event_handler().process(event)


@event_prepare
@shared_task
def test_decorator(event):
    print(event)


if __name__=='__main__':
    e = ETLImportEvent('test', [], [])
    test_decorator(e)