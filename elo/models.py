from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

class UserProfile(models.Model):
    user = models.OneToOneField(User, blank=False, null=False, on_delete=models.CASCADE)

    # This will update their steam information every time they log in or something I guess yeah that sounds good.
    handle = models.CharField(max_length=50, blank=True)
    steamid = models.CharField(max_length=50, blank=True)
    url = models.CharField(max_length=255, blank=True)
    avatar = models.CharField(max_length=255, blank=True)
    avatarM = models.CharField(max_length=255, blank=True)
    avatarL = models.CharField(max_length=255, blank=True)
    primarygroup = models.CharField(max_length=50, blank=True)
    realname = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.handle

def create_user_profile(sender, instance, created, **kw):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)