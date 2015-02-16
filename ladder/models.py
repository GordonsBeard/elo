# -*- coding: utf-8 -*-
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from django.utils.timezone import utc

class Game(models.Model):
    name = models.CharField(max_length=50)
    abv = models.CharField(max_length=10)
    slug = models.CharField(max_length=50, blank=True, editable=False)
    icon = models.ImageField(upload_to='img/games', blank=True)

    def save(self):
        self.slug = slugify(self.name)
        super(Game, self).save()

    def get_absolute_url(self):
        return "/g/{0}".format(self.slug)

    def __unicode__(self):
        return self.name

class Ladder(models.Model):
    PRIVACY_LEVELS = (
        (u'0', u'Open'),
        (u'1', u'Unlisted'),
        (u'2', u'Private'),
    )

    WEEKDAYS = (
        (u'0', u'Sunday'),
        (u'1', u'Monday'),
        (u'2', u'Tuesday'),
        (u'3', u'Wednesday'),
        (u'4', u'Thursday'),
        (u'5', u'Friday'),
        (u'6', u'Saturday'),
    )

    def ranked_players(self):
        """Gets number of players on ladder."""
        return Rank.objects.filter(ladder=self).count()

    def save(self):
        self.slug = slugify(self.name)
        super(Ladder, self).save()

    def get_absolute_url(self):
        return "/l/{0}".format(self.slug)

    def latest_match(self):
        matches = Match.objects.filter(ladder=self).order_by('-date_challenged').first()
        return matches.date_challenged

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.game.name)

    name = models.CharField(max_length=50, blank=False, unique=True)
    slug = models.CharField(max_length=60, blank=True, editable=False)

    description = models.TextField(blank=True)

    owner = models.ForeignKey('auth.User', blank=False)
    game = models.ForeignKey(Game)
    players = property(ranked_players)
    latest_activity = property(latest_match)
    max_players = models.IntegerField(default='0')
    privacy = models.CharField(max_length=2, choices=PRIVACY_LEVELS, blank=False, default='0')
    signups = models.BooleanField(blank=False, default=True)
    created = models.DateTimeField('Ladder Created', blank=False, auto_now_add=True)
    end_date = models.DateTimeField('Ladder Closes', blank=True, null=True)
    up_arrow = models.IntegerField(default='2')
    down_arrow = models.IntegerField(default='4')
    weekly_reset = models.CharField(max_length=2, choices=WEEKDAYS, blank=True, null=True)
    challenge_cooldown = models.IntegerField(blank=True, null=True)
    response_timeout = models.IntegerField(blank=True, default='3')


class Rank(models.Model):
    ARROW_ICONS = (
        (u'0', u"▲"),
        (u'1', u"▼"),
    )

    class Meta:
        verbose_name_plural = "Rankings"
        verbose_name = "Rank"

    player = models.ForeignKey('auth.User')
    rank = models.IntegerField()
    arrow = models.CharField(max_length=2, choices=ARROW_ICONS, default='0')
    ladder = models.ForeignKey(Ladder)

    def __unicode__(self):
        return u"{0} [{1}{2}]".format(self.player.userprofile.handle, self.rank, self.get_arrow_display())

class Challenge(models.Model):
    CHALLENGE_RESPONSES = (
        (u'0',  u'Not Accepted'),
        (u'1',  u'Accepted'),
        (u'2',  u'Forfeit'),
        (u'3',  u'Postponed'),
        (u'4',  u'Completed'),
    )

    challenger = models.ForeignKey('auth.User', related_name='challenge_challenger')
    challengee = models.ForeignKey('auth.User', related_name='challenge_challengee')
    deadline = models.DateTimeField('Challenge Expires', null=True, blank=True)
    accepted = models.CharField(max_length=2, choices=CHALLENGE_RESPONSES, blank=False, default=0)
    ladder = models.ForeignKey(Ladder, blank=True)
    note = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "{0} vs {1}".format(self.challenger, self.challengee)

    def save(self, *args, **kwargs):
        ladder = Ladder.objects.get(pk=self.ladder.pk)
        if ladder.response_timeout > 0:
            self.deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=ladder.response_timeout)
        else:
            self.deadline = None

        # At this point we should have all the data we need to save the
        # Challenge object. Just a couple of players, a ladder and deadline.
        super(Challenge, self).save(*args, **kwargs)

        if self.accepted:
            """
            Once match is accepted, created the MATCH object and record the current stats.
            At this point we record the pre-match stats, so we need to get the players' current rank.
            If this rank does not exist, we leave as null, let the adjust_rank function figure out their ranks post-match.
            """
            try:
                challenger_rank_obj = Rank.objects.get(ladder=self.ladder, player=self.challenger)
                challenger_rank = challenger_rank_obj.rank
                challenger_arrow = challenger_rank_obj.arrow
            except ObjectDoesNotExist:
                challenger_rank = None
                challenger_arrow = None

            try:
                challengee_rank_obj = Rank.objects.get(ladder=self.ladder, player=self.challengee)
                challengee_rank = challengee_rank_obj.rank
                challengee_arrow = challengee_rank_obj.arrow
            except ObjectDoesNotExist:
                challengee_rank = None
                challengee_arrow = None

            defaults = { 'date_challenged': datetime.datetime.utcnow().replace(tzinfo=utc),
                        'challenger': self.challenger, 'challengee': self.challengee,
                        'challenger_rank': challenger_rank, 'challenger_rank_icon': challenger_arrow,
                        'challengee_rank': challengee_rank, 'challengee_rank_icon': challengee_arrow }
            new_match, created = Match.objects.get_or_create(related_challenge=self, ladder=self.ladder, defaults=defaults)

        super(Challenge, self).save(*args, **kwargs)

