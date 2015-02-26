
class ChallengeValidationError( Exception ) :
    pass

class ChallengeeIsChallenger( ChallengeValidationError ) :
    pass

class ChallengeeOutOfRange( ChallengeValidationError ) :
    pass

class ParticipantBusy( ChallengeValidationError ) :
    pass

class PlayerNotInvolved( ChallengeValidationError ) :
    pass

class PlayerNotRanked( ChallengeValidationError ) :
    pass

