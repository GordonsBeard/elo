import django

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase, RequestFactory
from ladder.models import Challenge, Ladder, Game, Rank, Match
from ladder.views import join_ladder, leave_ladder

django.setup()

## Tests to Implement:
# User should not be able to issue challenge with an open challenge
# Users should only be able to challenge proper arrows

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
        self.factory = RequestFactory()

        # users
        self.user1 = User.objects.create_user(username='TestUser 1', email='test1@test.com',  password='test')
        self.user2 = User.objects.create_user(username='TestUser 2', email='test2@test.com',  password='test')
        self.user3 = User.objects.create_user(username='TestUser 3', email='test3@test.com',  password='test')
        self.unranked_user = User.objects.create_user(username='Unranked User', email='unranked@test.com',  password='test')

        # game (Test Game [tg]) and ladder (default settings)
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        self.ladder = Ladder.objects.create(owner = self.user1, game = self.game)


    def test_ladder_creation(self):
        """ Tests that ladder was created with default settings. """

        self.assertEqual(self.ladder.max_players, '0')
        self.assertEqual(self.ladder.privacy, '0')
        self.assertEqual(self.ladder.signups, True)
        self.assertEqual(self.ladder.up_arrow, '2')
        self.assertEqual(self.ladder.down_arrow, '4')
        self.assertEqual(self.ladder.weekly_reset, None)
        self.assertEqual(self.ladder.challenge_cooldown, None)
        self.assertEqual(self.ladder.response_timeout, '3')

    def test_joining_ladder(self):
        """ Tests that joining a ladder (via join_ladder) places you in last place with an up arrow. """
        # FallbackStorage is needed to deal with a django bug
        request = self.factory.get('{0}/join'.format(self.ladder.slug))
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        for i, testUser in enumerate((self.user1, self.user2, self.user3)):
            # user joins the ladder
            request.user = testUser
            response = join_ladder(request, self.ladder.slug)
            players_in_ladder = self.ladder.ranked_players()

            # check the rank after hitting join_ladder
            testRank = Rank.objects.get(ladder = self.ladder, player = testUser)

            self.assertEqual(response.status_code, 302)     # check for 302 status (redirect)
            self.assertEqual(players_in_ladder, i + 1)      # should have n player(s)
            self.assertEqual(testRank.arrow, '0')           # should have an up arrow
            self.assertEqual(testRank.rank, i + 1)          # should have a rank of n

    def test_leaving_ladder(self):
        """ Tests that leaving a ladder removes player completely, moves everyone up a rank. """
        # FallbackStorage is needed to deal with a django bug
        request = self.factory.get('{0}/join'.format(self.ladder.slug))
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # ranks for ladder
        # user1:user2:user3 :: 1st:2nd:3rd
        Rank.objects.create(player = self.user1, rank = 1, arrow = '0', ladder = self.ladder)
        Rank.objects.create(player = self.user2, rank = 2, arrow = '0', ladder = self.ladder)
        Rank.objects.create(player = self.user3, rank = 3, arrow = '0', ladder = self.ladder)
        
        players_in_ladder = self.ladder.ranked_players()
        
        # we should have 3 players in the ladder
        self.assertEqual(players_in_ladder, 3)
        
        # delete user 2
        request.user = self.user2
        response = leave_ladder(request, self.ladder.slug)
        players_in_ladder = self.ladder.ranked_players()

        # we should now have 2 players in the ladder
        self.assertEqual(players_in_ladder, 2)

        testRank1 = Rank.objects.get(player = self.user1, ladder = self.ladder)
        testRank3 = Rank.objects.get(player = self.user3, ladder = self.ladder)

        # make sure user1:user3 :: 1st:2nd
        self.assertEqual(testRank1.rank, 1)
        self.assertEqual(testRank3.rank, 2)

        # delete user 1
        request.user = self.user1
        response = leave_ladder(request, self.ladder.slug)
        players_in_ladder = self.ladder.ranked_players()

        # we should now have 1 player left in the ladder
        self.assertEqual(players_in_ladder, 1)

        testRank3 = Rank.objects.get(player = self.user3, ladder = self.ladder)

        # make sure the only player left is rank 1
        self.assertEqual(testRank3.rank, 1)

## Challenges
class Test_Challenge_Objects(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.challenger = User.objects.create_user(username='TestChallenger', email='challenger@test.com',  password='test')
        self.challengee = User.objects.create_user(username='TestChallengee', email='challengee@test.com',  password='test')

        # game and ladder
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

    def test_challenge_creation(self):
        """ Tests challenge is created with defaults. """
        raise NotImplementedError  
    
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