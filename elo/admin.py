from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from elo.models import UserProfile

class SteamProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "profiles"
    fields = ("handle", "steamid", "url", "avatar", "avatarM", "avatarL", "primarygroup", "realname", )

class UserAdmin(BaseUserAdmin):
    inlines = (SteamProfileInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)