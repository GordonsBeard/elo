from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django import forms
from itertools import chain

from ladder.models import Rank, Match, Ladder, Challenge, Game

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
    open_challenges = Challenge.objects.filter(Q(challengee = user) | Q(challenger = user)).filter(ladder = ladder).count()
    if  open_challenges > 0: 
        print "Open challenges"
        return []

    # Get user's arrow and rank
    user_arrow = user_rank.arrow
    user_nrank = user_rank.rank

    # get the constraints for this ladder
    up_distance = ladder.up_arrow
    dn_distance = ladder.down_arrow

    # Get the range of ranks to search between
    if user_arrow == '0' :
        r_range = (user_nrank-up_distance, user_nrank-1)
    elif user_arrow == '1' :
        r_range = (user_nrank+1, user_nrank+dn_distance)
    else :
        raise ValueError( 'Rank.arrow can be either "0" (Up Arrow) or "1" (Down Arrow), but was "{}"'.format( user_arrow ) )

    # Get all ranks on the ladder within our target range
    for target_rank in Rank.objects.filter(ladder = ladder,rank__range = r_range) :
        challengables.append(target_rank.rank)

    return challengables

def single_ladder_details(request, ladder):
    """Retrieve info on a single ladder."""
    
    # get the raw ranking list
    rank_list = Rank.objects.filter(ladder = ladder).order_by('rank')
    

    # if user is logged in
    if request.user.is_authenticated():
        # set a flag to allow them to join the ladder
        join_link = True if request.user.pk not in [key.player.pk for key in rank_list] else None
        # if there is a ranking, get a list of those you can challenge.
        
        try:
            current_player_rank = Rank.objects.get(player = request.user, ladder = ladder)
            challengables = _get_valid_targets(request.user, current_player_rank, rank_list, ladder)
            messages.debug(request, "Challengable ranks: {0}".format(challengables))
            print "Challengable ranks: {0}".format(challengables)
        except ObjectDoesNotExist:
            current_player_rank = None
            challengables = []
    else:
        current_player_rank = None
        join_link = False
        challengables = []

    match_list = Match.objects.filter(ladder = ladder).order_by('-date_complete')
    open_challenges = Challenge.objects.filter(challenger = request.user.id).filter(accepted = 0).order_by('-deadline')
    return {'challengables': challengables, 'current_player_rank':current_player_rank, 'join_link':join_link, 'ladder':ladder, 'rank_list':rank_list, 'match_list':match_list, 'open_challenges':open_challenges}

def list_all_ladders(request):
    """Retrieve info on all the ladders."""

    # List of all ladders includes match and rank info as well.
    match_list = Match.objects.all().order_by('-date_complete')
    rank_list = Rank.objects.all()
    ladder_list = Ladder.objects.all()

    if request.user.is_authenticated():
        # Check for open challenges
        try:
            challenger_list = Challenge.objects.filter(match__challenger = request.user, accepted=False)
        except Exception, e:
            challenger_list = []
        try:
            challengee_list = Challenge.objects.filter(match__challengee = request.user, accepted=False)
        except Exception, e:
            challengee_list = []

        # Check for logged-in users' open challenges
        your_challenges = list(chain(challenger_list, challengee_list))
    else:
        your_challenges = []

    return {'match_list':match_list, 'rank_list':rank_list, 'ladder_list':ladder_list, 'your_challenges':your_challenges}

def index(request, ladderslug = None):
    """Display a list of all ladders, or just one ladder."""
    # Single ladder was requested via GET or directly via URL
    if request.GET != {} or ladderslug:
        get_slug = ladderslug if ladderslug else request.GET['ladderslug']
        ladder = Ladder.objects.get(slug = get_slug)
        single_ladder_info = single_ladder_details(request, ladder)

        return render_to_response('single_ladder_listing.html', single_ladder_info, context_instance=RequestContext(request))

    # Mysterie ????
    elif request.method == 'POST':
        raise NotImplementedError("How are you POSTing? Why? Stop it please.")
    
    # Get a list of all ladders
    else:
        all_ladders = list_all_ladders(request)
        return render_to_response('ladder_home.html', all_ladders, context_instance=RequestContext(request))


def join_ladder(request, ladderslug):
    # TODO: Confirm joining ladder
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
    # TODO: Confirm leaving ladder
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

def issue_challenge(request):
    # TODO: if POST: confirm/issue challenge
    # TODO: otherwi: show a list of people you can challenge

    # unpack post
    challengee_id = request.POST['challengee']
    ladder_slug = request.POST['ladder']
    challengee = User.objects.get(pk = challengee_id)
    

    ladder = Ladder.objects.get(slug=ladder_slug)

    messages.success(request, u"You have issued a challenged to {0}, under the ladder {1}".format(challengee.userprofile.handle, ladder.name))
    return render_to_response('challenge.html', {'ladder':ladder, 'challengee':challengee }, context_instance=RequestContext(request))

def create_ladder(request):
    class CreateLadderForm(forms.ModelForm):
        class Meta:
            model = Ladder
            fields = ['name', 'game', 'owner']
            widgets = {'owner': forms.HiddenInput()}

    if request.method == 'POST':
        form = CreateLadderForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['name']
            game = form.cleaned_data['game']
            owner = form.cleaned_data['owner']

            newLadder = Ladder.objects.create(name = name, game = game, owner = owner)
            messages.success(request, "Ladder created: {0}".format(newLadder.name))
            return HttpResponseRedirect('/')
    else:
        form = CreateLadderForm(initial={'owner': request.user.pk})
    return render_to_response("create_ladder.html", {'form': form}, context_instance=RequestContext(request))