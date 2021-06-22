import ast
from django.utils.html import format_html, mark_safe
from django.urls import reverse
import json
from pygments import highlight
from pygments.lexers import JsonLexer, PythonLexer
from pygments.formatters import HtmlFormatter


def link_relation(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _link_relation(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj:
            model_name = linked_obj._meta.model_name
            app_label = linked_obj._meta.app_label
            view_name = f"admin:{app_label}_{model_name}_change"
            link_url = reverse(view_name, args=[linked_obj.id])
            return format_html('<a href="{}">{}</a>', link_url, linked_obj)
        else:
            return "-"

    _link_relation.short_description = field_name # Sets column name
    return _link_relation


def progress_bar(field_name):
    def _progress_bar(obj):
        percentage = getattr(obj, field_name)
        return format_html(
            '''
            <progress value="{0}" max="100"></progress>
            <span style="font-weight:bold">{0}%</span>
            ''',
            percentage
        )

    _progress_bar.short_description = field_name # Sets column name
    return _progress_bar


def pretty_json(field_name):
    def _pretty_json(obj):
        json_str = getattr(obj, field_name)
        response = json.dumps(json_str, sort_keys=True, indent=2)
        formatter = HtmlFormatter(style='colorful')
        response = highlight(response, JsonLexer(), formatter)
        # These styles can be added somewhere universally
        style = "<style>" + formatter.get_style_defs() + ".highlight{width: 500px; overflow: scroll; border: 1px solid gray;}</style>"
        return mark_safe(style + response)

    _pretty_json.short_description = field_name
    return _pretty_json


def pretty_python_exception(field_name):
    def _pretty_python_exception(obj):
        json_obj = getattr(obj, field_name)
        if not json_obj:
            return "-"
        message = json_obj["details"]
        if message[0:5] == "Error" and message[7:]:
            error = ast.literal_eval(message[7:])
            error = " ".join(error)
            formatter = HtmlFormatter(style='colorful')
            response = highlight(error, PythonLexer(), formatter)
            style = "<style>" + formatter.get_style_defs() + ".highlight{width: 500px; overflow: scroll; border: 1px solid gray;}</style>"
            return mark_safe(style + response)
        else:
            return message

    _pretty_python_exception.short_description = field_name
    return _pretty_python_exception
