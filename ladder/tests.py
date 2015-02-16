from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory
from ladder.models import Challenge, Ladder, Game, Rank, Match

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
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        self.user = User.objects.create_user(
            username='TestUser', email='test@test.com',  password='test')

    def test_ladder_creation(self):
        """ Tests that ladder was created with default settings. """
        ladder = Ladder.objects.create(owner = self.user, game = self.game)

        self.assertEqual(ladder.max_players, '0')
        self.assertEqual(ladder.privacy, '0')
        self.assertEqual(ladder.signups, True)
        self.assertEqual(ladder.up_arrow, '2')
        self.assertEqual(ladder.down_arrow, '4')
        self.assertEqual(ladder.weekly_reset, None)
        self.assertEqual(ladder.challenge_cooldown, None)
        self.assertEqual(ladder.response_timeout, '3')

    def test_joining_ladder(self):
        """ Tests that joining a ladder places you in last place with an up arrow. """
        raise NotImplementedError

    def test_leaving_ladder(self):
        """ Tests that leaving a ladder removes player completely, moves everyone up a rank. """
        raise NotImplementedError        

## Challenges
class Test_Challenge_Objects(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.challenger = User.objects.create_user(
            username='TestChallenger', email='challenger@test.com',  password='test')
        self.challengee = User.objects.create_user(
            username='TestChallengee', email='challengee@test.com',  password='test')

        # game and ladder
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

    def test_challenge_creation(self):
        """ Tests challenge is created with defaults. """
        raise NotImplementedError  
    
    def test_challenge_accepted(self):
        """ Tests that accepting a challenge will create matching Match object. """
        raise NotImplementedError  
    
    def test_challenge_forfeit(self):
        """ Tests declining a challenge, resulting in a loss. """
        raise NotImplementedError  

    def test_challenge_postpone(self):
        """ Tests postponing a match, adding more time to the request timeout. """
        raise NotImplementedError  
    
    def test_challenge_complete(self):
        """ Tests completing a challenge, updating linked Match object. """
        raise NotImplementedError  

## Match
class Test_Match_Objects(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.challenger = User.objects.create_user(
            username='TestChallenger', email='challenger@test.com',  password='test')
        self.challengee = User.objects.create_user(
            username='TestChallengee', email='challengee@test.com',  password='test')

        # game and ladder
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

    def test_match_creation(self):
        """ Tests default setings for a match """
        raise NotImplementedError  

## Rankings
class Test_Rank_Objects(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # users
        self.challenger = User.objects.create_user(
            username='TestChallenger', email='challenger@test.com',  password='test')
        self.challengee = User.objects.create_user(
            username='TestChallengee', email='challengee@test.com',  password='test')

        # game and ladder
        self.game = Game.objects.create(name = "Test Game", abv = "tg")
        ladder = Ladder.objects.create(owner = self.challenger, game = self.game)

    def test_winning_noswap(self):
        """ Tests winning a match, no swap of arrows or ranks. """
        raise NotImplementedError  
    
    def test_winning_swap(self):
        """ Tests winning a match, swapping arrows and ranks. """
        raise NotImplementedError  
    
    def test_losing_noswap(self):
        """ Tests losing a match, no swap of arrows and ranks. """
        raise NotImplementedError  

    def test_losing_swap(self):
        """ Tests losing a match, swapping arrows and ranks. """
        raise NotImplementedError  

if __name__ == '__main__':
    unittest.main()