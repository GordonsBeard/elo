# -*- coding: utf-8 -*-
import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.template.defaultfilters import slugify
from django.utils.timezone import utc
from ladder.exceptions import ParticipantBusy, PlayerNotRanked, ChallengeeOutOfRange, ChallengeeIsChallenger

def _can_challenge_user( challenger, challengee, ladder ) :
    """ This function validates a challenge before it is saved """
    # Make sure the challengee is actually unique
    if challenger == challengee :
        raise ChallengeeIsChallenger( "you cannot challenge yourself" )

    # Attempt to get the ranks of the participants
    try :
        challenger_rank = Rank.objects.get( ladder = ladder, player = challenger )
        challengee_rank = Rank.objects.get( ladder = ladder, player = challengee )
    except ObjectDoesNotExist :
        # Rank couldn't be retrieved, but both players must be ranked
        raise PlayerNotRanked( "either the challenger {} or challengee {} is not ranked on the ladder {}".format( challenger, challengee, ladder ), ladder )

    # Make sure the participants aren't already busy with another challenge
    active_ladder_challenges = Challenge.objects.filter( ladder = ladder ).filter( Q(accepted = Challenge.STATUS_ACCEPTED) | Q(accepted = Challenge.STATUS_NOT_ACCEPTED) )
    active_ladder_challenges = active_ladder_challenges.exclude( challenger = challenger, challengee = challengee ) # Exclude ourselves
    if      active_ladder_challenges.filter( Q( challenger = challenger ) | Q( challengee = challenger ) ) :
        raise ParticipantBusy( "cannot issue a new challenge with open challenges already", challenger )
    elif    active_ladder_challenges.filter( Q( challenger = challengee ) | Q( challengee = challengee ) ) :
        raise ParticipantBusy( "cannot issue a challenge to a player already busy with another challenge", challengee )

    # Find the difference between ranks
    rankdiff = challenger_rank.rank - challengee_rank.rank

    # Make sure the ranks are different
    if rankdiff == 0 :
        raise ChallengeeOutOfRange( "challengee and challenger are equally ranked at {}".format( challenger_rank.rank ), rankdiff )

    # Check that the target of the challenge is within the ladder's specified range
    if challenger_rank.arrow == Rank.ARROW_UP :
        if rankdiff < 0 or rankdiff > int( ladder.up_arrow ) :
            raise ChallengeeOutOfRange( "challengee is ranked {}, which can't be challenged from {}".format( challengee_rank.rank, challenger_rank.rank ), rankdiff )
    elif challenger_rank.arrow == Rank.ARROW_DOWN :
        if rankdiff > 0 or -rankdiff > int( ladder.down_arrow ) :
            raise ChallengeeOutOfRange( "challengee is ranked {}, which can't be challenged from {}".format( challengee_rank.rank, challenger_rank.rank ), rankdiff )
    else :
        # Somehow the challenger has an invalid arrow
        raise ValueError( "challenger arrow {} is invalid".format( challenger_rank.arrow ) )

    return True

def _get_user_challenges(user, ladder = None, statuses = None):
    """Get all the challenges from a specified user (challenger or challengee). When no ladder statuses passed along, returns all challenges.
        user    = User object
        ladder  = Ladder object (optional)
        statuses = Tuple of challenge statuses (see ladder views)
    """

    # Grab the challenges from a user without filters
    open_challenges = Challenge.objects.filter((Q(challengee = user) | Q(challenger = user)))

    # Narrow it down to a single ladder if provided.
    if ladder is not None:
        open_challenges = open_challenges.filter( ladder = ladder )

    # Narrow it down to statuses requested
    if statuses is not None:
        for status in statuses:
            open_challenges = open_challenges.filter( accepted = status )

    return open_challenges

class Game(models.Model):
    name    = models.CharField(max_length=50)
    abv     = models.CharField(max_length=10)
    slug    = models.CharField(max_length=50, blank=True, editable=False)
    icon    = models.ImageField(upload_to='img/games', blank=True)

    def save(self, force_insert=False, force_update=False, using=None):
        self.slug = slugify(self.name)
        super(Game, self).save()

    def get_absolute_url(self):
        return "/g/{0}".format(self.slug)

    def __unicode__(self):
        return self.name

