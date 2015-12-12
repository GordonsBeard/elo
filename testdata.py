from ladder.tests import generate_random_completed_match
from ladder.models import Ladder

def gltm( count ) :
    margin = len( str( count ) ) + 2
    for i in range( count ) :
        match = generate_random_completed_match( Ladder.objects.get(pk=1) )
        print ("{:<%d}{} WINNER: {}" % margin).format( i + 1, match, match.winner.username )