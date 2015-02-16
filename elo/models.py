from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    # This will update their steam information every time they log in or something I guess yeah that sounds good.
    handle = models.CharField(max_length=50, blank=True)
    steamid = models.CharField(max_length=50, blank=True)
    url = models.CharField(max_length=255, blank=True)
    avatar = models.CharField(max_length=255, blank=True)
    avatarM = models.CharField(max_length=255, blank=True)
    avatarL = models.CharField(max_length=255, blank=True)
    primarygroup = models.CharField(max_length=50, blank=True)
    realname = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return self.handle

def create_user_profile(sender, instance, created, **kw):
    if created:
        UserProfile.objects.create(user=instance)
