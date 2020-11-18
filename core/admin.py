from django.contrib import admin
from django.conf import settings
from notifier.events import SendEmailEvent
from django.contrib.auth.models import User
from notifier.tasks import send_notification
from core.models import UserRegistrationRequest
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import MskUser


class MskccUserInline(admin.StackedInline):
    model = MskUser
    can_delete = False
    verbose_name_plural = 'mskcc_user'


class UserAdmin(BaseUserAdmin):
    inlines = (MskccUserInline,)


def approve(modeladmin, request, queryset):
    for req in queryset:
        email = '%s@mskcc.org' % req.username
        User.objects.create(username=req.username, email=email, first_name=req.first_name,
                            last_name=req.last_name)
        req.approved = True
        req.save()
        content = "Your request to access Voyager is approved"
        email = SendEmailEvent(job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP, email_to=email,
                               email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM, subject='Registration approved',
                               content=content)
        send_notification.delay(email.to_dict())


approve.short_description = "Approve request"


class UserRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'approved',)
    search_fields = ('username',)
    actions = (approve,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserRegistrationRequest, UserRegistrationRequestAdmin)
