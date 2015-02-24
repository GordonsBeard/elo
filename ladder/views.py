from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, render_to_response
from django.template import RequestContext
from django import forms
from itertools import chain

from ladder.models import Rank, Match, Ladder, Challenge, Game
from ladder.helpers import _open_challenges_exist, _get_valid_targets, paged

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
            open_challenges_exist = _open_challenges_exist(request.user, ladder)
        except ObjectDoesNotExist:
            open_challenges_exist = False
            current_player_rank = None
            challengables = []
    else:
        open_challenges_exist = False
        current_player_rank = None
        join_link = False
        challengables = []

    match_list = Match.objects.filter(ladder = ladder).order_by('-date_complete')
    open_challenges = Challenge.objects.filter(challenger = request.user.id, ladder = ladder).filter(accepted = 0).order_by('-deadline')
    return {'can_challenge':open_challenges_exist, 'challengables': challengables, 'current_player_rank':current_player_rank, 'join_link':join_link, 'ladder':ladder, 'rank_list':rank_list, 'match_list':match_list, 'open_challenges':open_challenges}

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

def index(request, ladder_slug = None):
    """Display a list of all ladders, or just one ladder."""
    # Single ladder was requested via GET or directly via URL
    if request.GET != {} or ladder_slug:
        get_slug = ladder_slug if ladder_slug else request.GET['ladder_slug']
        ladder = Ladder.objects.get(slug = get_slug)
        single_ladder_info = single_ladder_details(request, ladder)

        return render_to_response('single_ladder_listing.html', single_ladder_info, context_instance=RequestContext(request))
    
    # Get a list of all ladders
    else:
        all_ladders = list_all_ladders(request)
        return render_to_response('ladder_home.html', all_ladders, context_instance=RequestContext(request))

@paged
def match_list( request, ladder_slug, page_info ) :
    # TODO: Implement this
    # Show a (paged) list of all matches on the ladder
    ladder          = Ladder.objects.get( slug = ladder_slug )
    matches         = Match.objects.filter( ladder = ladder ).order_by( '-date_complete' )[page_info.get_item_slice()]
    page_info.set_item_count( Match.objects.filter( ladder = ladder ).count() )

    return render_to_response('match_list.html', { 'ladder':ladder, 'pageinfo':page_info, 'matches':matches }, context_instance=RequestContext(request))

def match_detail( request, ladder_slug, match_id ) :
    # TODO: Implement this
    # Show details about the match defined by match_id
    pass;

def _user_already_ranked(user, ladder):
    """Returns true if user exists on ladder."""
    try:
        player_rank = Rank.objects.get( player = user, ladder = ladder )
    except ObjectDoesNotExist:
        return False
    return True

@login_required
def join_ladder(request, ladder_slug):
    """This view will confirm a user's attempt to join a ladder."""
    ladder = Ladder.objects.get(slug = ladder_slug)

    # Before going further, ensure the ladder is currently accepting signups.
    if ladder.signups == 0:
        messages.error(request, u"This ladder is currently not accepting signups. Please contact the owner for more information.")
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))

    # If GET and user is not ranked: allow the confirmation.
    if request.method == 'GET' and not _user_already_ranked(request.user, ladder):
        ladder = Ladder.objects.get(slug = ladder_slug)
        return render_to_response('confirm_join.html', {"ladder":ladder}, context_instance=RequestContext(request))

    # If GET but user is ranked: abort.
    elif request.method == 'GET' and _user_already_ranked(request.user, ladder):
        messages.error(request, u"Cannot join: you are already ranked on this ladder.")
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))

    # If POST but user is ranked: abort.
    elif request.method == 'POST' and _user_already_ranked(request.user, ladder):
        messages.error(request, u"Cannot join: you are already ranked on this ladder.")
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))
    
    # If POST and user is unranked: confirm the join.
    elif request.method == 'POST' and not _user_already_ranked(request.user, ladder):
        rank_list = Rank.objects.filter(ladder = ladder)
        
        new_rank = Rank(player = request.user, rank = rank_list.count() + 1, arrow = 0, ladder = ladder)
        new_rank.save()
        rank_list = Rank.objects.filter(ladder = ladder)
        messages.success(request, u"You've joined the ladder! You are now rank {0} of {1}.".format(new_rank.rank, rank_list.count()))
    
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))

@login_required
def leave_ladder(request, ladder_slug):
    """This view will confirm a user's attempt to leave a ladder."""
    ladder = Ladder.objects.get(slug = ladder_slug)

    # If GET: display confirmation of the leave
    if request.method == 'GET':
        challenges = Challenge.objects.filter( (Q(challengee = request.user) | Q(challenger = request.user)) & Q(accepted = Challenge.STATUS_NOT_ACCEPTED) ).count()
        return render_to_response('confirm_leave.html', {"ladder":ladder,"challenges":challenges}, context_instance=RequestContext(request))

    # If POST and user is unranked: abort
    elif request.method == 'POST' and not _user_already_ranked(request.user, ladder):
        messages.error(request, u"You are not ranked on this ladder.")
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))

    # If POST and user is ranked: confirm the delet
    elif request.method == 'POST' and _user_already_ranked(request.user, ladder):
        player_rank = Rank.objects.get(player = request.user, ladder = ladder)
        player_rank.delete()

        messages.success(request, u"You have been removed from the ladder: {0}".format(ladder.name))
        return HttpResponseRedirect('/l/{0}'.format(ladder.slug))

@login_required
def issue_challenge(request):
    # If POST: confirm/issue challenge
    if request.POST != {}:
        # unpack post
        challengee_id   = request.POST['challengee']
        ladder_slug     = request.POST['ladder']

        challenger      = request.user
        challengee      = User.objects.get(pk = challengee_id)
        ladder          = Ladder.objects.get(slug=ladder_slug)

        # Check for open challenges

        if _open_challenges_exist(request.user, ladder):
            messages.error(request, u"You have open challenges, you cannot challenge at this time.")
        else:
            # Generate a challenge
            challenge = Challenge( challenger=challenger, challengee=challengee, ladder=ladder )
            challenge.save()
            messages.success(request, u"You have issued a challenged to {0}, under the ladder {1}".format(challengee.userprofile.handle, ladder.name))

        return render_to_response('challenge.html', {'ladder':ladder, 'challengee':challengee }, context_instance=RequestContext(request))

    # Otherwise show a list of people you can challenge
    else:
        return redirect('/u/messages/challenges/')

@login_required
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