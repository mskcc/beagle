import uuid
from django.db import models
import django_auth_ldap.backend
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from notifier.events import SendEmailEvent
from notifier.tasks import send_notification


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MskUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.CharField(max_length=500)


class UserRegistrationRequest(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    approved = models.BooleanField(default=None, null=True, blank=True)

    def save(self, *args, **kwargs):
        content = "User %s %s, with email %s@mskcc.org requested Voyager access." % (
        self.first_name, self.last_name, self.username,)
        for email in settings.BEAGLE_NOTIFIER_EMAIL_ABOUT_NEW_USERS.split(','):
            email = SendEmailEvent(job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP, email_to=email,
                                   email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM, subject='Registration access',
                                   content=content)
            send_notification.delay(email.to_dict())
        super(UserRegistrationRequest, self).save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        MskUser.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.mskuser.groups = 'mskcc'
    instance.mskuser.save()


def populate_user_profile(sender, user=None, ldap_user=None, **kwargs):
    user.email = ldap_user._user_dn
    user.save()


django_auth_ldap.backend.populate_user.connect(populate_user_profile)
