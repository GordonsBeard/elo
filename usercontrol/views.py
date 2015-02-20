from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from ladder.models import Rank, Challenge, Match
from datetime import datetime

PROFILE_RECENT_MATCHES  = 5     # How many matches to show under the "Recent Matches" header
PROFILE_ACTIVE_LADDERS  = 5     # How many ladders to show under the "Active Ladders" header

# Create your views here.

def profile( request, username ) :
  user        = get_object_or_404( User, username = username )
  stats       = { 
    "Ladders Joined":       Rank.objects.filter( player_id = user.pk ).count(), 
    "Challenges Issued":    Challenge.objects.filter( challenger_id = user.pk ).count(), 
    "Challenges Received":  Challenge.objects.filter( challengee_id = user.pk ).count(), 
    "Matches Won":          Match.objects.filter( winner_id = user.pk ).count(), 
    "Matches Lost":         Match.objects.filter( Q(winner_id__isnull = False) & ( Q(challengee = user) | Q(challenger = user) ) & ~Q(winner_id = user.pk) ).count(),
  }
  matches     = Match.objects.filter( winner_id__isnull = False ).filter( Q(challengee = user) | Q(challenger = user) ).order_by( '-date_complete' )[:PROFILE_RECENT_MATCHES]
  ranks       = [(r,r.ladder.latest_match()) for r in user.rank_set.order_by( '-ladder__created' )[:PROFILE_ACTIVE_LADDERS]]
  return render( request, "profile.html", { 'userp':user, 'stats':stats, 'matches':matches, 'ranks':ranks } )

def message_list( request ) :
  num_challenges  = Challenge.objects.filter( accepted = Challenge.STATUS_NOT_ACCEPTED ).count()
  num_matches     = Match.objects.filter( Q(winner__isnull = True) & ( Q(challengee = request.user) | Q(challenger = request.user) ) ).count()
  return render( request, "messages.html", { 'num_challenges':num_challenges, 'num_matches':num_matches } )

def message_challenges( request ) :
  if request.method == "POST" :
    try :
      action    = request.POST['action']
      notice_id = request.POST['note_id']

      challenge = Challenge.objects.get( pk = notice_id )
      if action == "accept_challenge" :
        challenge.accepted = Challenge.STATUS_ACCEPTED
      elif action == "decline_challenge" :
        challenge.accepted = Challenge.STATUS_FORFEIT
      challenge.save()
    except AttributeError :
      messages.error( "Tried to use an invalid command. Tell a programmer." )
    except KeyError :
      messages.error( "Not enough information to complete request." )

  challenges = Challenge.objects.filter( challengee = request.user, accepted = Challenge.STATUS_NOT_ACCEPTED ).order_by( '-match__date_challenged' )
  return render( request, "challenges.html", { 'challenges':challenges } )

def message_matches( request ) :
  if request.method == "POST" :
    try :
      action    = request.POST['action']
      notice_id = request.POST['note_id']

      match     = Match.objects.get( pk = notice_id )
      if action == "challenger_wins" :
        match.winner = match.challenger
      elif action == "challengee_wins" :
        match.winner = match.challengee
      elif action == "forfeit" :
        match.forfeit = True
        if request.user == match.challenger :
          match.winner = match.challengee
        else :
          match.winner = match.challenger

      match.save()
    except AttributeError :
      messages.error( "Tried to use an invalid command. Tell a programmer." )
    except KeyError :
      messages.error( "Not enough information to complete request." )

  matches = Match.objects.filter( Q(winner__isnull = True) & ( Q(challengee = request.user) | Q(challenger = request.user) ) ).order_by( '-date_challenged' )
  return render( request, "matches.html", { 'matches':matches } )

def message_detail( request ) :
  pass;

def message_send( request ) :
  pass;