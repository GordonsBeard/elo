import time

def output_benchmark_times( fn ) :
  def _benchmarked_fn( *args, **kwargs ) :
    start   = time.time()
    result  = fn( *args, **kwargs )
    print( "Execution of {} took {} seconds".format( fn.__name__, time.time() - start ) )
    return result
  return _benchmarked_fn