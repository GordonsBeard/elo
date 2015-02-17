from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from ladder.models import Rank, Match, Ladder, Challenge


def index(request, ladderslug, message = None):
    ladder_requested = Ladder.objects.get(slug = ladderslug)
    rank_list = Rank.objects.filter(ladder = ladder_requested).order_by('rank')

    if request.user.is_authenticated():
        """ This is the magic that will happen when a user is logged in. """
        join_link = True if request.user.pk not in [key.player.pk for key in rank_list] else None
        try:
            current_player_rank = Rank.objects.get(player = request.user, ladder = ladder_requested)
        except ObjectDoesNotExist:
            current_player_rank = None
    else:
        """ Otherwise. """
        current_player_rank = None
        join_link = False

    match_list = Match.objects.filter(ladder = ladder_requested).order_by('-date_complete')
    open_challenges = Challenge.objects.filter(challenger = request.user.id).filter(accepted = 0).order_by('-deadline')
    return render_to_response('single_ladder_listing.html', {'current_player_rank':current_player_rank, 'join_link':join_link, 'ladder':ladder_requested, 'rank_list':rank_list, 'match_list':match_list, 'open_challenges':open_challenges}, context_instance=RequestContext(request))

def join_ladder(request, ladderslug):
    ladder_requested = Ladder.objects.get(slug = ladderslug)

    if not request.user.is_authenticated():
        messages.error(request, u"Log in before trying to join a ladder!")

        return index(request, ladderslug, message)

    rank_list = Rank.objects.filter(ladder = ladder_requested)

    try:
        player_rank = Rank.objects.get(player = request.user, ladder=ladder_requested)
        messages.error(request, u"You are already on this ladder! You are rank {0} of {1}.".format(player_rank.rank, rank_list.count()))

    except ObjectDoesNotExist:
        new_rank = Rank(player = request.user, rank = rank_list.count() + 1, arrow = 0, ladder = ladder_requested)
        new_rank.save()
        rank_list = Rank.objects.filter(ladder = ladder_requested)
        messages.success(request, u"You've joined the ladder! You are now rank {0} of {1}.".format(new_rank.rank, rank_list.count()))
    
    return HttpResponseRedirect('/l/{0}'.format(ladder_requested.slug))


def leave_ladder(request, ladderslug, **kwargs):
    ladder_requested = Ladder.objects.get(slug = ladderslug)

    if not request.user.is_authenticated():
        messages.error(request, u"Log in before trying to join a ladder!")

        return index(request, ladderslug)

    rank_list = Rank.objects.filter(ladder = ladder_requested)

    try:
        player_rank = Rank.objects.get(player = request.user, ladder = ladder_requested)
        player_rank.delete()

        messages.success(request, u"You have left this ladder. Everyone gets a free promotion!")
    except ObjectDoesNotExist:
        messages.error(request, u"You're not even on this ladder dumdum.")
  
    return HttpResponseRedirect('/l/{0}'.format(ladder_requested.slug))

def challenge_list(request, ladderslug, challengee):
    if not request.user.is_authenticated():
        messages.error(request, u"Log in before trying to issue a challenge!")
        return index(request, ladderslug)
    ladder_requested = Ladder.objects.get(slug = ladderslug)
    challengee_name = User.objects.get(id = challengee)
    messages.success(request,u"Challenge issued to {0}".format(challengee_name.userprofile.handle))
  
    return HttpResponseRedirect('/l/{0}'.format(ladder_requested.slug))

def issue_challenge(request):
    challengee_id = request.POST['challengee']

    challengee = User.objects.get(pk=challengee_id)
    ladder_slug = request.POST['ladder']

    ladder = Ladder.objects.get(slug=ladder_slug)

    messages.success(request, u"You have issued a challenged to {0}, under the ladder {1}".format(challengee.userprofile.handle, ladder.name))
    return render_to_response('challenge.html', {'ladder':ladder, 'challengee':challengee }, context_instance=RequestContext(request))
