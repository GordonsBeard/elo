from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import transaction
from django.db.models import Q
from django.test import Client, TestCase, RequestFactory
from django.utils.importlib import import_module

# Modules to tests less or more
from ladder.models import Challenge, Ladder, Game, Rank, Match
from ladder.views import join_ladder, leave_ladder, issue_challenge
from ladder.exceptions import ChallengeeOutOfRange, ChallengeeIsChallenger, PlayerNotRanked, ParticipantBusy

from datetime import datetime
from random import random, seed

# Needed for tests to run in VS
import django
django.setup()

def generate_random_valid_challenge( ladder ) :
    valid_challengers = ladder.rank_set.exclude( rank = 1 )
    challenger        = valid_challengers.order_by('?')[0] # '?' ordering is random

    if challenger.arrow == u'0' :
        valid_challengees = ladder.rank_set.filter( rank__lt = challenger.rank, rank__gt = challenger.rank - int( ladder.up_arrow ) - 1 )
    else :
        valid_challengees = ladder.rank_set.filter( rank__gt = challenger.rank, rank__lt = challenger.rank + int( ladder.down_arrow ) + 1 )

    challengee = valid_challengees.order_by('?')[0]

    return Challenge.objects.create( challenger = challenger.player, challengee = challengee.player, ladder = ladder )

def generate_random_completed_match( ladder ) :
    challenge = generate_random_valid_challenge( ladder )
    challenge.accept()
    challenge.save()

    match = ladder.match_set.get( related_challenge = challenge )

    if random() < 0.5 :
        match.choose_winner( 0 )
    else :
        match.choose_winner( 1 )
    match.save()
    return match


## Tests to Implement:
# User should not be able to issue challenge with an open challenge
# Users should only be able to challenge proper arrows

class TestClient(Client):

    def login_user(self, user):
        """
        Login as specified user, does not depend on auth backend (hopefully)

        This is based on Client.login() with a small hack that does not
        require the call to authenticate()
        """
        if not 'django.contrib.sessions' in settings.INSTALLED_APPS:
            raise AssertionError("Unable to login without django.contrib.sessions in INSTALLED_APPS")
        user.backend = "%s.%s" % ("django.contrib.auth.backends", "ModelBackend")
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        if self.session:
            request.session = self.session
        else:
            request.session = engine.SessionStore()
        login(request, user)

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.cookies[session_cookie].update(cookie_data)

        # Save the session values.
        request.session.save()

## Game
class Test_Game_Objects(TestCase):
    def setUp(self):
        Game.objects.create(name = "Test Game", abv = "tg")

    def test_game_slug(self):
        """ Tests that slugify is working as expected. """
        test_game = Game.objects.get(slug="test-game")
        self.assertEqual(test_game.name, "Test Game")

## Ladder
class Test_Ladder_Objects(TestCase):
    def setUp(self):

        # users
        self.users = []
        for i in range(10) :
            self.users.append( User.objects.create_user(username="test_user_{}".format(i), email="test{}@test.com".format(i), password='test') )

        # game (Test Game [tg]) and ladder (default settings)
        self.game = Game.objects.create(name = "Test Game", abv = "tg")

    def test_ladder_creation(self):
        """ Tests that ladder was created with default settings. """
        test_ladder = Ladder.objects.create(owner = self.users[0], game = self.game, name = "Test Party Ladder")
        self.assertEqual(test_ladder.max_players, '0')
        self.assertEqual(test_ladder.privacy, '0')
        self.assertEqual(test_ladder.signups, True)
        self.assertEqual(test_ladder.up_arrow, '2')
        self.assertEqual(test_ladder.down_arrow, '4')
        self.assertEqual(test_ladder.weekly_reset, None)
        self.assertEqual(test_ladder.challenge_cooldown, None)
        self.assertEqual(test_ladder.response_timeout, '3')
        self.assertEqual(test_ladder.name, 'Test Party Ladder')
        self.assertEqual(test_ladder.owner, self.users[0])

    def test_ladder_membership(self):
        test_ladder = Ladder.objects.create(owner = self.users[0], game = self.game, name = "Test Party Ladder")
        test_rank   = Rank.objects.create(player = self.users[0], rank = 1, arrow = 0, ladder = test_ladder)
        self.assertEqual(test_ladder.is_user_ranked(self.users[0]), True)

    def test_ladder_challenges(self):
        test_ladder = Ladder.objects.create(owner = self.users[0], game = self.game, name = "Test Party Ladder")
        def _add_player_to_test_ladder( player ) :
            return Rank.objects.create( player = player, rank = test_ladder.rank_set.all().count() + 1, arrow = 0, ladder = test_ladder )

        def _create_challenge( challenger, challengee ) :
            return Challenge.objects.create( challenger = challenger, challengee = challengee, ladder = test_ladder )

        test_rank_1 = _add_player_to_test_ladder( self.users[0] )
        test_rank_2 = _add_player_to_test_ladder( self.users[1] )
        test_rank_3 = _add_player_to_test_ladder( self.users[2] )
        test_rank_4 = _add_player_to_test_ladder( self.users[3] )

        self.assertEqual(test_ladder.latest_match(), "Never")

        challenge_1 = _create_challenge( self.users[1], self.users[0] )
        challenge_1.accept()
        challenge_1.save()

        self.assertEqual(test_ladder.match_set.all().count(), 1)
        latest_match = test_ladder.latest_match()
        self.assertEqual(latest_match, Match.objects.get( related_challenge = challenge_1 ).date_challenged)

        challenge_2 = _create_challenge( self.users[3], self.users[2] )
        challenge_2.accept()
        challenge_2.save()