class Ladder(models.Model):
    PRIVACY_OPEN     = u'0'
    PRIVACY_UNLISTED = u'1'
    PRIVACY_PRIVATE  = u'2'

    PRIVACY_LEVELS = (
        (PRIVACY_OPEN,      u'Open'),
        (PRIVACY_UNLISTED,  u'Unlisted'),
        (PRIVACY_PRIVATE,   u'Private'),
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
        return Rank.objects.filter( ladder = self ).count()

    def save(self, force_insert=False, force_update=False, using=None):
        self.slug = slugify(self.name)
        super(Ladder, self).save()

    def get_absolute_url(self):
        return "/l/{0}".format(self.slug)

    def latest_match(self):
        matches = Match.objects.filter(ladder_id=self.id).order_by('-date_challenged').first()
        if not matches :
            return "Never"
        return matches.date_challenged

    def is_user_ranked( self, user ) :
        return user.rank_set.get( ladder = self ) != None

    def __unicode__(self):
        return "{0} ({1})".format(self.name, self.game.name)

    name                = models.CharField(max_length=50, blank=False, unique=True)
    slug                = models.CharField(max_length=60, blank=True, editable=False)

    description         = models.TextField(blank=True)

    owner               = models.ForeignKey('auth.User', blank=False)
    game                = models.ForeignKey(Game)
    players             = property(ranked_players)
    latest_activity     = property(latest_match)
    max_players         = models.IntegerField(default='0')
    privacy             = models.CharField(max_length=2, choices=PRIVACY_LEVELS, blank=False, default=PRIVACY_OPEN)
    signups             = models.BooleanField(blank=False, default=True)
    created             = models.DateTimeField('Ladder Created', blank=False, auto_now_add=True)
    end_date            = models.DateTimeField('Ladder Closes', blank=True, null=True)
    up_arrow            = models.IntegerField("up arrow range", default='2')
    down_arrow          = models.IntegerField("down arrow range", default='4')
    weekly_reset        = models.CharField(max_length=2, choices=WEEKDAYS, blank=True, null=True)
    challenge_cooldown  = models.IntegerField(blank=True, null=True)
    response_timeout    = models.IntegerField(blank=True, default='3')


class Rank(models.Model):
    ARROW_UP    = u'0'
    ARROW_DOWN  = u'1'

    ARROW_ICONS = (
        (ARROW_UP,   u"▲"),
        (ARROW_DOWN, u"▼"),
    )

    class Meta:
        verbose_name_plural = "Rankings"
        verbose_name        = "Rank"

    player  = models.ForeignKey('auth.User')
    rank    = models.IntegerField()
    arrow   = models.CharField(max_length=2, choices=ARROW_ICONS, default='0')
    ladder  = models.ForeignKey(Ladder)

    def __unicode__(self):
        return u"{0} [{1}{2}]".format(self.player.userprofile.handle, self.rank, self.get_arrow_display())

class Challenge(models.Model):
    STATUS_NOT_ACCEPTED = u'0'
    STATUS_ACCEPTED     = u'1'
    STATUS_FORFEIT      = u'2'
    STATUS_POSTPONED    = u'3'
    STATUS_COMPLETED    = u'4'
    STATUS_CANCELLED    = u'5'

    CHALLENGE_RESPONSES = (
        (STATUS_NOT_ACCEPTED,  u'Not Accepted'),
        (STATUS_ACCEPTED,      u'Accepted'),
        (STATUS_FORFEIT,       u'Forfeit'),
        (STATUS_POSTPONED,     u'Postponed'),
        (STATUS_COMPLETED,     u'Completed'),
        (STATUS_CANCELLED,     u'Cancelled')
    )

    challenger  = models.ForeignKey('auth.User', related_name='challenge_challenger')
    challengee  = models.ForeignKey('auth.User', related_name='challenge_challengee')
    deadline    = models.DateTimeField('Challenge Expires', null=True, blank=True)
    accepted    = models.CharField(max_length=2, choices=CHALLENGE_RESPONSES, blank=False, default=0)
    ladder      = models.ForeignKey(Ladder, blank=True)
    note        = models.TextField(blank=True, null=True)

    #match       = models.OneToOneField(Match)

    def __unicode__(self):
        return "{0} vs {1}".format(self.challenger, self.challengee)

    def accept(self):
        self.accepted = Challenge.STATUS_ACCEPTED

    def forfeit(self):
        self.accepted = Challenge.STATUS_FORFEIT

    def postpone(self):
        self.accepted = Challenge.STATUS_POSTPONED

    def complete(self):
        self.accepted = Challenge.STATUS_COMPLETED

    def cancel(self):
        self.accepted = Challenge.STATUS_CANCELLED

    def save(self, *args, **kwargs):
        # Check that our challenge is actually valid
        _can_challenge_user( self.challenger, self.challengee, self.ladder )

        if not self.deadline :
            ladder = self.ladder
            if ladder.response_timeout > 0 :
                self.deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=int(ladder.response_timeout))
            else:
                self.deadline = None

        # At this point we should have all the data we need to save the
        # Challenge object. Just a couple of players, a ladder and deadline.
        super(Challenge, self).save(*args, **kwargs)

        if self.accepted == Challenge.STATUS_ACCEPTED:
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

