import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
import time # for measuring execution time
import datetime # to convert seconds to hours:minutes:seconds


def reportMemUsage(startTime = None):

    displayString = "Memory usage: %s kB \t Runtime: " % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8) 

    if startTime is not None: displayString += str(datetime.timedelta(seconds=( time.time()- startTime) ))
    
    print displayString

    return None

if __name__ == '__main__':

	startTime = time.time()

	reportMemUsage(startTime = startTime)


