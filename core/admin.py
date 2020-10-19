from django.contrib import admin
from core.models import UserRegistrationRequest
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import MskUser


class MskccUserInline(admin.StackedInline):
    model = MskUser
    can_delete = False
    verbose_name_plural = 'mskcc_user'


class UserAdmin(BaseUserAdmin):
    inlines = (MskccUserInline,)


def approve(modeladmin, request, queryset):
    for req in queryset:
        User.objects.create(username=req.username, email='%s@mskcc.org' % req.username, first_name=req.first_name,
                            last_name=req.last_name)
        req.approved = True
        req.save()


approve.short_description = "Approve request"


class UserRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'approved',)
    search_fields = ('username',)
    actions = (approve,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserRegistrationRequest, UserRegistrationRequestAdmin)