class Match(models.Model):
    ARROW_UP    = u'0'
    ARROW_DOWN  = u'1'

    ARROW_ICONS = (
        (ARROW_UP,   u"▴"),
        (ARROW_DOWN, u"▾"),
    )

    class Meta:
        verbose_name_plural = "Matches"
        verbose_name = "Match"

    def choose_winner( self, winner ) :
        if isinstance( winner, int ) :
            if winner == 0 :
                self.winner = self.challenger
            elif winner == 1 :
                self.winner = self.challengee
            else :
                raise ValueError( "choose_winner accepts either a user, 0, or 1" )
        elif isinstance( winner, User ) :
            if winner != self.challenger and winner != self.challengee :
                raise ValueError( "the winner of a match must be either the challenger or the challengee" )
            self.winner = winner
        else :
            raise TypeError( "choose_winner accepts integers or users, not {}".format( type(winner) ) )

    def save(self, *args, **kwargs):
        if self.winner:
            # With the winner mark the related challenge as "Completed"
            if self.related_challenge.accepted == Challenge.STATUS_ACCEPTED:
                # As long as the match wasn't forfeit of course.
                if self.forfeit :
                    self.related_challenge.forfeit()
                else :
                    self.related_challenge.complete()
                self.related_challenge.save(*args, **kwargs)

            # Because there is a winner, mark the Match object as complete
            # right now.
            self.date_complete = datetime.datetime.utcnow().replace(tzinfo=utc)

            # Record the winner's rank & icon on the Match object.
            # If the challenger is the winner, give them the challengee's rank
            # (if higher)
            self.winner_rank = self.challengee_rank if self.challenger_rank > self.challengee_rank else self.challenger_rank
            self.winner_rank_icon = u'0'

        super(Match, self).save(*args, **kwargs)

    def get_loser( self ):
        if self.winner:
            return self.challenger if self.challengee_id == self.winner_id else self.challengee
        else:
            return None

    def get_loser_id( self ):
        if self.winner:
            return self.challenger_id if self.challengee_id == self.winner_id else self.challengee_id
        else:
            return None

    date_challenged         = models.DateTimeField('Date Challenged')
    date_complete           = models.DateTimeField('Challenge Completed', blank=True, null=True)

    ladder                  = models.ForeignKey(Ladder)

    challenger              = models.ForeignKey('auth.User',     related_name='match_challenger')
    challenger_rank         = models.IntegerField(blank=True, null=True)
    challenger_rank_icon    = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    character1              = models.CharField('Challenger\'s Character', max_length=40, blank=True)

    challengee              = models.ForeignKey('auth.User',     related_name='match_challengee')
    challengee_rank         = models.IntegerField(blank=True, null=True)
    challengee_rank_icon    = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    character2              = models.CharField('Challengee\'s Character', max_length=40, blank=True)

    winner                  = models.ForeignKey('auth.User', blank=True, null=True)
    winner_rank             = models.IntegerField(blank=True, null=True)
    winner_rank_icon        = models.CharField(max_length=2, choices=ARROW_ICONS, null=True, blank=True)

    loser                   = property( get_loser )
    loser_id                = property( get_loser_id )

    forfeit                 = models.BooleanField(blank=False, default=False)
    related_challenge       = models.OneToOneField(Challenge)

    def __unicode__(self):
        return "{0} vs {1}".format(self.challenger, self.challengee)

