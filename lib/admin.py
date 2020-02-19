from django.utils.html import format_html
from django.urls import reverse

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
