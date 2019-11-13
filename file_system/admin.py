from django.contrib import admin
from .models import Storage, File, FileType, FileMetadata, FileGroup, FileGroupMetadata, FileRunMap

# Register your models here.


class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_name', 'size')


class FileRunMapAdmin(admin.ModelAdmin):
    list_display = ('file', 'run')


admin.site.register(File, FileAdmin)
admin.site.register(Storage)
admin.site.register(FileGroup)
admin.site.register(FileType)
admin.site.register(FileMetadata)
admin.site.register(FileGroupMetadata)
admin.site.register(FileRunMap, FileRunMapAdmin)
