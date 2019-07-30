from django.contrib import admin
from .models import File, SampleMetadata, Storage, FileGroup, FileGroupMetadata, Sample

# Register your models here.

admin.site.register(File)
admin.site.register(SampleMetadata)
admin.site.register(Storage)
admin.site.register(Sample)
admin.site.register(FileGroup)
admin.site.register(FileGroupMetadata)
