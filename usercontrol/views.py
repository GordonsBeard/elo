from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
from ladder.models import Rank, Challenge, Match, _get_user_challenges
from ladder.helpers import paged
from ladder.exceptions import PlayerNotInvolved
from datetime import datetime

PROFILE_RECENT_MATCHES    = 5         # How many matches to show under the "Recent Matches" header
PROFILE_ACTIVE_LADDERS    = 5         # How many ladders to show under the "Active Ladders" header

def profile( request, username ) :
    # Get our user object or bail
    user              = get_object_or_404( User, username = username )

    # Get user info
    stats             = { 
        "Ladders Joined":         Rank.objects.filter( player_id = user.pk ).count(), 
        "Challenges Issued":      Challenge.objects.filter( challenger_id = user.pk ).count(), 
        "Challenges Received":    Challenge.objects.filter( challengee_id = user.pk ).count(), 
        "Matches Won":            Match.objects.filter( winner_id = user.pk ).count(), 
        "Matches Lost":           Match.objects.filter( Q(winner_id__isnull = False) & ( Q(challengee = user) | Q(challenger = user) ) & ~Q(winner_id = user.pk) ).count(),
    }
    matches           = Match.objects.filter( winner_id__isnull = False ).filter( Q(challengee = user) | Q(challenger = user) ).order_by( '-date_complete' )[:PROFILE_RECENT_MATCHES]
    ladders           = user.rank_set.order_by( '-ladder__created' )
    ranks             = [(r,r.ladder.latest_match()) for r in ladders[:PROFILE_ACTIVE_LADDERS]]

    # Get common ladders
    if request.user.is_authenticated() and not user == request.user :
        # TODO : find these more efficiently
        # common_ladders is the intersection of user's ladders and request.user's ladders
        # invite_ladders is the difference of request.user's ladders (that they can invite to) and user's ladders
        common_ladders    = [r.ladder for r in ladders if r.ladder.rank_set.filter( player = request.user ).count()]
        invite_ladders    = [r.ladder for r in request.user.rank_set.order_by( 'ladder__name' ) if not r.ladder.rank_set.filter( player = user ).count()]
    else :
        common_ladders    = []
        invite_ladders    = []

    return render( request, "profile.html", { 'userp':user, 'stats':stats, 'matches':matches, 'ranks':ranks, 'common':common_ladders, 'invite':invite_ladders } )
@paged
def match_list( request, username, page_info ) :
    user            = get_object_or_404( User, username = username )
    all_matches     = Match.objects.filter( Q( challenger = user ) | Q( challengee = user ) )
    matches         = all_matches.order_by( '-date_complete' )[page_info.get_item_slice()]
    page_info.set_item_count( all_matches.count() )

    return render_to_response('user_match_list.html', { 'userp':user, 'pageinfo':page_info, 'matches':matches }, context_instance=RequestContext(request))

@login_required
def message_list( request ) :
    num_challenges    = _get_user_challenges( request.user ).filter( accepted = 0 ).count()
    num_matches       = Match.objects.filter( Q(winner__isnull = True) & ( Q(challengee = request.user) | Q(challenger = request.user) ) ).count()
    return render( request, "messages.html", { 'num_challenges':num_challenges, 'num_matches':num_matches } )

@login_required
def message_challenges( request ) :
    if request.method == "POST" :
        try :
            action    = request.POST['action']
            notice_id = request.POST['note_id']

            challenge = Challenge.objects.get( pk = notice_id )

            if challenge.challengee == request.user :
                if action == "accept_challenge" :
                    challenge.accept()
                    challenge.save()
                    messages.success( request, "You accepted the challenge against {}".format( challenge.challenger.userprofile.handle ) )
                elif action == "decline_challenge" :
                    challenge.forfeit()
                    challenge.save()
                    messages.success( request, "You forfeited the challenge against {}".format( challenge.challenger.userprofile.handle ) )
                else :
                    messages.error( request, "Invalid command" )
            elif challenge.challenger == request.user :
                # TO-DO add cancel challenge action
                pass
            else :
                raise PlayerNotInvolved()
        except AttributeError :
            messages.error( request, "Tried to use an invalid command. Tell a programmer." )
        except KeyError :
            messages.error( request, "Not enough information to complete request." )
        except PlayerNotInvolved :
            messages.error( request, "Challenge not found" )

    challenges = _get_user_challenges( request.user )

    # status = 1
    # Accepted
    open_challenges = challenges.filter( challengee = request.user ).filter( accepted = 0 )

    # status = 0
    # Not Accepted / Pending
    pending_challenges = challenges.filter( challenger = request.user ).filter( accepted = 0 )

    # status = 2, 3, 4
    # Completed, Forfeit, Postponed
    past_challenges = challenges.filter( Q( challenger = request.user )|Q( challengee = request.user ) ).filter( Q( accepted = 2 )|Q( accepted = 3 )|Q( accepted = 4 ) )[:25]

    return render( request, "challenges.html", { 'open_challenges':open_challenges, 'pending_challenges': pending_challenges, 'past_challenges':past_challenges } )

@login_required
def message_matches( request ) :
    if request.method == "POST" :
        try :
            action    = request.POST['action']
            notice_id = request.POST['note_id']

            match     = Match.objects.get( pk = notice_id )
            other     = match.challenger if request.user == match.challengee else match.challengee

            if request.user == match.challenger or request.user == match.challengee :
                if action == "challenger_wins" :
                    match.choose_winner( match.challenger )
                    match.save()
                    messages.success( request, "You entered your results for your match against {} successfully".format( other.userprofile.handle ) )
                elif action == "challengee_wins" :
                    match.choose_winner( match.challengee )
                    match.save()
                    messages.success( request, "You entered your results for your match against {} successfully".format( other.userprofile.handle ) )
                elif action == "forfeit" :
                    match.forfeit = True
                    match.choose_winner( other )
                    match.save()
                    messages.success( request, "You forfeited your match against {} successfully".format( other.userprofile.handle ) )
            else:
                raise PlayerNotInvolved()
        except AttributeError :
            messages.error( request, "Tried to use an invalid command. Tell a programmer." )
        except KeyError :
            messages.error( request, "Not enough information to complete request." )
        except PlayerNotInvolved :
            messages.error( request, "Match not found" )

    matches = Match.objects.filter( Q(winner__isnull = True) & ( Q(challengee = request.user) | Q(challenger = request.user) ) ).order_by( '-date_challenged' )
    return render( request, "matches.html", { 'matches':matches } )

def message_detail( request ) :
    pass;

def message_send( request ) :
    pass;