class Test_Ladder_Validation( TestCase ) :
    def _add_user_to_ladder( self, user ) :
        return Rank.objects.create( player = user, rank = self.ladder.rank_set.count() + 1, arrow = Rank.ARROW_UP, ladder = self.ladder )

    def _create_user( self, i ) :
        return User.objects.create_user( username = "TestUser%d" % i, email = "test%d@test.com" % i, password = 'test' )

    def setUp( self ) :
        self.users  = [self._create_user( i ) for i in range( 10 )]

        self.game   = Game.objects.create( name = "Test Game", abv = "tg" )
        self.ladder = Ladder.objects.create( name = "Test Ladder", owner = self.users[0], game = self.game )

    def test_basic_valid_challenge( self ) :
        test_rank_1 = self._add_user_to_ladder( self.users[0] )
        test_rank_2 = self._add_user_to_ladder( self.users[1] )

        self.assertRaises( ChallengeeIsChallenger, lambda: Challenge.objects.create( challenger = self.users[0], challengee = self.users[0], ladder = self.ladder ) )
        self.assertRaises( ChallengeeOutOfRange, lambda: Challenge.objects.create( challenger = self.users[0], challengee = self.users[1], ladder = self.ladder ) )
        self.assertRaises( PlayerNotRanked, lambda: Challenge.objects.create( challenger = self.users[0], challengee = self.users[2], ladder = self.ladder ) )
        self.assertIsNotNone( Challenge.objects.create( challenger = self.users[1], challengee = self.users[0], ladder = self.ladder ) )

    def test_large_ladder_challenge( self ) :
        for u in self.users :
            self._add_user_to_ladder( u )
        Rank.objects.get( ladder = self.ladder, player = self.users[1] ).arrow = Rank.ARROW_DOWN

        self.assertRaises( ChallengeeOutOfRange, lambda: Challenge.objects.create( challenger = self.users[9], challengee = self.users[0], ladder = self.ladder ) )
        self.assertRaises( ChallengeeOutOfRange, lambda: Challenge.objects.create( challenger = self.users[1], challengee = self.users[9], ladder = self.ladder ) )
        self.assertIsNotNone( Challenge.objects.create( challenger = self.users[5], challengee = self.users[4], ladder = self.ladder ) )
        self.assertRaises( ParticipantBusy, lambda: Challenge.objects.create( challenger = self.users[6], challengee = self.users[4], ladder = self.ladder ) )
        self.assertIsNotNone( Challenge.objects.create( challenger = self.users[2], challengee = self.users[0], ladder = self.ladder ) )
        self.assertIsNotNone( Challenge.objects.create( challenger = self.users[9], challengee = self.users[8], ladder = self.ladder ) )
        self.assertIsNotNone( Challenge.objects.create( challenger = self.users[3], challengee = self.users[1], ladder = self.ladder ) )

    def test_random_challenges( self ) :
        for u in self.users :
            self._add_user_to_ladder( u )

        for _ in range( 20 ) :
            challenge = generate_random_valid_challenge( self.ladder )
            self.assertIsNotNone( challenge )
            challenge.delete()

