from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext

from itertools import chain

from django.urls.base import reverse

from ladder.models import Game, Match, Rank, Ladder, Challenge

def index(request):

    game_list = Game.objects.all()

    match_list = Match.objects.all().order_by('-date_complete')

    rank_list = Rank.objects.all()

    ladder_list = Ladder.objects.all()

    try:
        challenger_list = Challenge.objects.filter(match__challenger = request.user, accepted=False)
    except Exception:
        challenger_list = []
    try:
        challengee_list = Challenge.objects.filter(match__challengee = request.user, accepted=False)
    except Exception:
        challengee_list = []

    your_challenges = list(chain(challenger_list, challengee_list))

    return render(request, 'home.html', {'game_list':game_list, 'match_list':match_list, 'rank_list':rank_list, 'ladder_list':ladder_list, 'your_challenges':your_challenges}, context_instance=RequestContext(request))

def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out!")
    return HttpResponseRedirect(reverse('index'))