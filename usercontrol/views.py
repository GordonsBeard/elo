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
  pass;

def message_detail( request ) :
  pass;

def message_send( request ) :
  pass;