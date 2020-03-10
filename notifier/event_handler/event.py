import json
import importlib


class Event(object):

    EVENT_MODULE_NAME = 'notifier.events'

    def to_dict(self):
        classname = self.__class__.__name__
        vars = self.__dict__
        vars.update({'class': classname})
        return vars

    @staticmethod
    def from_dict(obj):
        module = importlib.import_module(Event.EVENT_MODULE_NAME)
        class_ = getattr(module, obj.pop('class'))
        instance = class_(**obj)
        return instance
