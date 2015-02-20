from django.contrib import admin

from elo.models import UserProfile
from ladder.models import Match, Rank, Game, Challenge, Ladder

class RankInline( admin.TabularInline ) :
    model = Rank
    verbose_name_plural = "rankings"
    ordering = ('rank',)
    fields = ('rank','player','arrow')

class LadderAdmin( admin.ModelAdmin ) :
    inlines = [RankInline]
    list_display = ('__unicode__','created','end_date','players')

class MatchAdmin(admin.ModelAdmin):
    list_display = ('date_challenged', 'ladder', 'challenger_name', 'challengee_name', 'winner_name')
    list_filter = ['date_challenged']
    search_fields = ['challenger', 'challengee']

    def challenger_name(self, obj):
        up = UserProfile.objects.get(user=obj.challenger)
        return up.handle

    def challengee_name(self, obj):
        up = UserProfile.objects.get(user=obj.challengee)
        return up.handle

    def winner_name(self, obj):
        up = UserProfile.objects.get(user=obj.winner)
        return up.handle

class RankAdmin(admin.ModelAdmin):
    ordering = ('ladder', 'rank')
    #list_display = ('player_name', 'rank', 'arrow', 'game')
    #list_filter = ('game',)
    #def player_name(self, obj):
    #    up = UserProfile.objects.get(user=obj.player)
    #    return up.handle


class GameAdmin(admin.ModelAdmin):
    readonly_fields=('slug',)

admin.site.register(Match, MatchAdmin)
admin.site.register(Rank, RankAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Ladder, LadderAdmin)
admin.site.register(Challenge)
