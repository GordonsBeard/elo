from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from ladder.models import Rank, Match, Ladder, Challenge


def index(request, ladder, message=None):
    ladder_requested = Ladder.objects.get(slug=ladder)
    rank_list = Rank.objects.filter(ladder=ladder_requested).order_by('rank')
    if request.user.is_authenticated():
        """ This is the magic that will happen when a user is logged in. """
        join_link = True if request.user.pk not in [key.player.pk for key in rank_list] else None
        try:
            current_player_rank = Rank.objects.get(player = request.user, ladder=ladder_requested)
        except ObjectDoesNotExist:
            current_player_rank = None
    else:
        """ Otherwise. """
        current_player_rank = None
        join_link = False
    match_list = Match.objects.filter(ladder=ladder_requested).order_by('-date_complete')
    open_challenges = Challenge.objects.filter(challenger=request.user.id).filter(accepted=0).order_by('-deadline')
    return render_to_response('single_ladder_listing.html', {'current_player_rank':current_player_rank, 'join_link':join_link, 'ladder':ladder_requested, 'rank_list':rank_list, 'match_list':match_list, 'open_challenges':open_challenges, 'message':message}, context_instance=RequestContext(request))

def join_ladder(request, ladder):
    ladder_requested = Ladder.objects.get(slug=ladder)

    if not request.user.is_authenticated():
        message = u"Log in before trying to join a ladder!"

        return index(request, ladder, message)

    rank_list = Rank.objects.filter(ladder=ladder_requested)

    try:
        player_rank = Rank.objects.get(player=request.user, ladder=ladder_requested)
        message = u"You are already on this ladder! You are rank {0} of {1}.".format(player_rank.rank, rank_list.count())
    except ObjectDoesNotExist:
        new_rank = Rank(player=request.user, rank=rank_list.count() + 1, arrow=0, ladder=ladder_requested)
        new_rank.save()
        rank_list = Rank.objects.filter(ladder=ladder_requested)
        message = u"You've joined the ladder! You are now rank {0} of {1}.".format(new_rank.rank, rank_list.count())

    return index(request, ladder, message)

def challenge_list(request, ladder, challengee):
    if not request.user.is_authenticated():
        message = u"Log in before trying to issue a challenge!"

        return index(request, ladder, message)

    challengee_name = User.objects.get(id=challengee)
    message = u"Challenge issued to {0}".format(challengee_name.userprofile.handle)

    return render(request, 'single_ladder_listing.html', {'ladder': ladder, 'message': message})
