import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
import time # for measuring execution time
import datetime # to convert seconds to hours:minutes:seconds


def reportMemUsage(startTime = None):

	# ru_maxrss is actually in kilobytes: http://man7.org/linux/man-pages/man2/getrusage.2.html
    displayString = "Memory usage: %s kB \t Runtime: " % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) 

    if startTime is not None: displayString += str(datetime.timedelta(seconds=( time.time()- startTime) ))
    
    print displayString

    return None

if __name__ == '__main__':

	startTime = time.time()

	reportMemUsage(startTime = startTime)


