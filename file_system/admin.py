from django.contrib import admin
from .models import File, FileMetadata, Storage, FileGroup, FileGroupMetadata, Sample

# Register your models here.

admin.site.register(File)
admin.site.register(FileMetadata)
admin.site.register(Storage)
admin.site.register(Sample)
admin.site.register(FileGroup)
admin.site.register(FileGroupMetadata)