class Test_Ladder_Views(TestCase):
    def setUp(self):
        #self.factory = RequestFactory()

        # users
        self.user1 = User.objects.create_user(username='TestUser 1', email='test1@test.com',  password='test')
        self.user2 = User.objects.create_user(username='TestUser 2', email='test2@test.com',  password='test')
        self.user3 = User.objects.create_user(username='TestUser 3', email='test3@test.com',  password='test')
        self.unranked_user = User.objects.create_user(username='Unranked User', email='unranked@test.com',  password='test')
        
        # game (Test Game [tg]) and ladder (default settings)
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        self.ladder = Ladder.objects.create(name = "Test Ladder", owner = self.user1, game = self.game)

    def test_join_ladder_view_single(self):
        """ Tests that joining a ladder (via views) places you in last place with an up arrow. """
        
        # Log the user in first
        client = TestClient()
        client.login_user(self.user1)
        join_ladder_url = '/l/{0}/join'.format( self.ladder.slug )

        # Get the confirmation of the Join
        request = client.get('/l/{0}/join/'.format(self.ladder.slug))
        self.assertEqual( request.status_code, 200 )
        self.assertInHTML( '<input type="submit" value="Join" />', request.content )

        # Submit the Join
        response = client.post('/l/{0}/join/'.format( self.ladder.slug ) )
        
        # Should be redirected back to the ladder
        expected_url = 'http://testserver/l/{0}'.format( self.ladder.slug )
        self.assertRedirects(response, expected_url, status_code = 302, target_status_code = 301)

        # User should now be ranked on this ladder.
        testUserRank = Rank.objects.get( player = self.user1, ladder = self.ladder )
        self.assertEqual( testUserRank.arrow, testUserRank.ARROW_UP )
        self.assertEqual( testUserRank.rank, 1 )

        # Message should state you've joined the ladder
        # Currently just checking for the existence of a message.
        self.assertIn('messages', response.cookies)

    def test_join_ladder_view_multi(self):
        """ Tests that joining a ladder (via views) with multiple players place you in last place with an up arrow. """
        
        test_users = [self.user1, self.user2, self.user3]

        for i, single_user in enumerate(test_users):

            # Log the user in first
            client = TestClient()
            client.login_user(single_user)
            join_ladder_url = '/l/{0}/join/'.format( self.ladder.slug )

            # Get the confirmation of the Join
            request = client.get('/l/{0}/join/'.format(self.ladder.slug))
            self.assertEqual( request.status_code, 200 )
            self.assertInHTML( '<input type="submit" value="Join" />', request.content )

            # Submit the Join
            response = client.post('/l/{0}/join/'.format( self.ladder.slug ) )
        
            # Should be redirected back to the ladder
            expected_url = 'http://testserver/l/{0}'.format( self.ladder.slug )
            self.assertRedirects(response, expected_url, status_code = 302, target_status_code = 301)

            # User should now be ranked on this ladder.
            testUserRank = Rank.objects.get( player = single_user, ladder = self.ladder )
            self.assertEqual( testUserRank.arrow, testUserRank.ARROW_UP )
            self.assertEqual( testUserRank.rank, i + 1 )

            # Log this user out and begin the process again.
            client.logout()

        # Make sure that we now have 3 ranks on this Ladder
        actual_ranks = Rank.objects.filter( ladder = self.ladder )
        expected_ranks = len(test_users)
        self.assertEqual( actual_ranks.count(), expected_ranks) 

    #def test_leaving_ladder(self):
    #    """ Tests that leaving a ladder removes player completely, moves everyone up a rank. """
    #    # FallbackStorage is needed to deal with a django bug
    #    request = self.factory.get('/l/{0}/join'.format(self.ladder.slug))
    #    setattr(request, 'session', 'session')
    #    messages = FallbackStorage(request)
    #    setattr(request, '_messages', messages)

    #    # ranks for ladder
    #    # user1:user2:user3 :: 1st:2nd:3rd
    #    Rank.objects.create(player = self.user1, rank = 1, arrow = '0', ladder = self.ladder)
    #    Rank.objects.create(player = self.user2, rank = 2, arrow = '0', ladder = self.ladder)
    #    Rank.objects.create(player = self.user3, rank = 3, arrow = '0', ladder = self.ladder)
        
    #    players_in_ladder = self.ladder.ranked_players()
        
    #    # we should have 3 players in the ladder
    #    self.assertEqual(players_in_ladder, 3)
        
    #    # delete user 2
    #    request.user = self.user2
    #    response = leave_ladder(request, self.ladder.slug)
    #    players_in_ladder = self.ladder.ranked_players()

    #    # we should now have 2 players in the ladder
    #    self.assertEqual(players_in_ladder, 2)

    #    testRank1 = Rank.objects.get(player = self.user1, ladder = self.ladder)
    #    testRank3 = Rank.objects.get(player = self.user3, ladder = self.ladder)

    #    # make sure user1:user3 :: 1st:2nd
    #    self.assertEqual(testRank1.rank, 1)
    #    self.assertEqual(testRank3.rank, 2)

    #    # delete user 1
    #    request.user = self.user1
    #    response = leave_ladder(request, self.ladder.slug)
    #    players_in_ladder = self.ladder.ranked_players()

    #    # we should now have 1 player left in the ladder
    #    self.assertEqual(players_in_ladder, 1)

    #    testRank3 = Rank.objects.get(player = self.user3, ladder = self.ladder)

    #    # make sure the only player left is rank 1
    #    self.assertEqual(testRank3.rank, 1)

