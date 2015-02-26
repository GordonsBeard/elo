
class ChallengeValidationError( Exception ) :
    def __init__( self, error ) :
       self.value = error

    def __str__( self ) :
        return repr( self.value )

class ChallengeeIsChallenger( ChallengeValidationError ) :
    pass

class ChallengeeOutOfRange( ChallengeValidationError ) :
    def __init__( self, error, rankdiff ) :
        self.value    = error
        self.rankdiff = rankdiff

class ParticipantBusy( ChallengeValidationError ) :
    def __init__( self, error, user ) :
        self.value = error
        self.user  = user

class PlayerNotRanked( ChallengeValidationError ) :
    def __init__( self, error, ladder ) :
        self.value  = error
        self.ladder = ladder

