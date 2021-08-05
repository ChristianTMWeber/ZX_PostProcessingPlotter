import resource # print 'Memory usage: %s (kB)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
import time # for measuring execution time
import datetime # to convert seconds to hours:minutes:seconds


def reportMemUsage(startTime = None, defaultTime = time.time() ):

    # ru_maxrss is actually in kilobytes: http://man7.org/linux/man-pages/man2/getrusage.2.html

    memoryUsedMB =  round( float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/1024 )

    displayString = "Memory usage: %i MiB " % (memoryUsedMB) 

    if startTime is None:  referenceTime = defaultTime
    else:                  referenceTime = startTime
   
    displayString += "\t Runtime: " + str(datetime.timedelta(seconds=( time.time() - referenceTime) ))
    
    print displayString

    return None

if __name__ == '__main__':

    startTime = time.time()

    reportMemUsage()
    reportMemUsage(startTime = startTime)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


