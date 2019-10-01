import numpy as np

def getArrayConfInterval( npAppray, confidenceValue = 0.68,  intervalCenter = None):

    if intervalCenter is None: intervalCenter = np.mean(npAppray)

    absDistanceToMean = np.abs( npAppray - intervalCenter  )

    sortIndex =  np.argsort(absDistanceToMean)

    arraySortedByDistancetoMean = npAppray[  sortIndex ]

    lowLimit =  None; highLimit = None

    # if the array entries are not too badly distributed
    confIndex = int( round( len(npAppray)*confidenceValue) )

    for x in xrange(  len(npAppray) ):
        arrayVal = arraySortedByDistancetoMean[x]
        if    arrayVal < intervalCenter : lowLimit = arrayVal
        else :                            highLimit = arrayVal


        if x >= confIndex:
            if highLimit is not None and lowLimit is not None: break

    return (lowLimit , highLimit)


if __name__ == '__main__':

    lowList = []; highList = []

    for nDraws in xrange(100):

        gaussArray = np.random.normal(0,1,1000)

        low, high = getArrayConfInterval( gaussArray, confidenceValue = 0.9545,  intervalCenter = None)

        lowList.append(low)
        highList.append(high)

        print low, high

    print "\n"
    print np.mean(lowList), np.std(lowList)
    print np.mean(highList), np.std(highList)


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