class Match(models.Model):
    ARROW_ICONS = (
        (u'0', u"▴"),
        (u'1', u"▾"),
    )

    class Meta:
        verbose_name_plural = "Matches"
        verbose_name = "Match"

    def save(self, *args, **kwargs):
        if self.winner:
            # With the winner mark the related challenge as "Completed"
            if self.related_challenge.accepted == '0':
                # As long as the match wasn't forfeit of course.
                self.related_challenge.accepted = '4' if not self.forfeit else '2'
                self.related_challenge.save(*args, **kwargs)

            # Because there is a winner, mark the Match object as complete
            # right now.
            self.date_complete = datetime.datetime.utcnow().replace(tzinfo=utc)

            # Record the winner's rank & icon on the Match object.

            current_ladder_ranks = Rank.objects.filter(ladder=self.ladder).count()

            challenger_rank, _created = Rank.objects.get_or_create(ladder=self.ladder, player=self.challenger, defaults={'rank':current_ladder_ranks+1, 'arrow':'0'})
            challengee_rank, _created = Rank.objects.get_or_create(ladder=self.ladder, player=self.challengee, defaults={'rank':current_ladder_ranks+2, 'arrow':'0'})


            # If the challenger is the winner, give them the challengee's rank
            # (if higher)
            self.winner_rank = challengee_rank.rank if challenger_rank.rank > challengee_rank.rank else challenger_rank.rank
            self.winner_rank_icon = 0

        super(Match, self).save(*args, **kwargs)

    date_challenged = models.DateTimeField('Date Challenged')
    date_complete = models.DateTimeField('Challenge Completed', blank=True, null=True)

    ladder = models.ForeignKey(Ladder)

    challenger = models.ForeignKey('auth.User',     related_name='match_challenger')
    challenger_rank = models.IntegerField(blank=True, null=True)
    challenger_rank_icon = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    character1 = models.CharField('Challenger\'s Character', max_length=40, blank=True)

    challengee = models.ForeignKey('auth.User',     related_name='match_challengee')
    challengee_rank = models.IntegerField(blank=True, null=True)
    challengee_rank_icon = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    character2 = models.CharField('Challengee\'s Character', max_length=40, blank=True)

    winner = models.ForeignKey('auth.User', blank=True, null=True)
    winner_rank = models.IntegerField(blank=True, null=True)
    winner_rank_icon = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    forfeit = models.BooleanField(blank=False, default=False)
    related_challenge = models.ForeignKey(Challenge)

    def __unicode__(self):
        return "{0} vs {1}".format(self.challenger, self.challengee)

def adjust_rank(instance, sender, **kwargs):
    """
    KNOWN BUGS:
    """
    if issubclass(sender, Match):
        if not instance.winner:
            # If there isn't a winner then why are we here?
            # What is our purpose in life if not to achieve where others have
            # failed?
            return

        winner = instance.challenger if instance.challenger == instance.winner else instance.challengee
        loser = instance.challenger if instance.challengee == instance.winner else instance.challengee

        ladder = instance.ladder

        # Get current number of people ranked on the ladder.
        rankings = Rank.objects.filter(ladder=ladder).count()

        if rankings>0:
            # The ladder is already initialized.

            # Now that we have a winner we need to give people actual ranks.
            # If they don't have one, give them the current rankings +1.
            # Challenger gets ranked higher by default because THEMS THE BREAKS
            defaults = {'rank':rankings+1, 'arrow':'0',}
            winner_rank, _created = Rank.objects.get_or_create(player=winner, ladder=ladder, defaults=defaults)
            loser_rank, _created = Rank.objects.get_or_create(player=loser, ladder=ladder, defaults=defaults)

            # Loser gets an up arrow if they are at the bottom of the list.
            loser_rank.arrow = '0' if winner_rank.rank >= rankings or loser_rank.rank >= rankings else '1'

            # Winner always gets an up arrow.
            winner_rank.arrow = '0'

            # If winner is lower down on the ladder than loser
            if winner_rank.rank > loser_rank.rank:
                old_winner_rank = winner_rank.rank
                old_loser_rank = loser_rank.rank

                # This swaps the ranks
                winner_rank.rank = old_loser_rank
                loser_rank.rank = old_winner_rank

            winner_rank.save()
            loser_rank.save()

#pre_save.connect(record_prematch_ranks, sender=Match)
post_save.connect(adjust_rank, sender=Match)
