from django.contrib import admin
from study.models import Study


class StudyAdmin(admin.ModelAdmin):
    list_display = ("id", "study_id")


admin.site.register(Study, StudyAdmin)