def del_user_rank_adjustment(instance, sender, **kwargs):
    """This updates all existing ranks on the ladder, and cancels all outstanding challenges."""
    
    if issubclass(sender, Rank):
        # get a list of the remaining players with a larger (worse) rank
        remainingPlayers = Rank.objects.filter(ladder = instance.ladder)

        # if there are no players remaining players, we're done
        if remainingPlayers == 0:
            return

        lowerRankedPlayers = remainingPlayers.filter(rank__gt = instance.rank)
        if lowerRankedPlayers > 0:
            for player in lowerRankedPlayers:
                player.rank -= 1
                player.save()

        lastPlace = remainingPlayers.order_by('rank').last()
        if lastPlace.arrow == Rank.ARROW_DOWN :
            lastPlace.arrow = Rank.ARROW_UP
            lastPlace.save()

        # get a list of all non-completed challenges
        open_challenges = _get_user_challenges( instance.player, ladder = instance.ladder, statuses = (Challenge.STATUS_NOT_ACCEPTED, Challenge.STATUS_ACCEPTED) )
        for challenge in open_challenges:
            challenge.delete()

def adjust_rank(instance, sender, **kwargs):
    if issubclass(sender, Match):
        if not instance.winner:
            # If there isn't a winner then why are we here?
            # What is our purpose in life if not to achieve where others have
            # failed?
            return

        # Having two if statements like this is faster than having a single if/else for some reason
        winner  = instance.challenger if instance.challenger == instance.winner else instance.challengee
        loser   = instance.challenger if instance.challengee == instance.winner else instance.challengee

        ladder  = instance.ladder

        # Get current number of people ranked on the ladder.
        rankings = ladder.ranked_players()

        # if rankings>0:
        #     # The ladder is already initialized.

        #     # Now that we have a winner we need to give people actual ranks.
        #     # If they don't have one, give them the current rankings +1.
        #     # Challenger gets ranked higher by default because THEMS THE BREAKS
        #     defaults = {'rank':rankings+1, 'arrow':Rank.ARROW_DOWN,}
        #     winner_rank, _created = Rank.objects.get_or_create(player=winner, ladder=ladder, defaults=defaults)
        #     loser_rank, _created = Rank.objects.get_or_create(player=loser, ladder=ladder, defaults=defaults)

        # We should never allow unranked players to get this far
        winner_rank = Rank.objects.only('rank').get( player = winner, ladder = ladder )
        loser_rank  = Rank.objects.only('rank').get( player = loser,  ladder = ladder )

        # If the winner is lower down on the ladder than the loser
        if winner_rank.rank > loser_rank.rank :
            old_winner_rank = winner_rank.rank
            old_loser_rank  = loser_rank.rank

            # This swaps the ranks
            winner_rank.rank = old_loser_rank
            loser_rank.rank  = old_winner_rank

        # Loser gets an up arrow if they are at the bottom of the list.
        loser_rank.arrow = Rank.ARROW_DOWN if loser_rank.rank < rankings else Rank.ARROW_UP

        # Winner always gets an up arrow.
        winner_rank.arrow = Rank.ARROW_UP

        winner_rank.save()
        loser_rank.save()

# After updating a Match, if there is a winner, adjust relevant Ranks
post_save.connect(adjust_rank, sender = Match)

# After deleting a User's Rank, update all other Ranks up one.
post_delete.connect(del_user_rank_adjustment, sender = Rank)