from django.contrib import admin
from .models import Storage, File, FileType, FileMetadata, FileGroup, FileGroupMetadata

# Register your models here.

admin.site.register(File)
admin.site.register(Storage)
admin.site.register(FileGroup)
admin.site.register(FileType)
admin.site.register(FileMetadata)
admin.site.register(FileGroupMetadata)
