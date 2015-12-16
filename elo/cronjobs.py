from django.db.models import Q
from django.utils import timezone

from django_cron import CronJobBase, Schedule

from ladder.models import Challenge

class ChallengeTimeouts(CronJobBase):
    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'elo.challenge_timeouts'

    def do(self):
        # Grab all the Not Accepted challenges that have a deadline less than now.
        # Also exclude Challenges with null/None timeouts set.
        all_challenges = Challenge.objects.filter( Q( accepted = Challenge.STATUS_NOT_ACCEPTED ) & Q(deadline__lte = timezone.now())).exclude(deadline=None)
        
        # Mark them all as Forfeits.
        for challenge in all_challenges:
            challenge.forfeit()
            challenge.save()