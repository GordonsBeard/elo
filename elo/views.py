import json, urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

from django_openid_auth.models import UserOpenID
from django_openid_auth.views import parse_openid_response

from itertools import chain

from elo.models import UserProfile
from ladder.models import Game, Match, Rank, Ladder, Challenge

def index(request):

    game_list = Game.objects.all()

    match_list = Match.objects.all().order_by('-date_complete')

    rank_list = Rank.objects.all()

    ladder_list = Ladder.objects.all()

    try:
        challenger_list = Challenge.objects.filter(match__challenger = request.user, accepted=False)
    except Exception, e:
        challenger_list = []
    try:
        challengee_list = Challenge.objects.filter(match__challengee = request.user, accepted=False)
    except Exception, e:
        challengee_list = []

    your_challenges = list(chain(challenger_list, challengee_list))

    return render_to_response('home.html', {'game_list':game_list, 'match_list':match_list, 'rank_list':rank_list, 'ladder_list':ladder_list, 'your_challenges':your_challenges}, context_instance=RequestContext(request))

def login(request):
    data = {}
    data['response'] = request.GET["openid.claimed_id"]
    data['id'] = request.GET["openid.claimed_id"][36:]
    data['url'] = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+settings.STEAM_API_KEY+"&steamids="+data['id']

    claim = data['response']

    # Get public info
    data['info'] = json.loads(urllib.urlopen(data["url"]).read())["response"]["players"][0]

    handle = data['info']['personaname']
    steamid = data['info']['steamid']
    url = data['info']['profileurl']
    avatar = data['info']['avatar']
    avatarM = data['info']['avatarmedium']
    avatarL = data['info']['avatarfull']
    try:
        primarygroup = data['info']['primaryclanid']
    except KeyError:
        primarygroup = ""
    try:
        realname = data['info']['realname']
    except KeyError:
        realname = ""

    # Find the user
    try:
        useroid = UserOpenID.objects.get(claimed_id=claim)

        # Get them by steamid, then get the User instance associated with this
        # profile.
        userP = UserProfile.objects.get(steamid=steamid)
        user = User.objects.get(id=userP.user_id)

    # New user
    except UserOpenID.DoesNotExist:
        # Slugify their current display name, this will be used for internal control panels only.
        slugName = "{0}-{1}".format(slugify(handle), steamid[len(steamid)-3:len(steamid)])
        user = User.objects.create_user(username=slugName, email='', password='!')
        user.save()
        useroid = UserOpenID(user=user, claimed_id=claim, display_id=claim)
        useroid.save()
    try:
        up = UserProfile.objects.get(user_id=user.id)
    except UserProfile.DoesNotExist:
        up = UserProfile(user_id=user.id)
        up.save()

    # User exists, fill out profile, which is auto-filled with blanks atm.
    up.handle=handle
    up.steamid=steamid
    up.url=url
    up.avatar=avatar
    up.avatarM=avatarM
    up.avatarL=avatarL
    up.primarygroup=primarygroup
    up.realname=realname

    up.save()

    # Stole these lines from inside the openid_auth files. idk why now
    # PROB. IMPORTANT THO
    openid_response = parse_openid_response(request)
    user = authenticate(openid_response=openid_response)

    auth_login(request, user)

    return HttpResponseRedirect('/')

def logout_view(request):
    logout(request)
    return HttpResponse('Logged out.')