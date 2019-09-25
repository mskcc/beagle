from django.contrib import admin
from .models import RequestFetchJob, SamplesFetchJob, ETLError


admin.site.register(RequestFetchJob)
admin.site.register(SamplesFetchJob)
admin.site.register(ETLError)
