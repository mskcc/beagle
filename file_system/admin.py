from django.contrib import admin
from .models import Storage, File, FileType, FileMetadata, FileGroup, FileGroupMetadata, FileRunMap

# Register your models here.


class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_name', 'file_group', 'size')
    search_fields = ['file_name']


class FileRunMapAdmin(admin.ModelAdmin):
    list_display = ('file', 'run')


class FileMetadataAdmin(admin.ModelAdmin):
    list_display = ('file', 'version', 'metadata')
    autocomplete_fields = ['file']
    search_fields = ('id', 'metadata__requestId')

admin.site.register(File, FileAdmin)
admin.site.register(Storage)
admin.site.register(FileGroup)
admin.site.register(FileType)
admin.site.register(FileMetadata, FileMetadataAdmin)
admin.site.register(FileGroupMetadata)
admin.site.register(FileRunMap, FileRunMapAdmin)
