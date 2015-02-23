# coding=UTF-8
from django.db.models import Q
from ladder.models import Challenge, Rank

def _open_challenges_exist(user, ladder):
    """Returns True if there are challenges open in the provided ladder for the user."""

    open_challenges = Challenge.objects.filter( (Q(challenger=user)|Q(challengee=user)) & (Q(accepted = Challenge.STATUS_ACCEPTED) | Q(accepted = Challenge.STATUS_NOT_ACCEPTED)) & Q(ladder = ladder) )

    if open_challenges.count() > 0:
        return True
    else:
        return False

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

    # user has no open challenges in this ladder
    open_challenges = _get_user_challenges(user, ladder, (Challenge.STATUS_NOT_ACCEPTED, Challenge.STATUS_ACCEPTED)).count()

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

# TODO: test this
# It should wrap a view function with automatic paging support
def paged( fn, default_length ) :
    def _paged_viewfn( request, *args, **kwargs ) :
        page = request.GET['p'] if request.method == "GET" and request.GET.has_key( 'p' ) else 1
        page_length = request.GET['l'] if request.method == "GET" and request.GET.has_key( 'l' ) else default_length
        return fn( request, page = page, page_length = page_length, *args, **kwargs )
    return _paged_viewfn