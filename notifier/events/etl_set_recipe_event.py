from django.conf import settings
from notifier.event_handler.event import Event


class ETLSetRecipeEvent(Event):

    def __init__(self, job_notifier, recipe):
        self.job_notifier = job_notifier
        self.recipe = recipe

    @classmethod
    def get_type(cls):
        return "ETLSetRecipeEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_set_recipe_event"

    def __str__(self):
        return self.recipe