## Challenges
#class Test_Challenge_Objects(TestCase):
#    def setUp(self):
#        self.factory = RequestFactory()

#        # users
#        self.user1 = User.objects.create_user(username='TestChallenger', email='user1@test.com',  password='test')
#        self.user2 = User.objects.create_user(username='TestChallengee', email='user2@test.com',  password='test')

#        # game and ladder
#        self.game = Game.objects.create(name = "Test Game", abv = "tg")
#        self.ladder = Ladder.objects.create(owner = self.user1, game = self.game)

#        # ranks
#        self.user1rank = Rank.objects.create(player = self.user1, rank = 1, arrow = '0', ladder = self.ladder)
#        self.user2rank = Rank.objects.create(player = self.user2, rank = 2, arrow = '0', ladder = self.ladder)

#    def test_issue_challenge(self):
#        """ Tests that a challenge is issued to the correct player/ladder """
#        # TODO: Currently cannot login because of OpenID
#        c = Client()
#        client.login_user(self.user)
        
#        # user1 and user2 are on the ladder.
#        response = c.post('/l/challenge', { 'challenger':self.user2.pk, 'challengee_id':self.user1.pk, 'ladder_slug': self.ladder.slug })
#        print response

#        # test redirect
#        self.assertEqual(response.status_code, 302)

#        # Check if challenge exists
#        print Challenge.objects.all()
#        test_challenge = Challenge.objects.filter( Q( challengee = self.user2 ) | Q( challenger = self.user2 ) )
#        print test_challenge.count()
#        self.assertEqual( 1, test_challenge.count() )
        

    #def test_challenge_creation(self):
    #    """ Tests challenge is created with defaults. """
    #    raise NotImplementedError  
    
    #def test_challenge_accepted(self):
    #    """ Tests that accepting a challenge will create matching Match object. """
    #    raise NotImplementedError  
    
    #def test_challenge_forfeit(self):
    #    """ Tests declining a challenge, resulting in a loss. """
    #    raise NotImplementedError  

    #def test_challenge_postpone(self):
    #    """ Tests postponing a match, adding more time to the request timeout. """
    #    raise NotImplementedError  
    
    #def test_challenge_complete(self):
    #    """ Tests completing a challenge, updating linked Match object. """
    #    raise NotImplementedError  

## Match
#class Test_Match_Objects(TestCase):
#    def setUp(self):
#        self.factory = RequestFactory()

#        # users
#        self.challenger = User.objects.create_user(username='TestChallenger', email='challenger@test.com',  password='test')
#        self.challengee = User.objects.create_user(username='TestChallengee', email='challengee@test.com',  password='test')

#        # game and ladder
#        self.game = Game.objects.create(name = "Test Game", abv = "tg")
#        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

#    def test_match_creation(self):
#        """ Tests default setings for a match """
#        raise NotImplementedError  

## Rankings
#class Test_Rank_Objects(TestCase):
#    def setUp(self):
#        self.factory = RequestFactory()

#        # users
#        self.challenger = User.objects.create_user(username='TestChallenger', email='challenger@test.com',  password='test')
#        self.challengee = User.objects.create_user(username='TestChallengee', email='challengee@test.com',  password='test')

#        # game and ladder
#        self.game = Game.objects.create(name = "Test Game", abv = "tg")
#        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

#    def test_winning_noswap(self):
#        """ Tests winning a match, no swap of arrows or ranks. """
#        raise NotImplementedError  
    
#    def test_winning_swap(self):
#        """ Tests winning a match, swapping arrows and ranks. """
#        raise NotImplementedError  
    
#    def test_losing_noswap(self):
#        """ Tests losing a match, no swap of arrows and ranks. """
#        raise NotImplementedError  

#    def test_losing_swap(self):
#        """ Tests losing a match, swapping arrows and ranks. """
#        raise NotImplementedError  

if __name__ == '__main__':
    unittest.main()