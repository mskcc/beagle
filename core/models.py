from django.db import models
import django_auth_ldap.backend
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User


class MskUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.CharField(max_length=500)


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
