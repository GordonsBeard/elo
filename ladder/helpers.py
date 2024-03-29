# coding=UTF-8
from django.db.models import Q
from ladder.models import Challenge, Rank
from math import ceil

def _open_challenges_exist(user, ladder):
    """Returns True if there are challenges open in the provided ladder for the user."""

    open_challenges = Challenge.objects.filter( (Q(challenger=user)|Q(challengee=user)) & (Q(accepted = Challenge.STATUS_ACCEPTED) | Q(accepted = Challenge.STATUS_NOT_ACCEPTED)) & Q(ladder = ladder) )

    if open_challenges.count() > 0:
        return True
    else:
        return False

def _get_valid_targets(user, user_rank, allTargets, ladder):
    """Takes a Rank QueryObject and returns a list of challengable ranks in the ladder.

        You are allowed to challenge if:
            - User is on the ladder. (checked beforehand)
            - User has no open challenges in this ladder.
            - User's (/w ▲) target is within current rank - UPARROW range.
            - User's (/w ▼) target is within current rank + DNARROW range.
            - User has not challenged target since TIMEOUT time has passed. *NOT IMPLEMENTED
    """
    # list of ranks player can challenge
    challengables = []

    # Get user's arrow and rank
    user_arrow = user_rank.arrow
    user_nrank = user_rank.rank

    # get the constraints for this ladder
    up_distance = ladder.up_arrow
    dn_distance = ladder.down_arrow

    # Get the range of ranks to search between
    if user_arrow == Rank.ARROW_UP :
        r_range = (user_nrank - up_distance, user_nrank - 1)
    elif user_arrow == Rank.ARROW_DOWN :
        r_range = (user_nrank + 1, user_nrank + dn_distance)
    else :
        raise ValueError( 'Rank.arrow can be either "0" (Up Arrow) or "1" (Down Arrow), but was "{}"'.format( user_arrow ) )

    # Get all ranks on the ladder within our target range
    for target_rank in Rank.objects.filter(ladder = ladder,rank__range = r_range) :
        challengables.append(target_rank.rank)

    return challengables