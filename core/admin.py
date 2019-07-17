from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import MskUser


class MskccUserInline(admin.StackedInline):
    model = MskUser
    can_delete = False
    verbose_name_plural = 'mskcc_user'


class UserAdmin(BaseUserAdmin):
    inlines = (MskccUserInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
