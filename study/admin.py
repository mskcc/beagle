from django.contrib import admin
from study.models import Study


class StudyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "study_id",
        "requests",
        "samples"
    )
    ordering = ("-created_date",)


admin.site.register(Study, StudyAdmin)
