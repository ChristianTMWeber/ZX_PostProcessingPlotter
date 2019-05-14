import ROOT
import numpy as np
import plotPostProcess as postProcess
import matplotlib.pyplot as plt # to plot the np.array
from scipy.optimize import brute  # for the fittin'


def convertTH2toNumpyArray(hist ): # plot comes out rotated, fix eventually
    x_bins = hist.GetNbinsX()
    y_bins = hist.GetNbinsY()
    
    bins = np.zeros((x_bins,y_bins))

    for y_bin in xrange(y_bins): 
        for x_bin in xrange(x_bins): 
            bins[x_bin,y_bin] = hist.GetBinContent(x_bin + 1,y_bin + 1)

    return bins

def fillTHWithNumpyArray(fillHist,npArray):

    if   len(npArray.shape) == 1 : 
        assert isinstance(fillHist, ROOT.TH1) and not isinstance(fillHist, ROOT.TH2)

        for x in xrange(0,npArray.shape[0]):
                fillHist.SetBinContent(x+1, npArray[x])
                fillHist.SetBinError(x+1, 0.)


    elif len(npArray.shape) == 2 : 
        assert  isinstance(fillHist, ROOT.TH2)

        for x in xrange(0,npArray.shape[0]):
            for y in xrange(0,npArray.shape[1]):
                fillHist.SetBinContent(x+1,y+1, npArray[x,y])
                fillHist.SetBinError(x+1,y+1, 0.)

    return None

def getXYFromNumpyArrayIndex( x , y, TH2):
    return  aggregateSignalTH2s.GetXaxis().GetBinLowEdge(x+1) , aggregateSignalTH2s.GetYaxis().GetBinLowEdge(y+1)

def makeM4lTH2MaskFromFunction( m4lCutFunction, referenceTH2 ):
    # Let's fill a copy of the referenceTH2 with the output of the m4lCutFunction
    # This should make it a mask-like histograms, with bins that are within the limts being 1 and bins outside the limts 0
    # m4lCutFunction needs to be a function of xValue and yValue

    maskTH2 = referenceTH2.Clone("m4lCutMask")
    maskTH2.SetTitle("m4lCutMask")


    x_bins = maskTH2.GetNbinsX()
    y_bins = maskTH2.GetNbinsY()

    
    for y_bin in xrange(y_bins+1): 
        for x_bin in xrange(x_bins+1): 

            xVal = maskTH2.GetXaxis().GetBinCenter(x_bin)
            yVal = maskTH2.GetYaxis().GetBinCenter(y_bin)

            binOK = m4lCutFunction(xVal, yVal)

            maskTH2.SetBinContent(x_bin , y_bin , int(binOK) )

    return maskTH2

def getMaxSignificanceMask(signal,background, startingMask = None): # assuming signal and background are numpy arrays

    if startingMask is None: 
        saveValues = np.zeros(signal.shape)
        removeValues = signal.copy()

    significanceOld = -2;    significanceNew = -1

    while significanceNew > significanceOld:

        significanceOld = significanceNew

        xyMax = np.unravel_index(np.argmax(removeValues, axis=None), removeValues.shape) # x,y coordinate of maximum

        saveValues[xyMax] = signal[xyMax]
        removeValues[xyMax] = 0

        significanceNew = saveValues.sum() / np.sqrt( (background*(saveValues>0)).sum() )

    return saveValues>0


def getRectangle( anArray , xLow, xHigh, yLow, yHigh ):

    outArray = np.zeros( anArray.shape , dtype=type(anArray[0,0]))

    for x in xrange( int(xLow), int(xHigh) +1 ): 
        for y in xrange( int(yLow), int(yHigh) ): outArray[x,y] = 1 

    return outArray

def getBoundingBoxParameters(mask):

    # get upper y bounding box 
    xMax , yMax = mask.shape

    for x in xrange(0, xMax,+1 ): 
        if any(mask[x,:]): xHigh = x; continue

    for x in xrange(xMax-1, 0-1 ,-1 ): 
        if any(mask[x,:]): xLow = x; continue

    for y in xrange(0, yMax,+1 ): 
        if any(mask[:,y]): yHigh = y; continue

    for y in xrange(yMax-1, 0-1 ,-1 ): 
        if any(mask[:,y]): yLow = y; continue

    return xLow, xHigh, yLow, yHigh


def drawRectangularBoundingBox(mask):

    xLow, xHigh, yLow, yHigh = getBoundingBoxParameters(mask)

    maskCopy = getRectangle( mask , xLow, xHigh, yLow, yHigh )

    #maskCopy = mask.copy()
    #for x in xrange(xBounds[0],xBounds[1]+1): 
    #    for y in xrange(yBounds[0],yBounds[1]+1): maskCopy[x,y] = 1 

    return maskCopy


def fixHolesInMask(mask):

    xMax , yMax = mask.shape

    for x in xrange(1, xMax-1 ):  # let's ignore the outermost pixels for now
        for y in xrange(1, yMax-1 ):

            if mask[x,y] == 0:
                # if this is greater than 2, then the current pixel is sourrounded by at least 3 active ones 
                if (mask[x-1,y] + mask[x+1,y] + mask[x,y-1] + mask[x,y+1] ) > 2 :

                    mask[x,y] = 1

    return mask 

def aggregateMasks( maskList ):

    if isinstance(maskList[0],np.ndarray): 

        aggregateMask = maskList[0].copy()
        for aMask in maskList[1:]: aggregateMask = aggregateMask + aMask

    elif isinstance(maskList[0],ROOT.TH2):

        aggregateMask = maskList[0].Clone("aggregateHist")
        for aMask in maskList[1:]: aggregateMask.Add(aMask)

    else: aggregateMask = None

    return aggregateMask


def getSignificanceFromBox(boundingBoxParams, signal, background):

    xLow   = boundingBoxParams[0]
    xHigh  = boundingBoxParams[1]
    yLow   = boundingBoxParams[2]
    yHigh  = boundingBoxParams[3]

    mask = getRectangle( signal , xLow, xHigh, yLow, yHigh )

    significance = calculateSignificance(signal, background, mask)

    return significance

def calculateSignificance(signal, background, mask):

    signalCount     = (signal * mask).sum()
    backgroundCount = (background * mask).sum()

    significance = signalCount / np.sqrt(backgroundCount)

    return significance

def significanceDef(signal, background):
    return signal / np.sqrt(background)


def drawArray(anArray):
    plt.imshow(np.rot90(anArray,1), cmap='hot') #, interpolation='nearest'); 
    plt.show()

    return None

def getMaximumLocation(anArray):
    return np.unravel_index(np.argmax(anArray, axis=None), anArray.shape) # x,y coordinate of maximum


def makeMaxStrip( signal, background, adjacentStrip = None, signalOffset = 0, backgrounOffset = 0):

    assert len(signal.shape)==1  
    assert len(background.shape)==1
    assert len(signal) == len(background)

    if adjacentStrip is None: 
        y1LowLimit = 0; y1HighLimit = len(signal)-1;  
        y2LowLimit = 0; y2HighLimit = len(signal); 

    else: 
        firstNonZeroIndex = np.argmax(adjacentStrip)
        lastNonZeroIndex  = len(adjacentStrip)-1-np.argmax(np.flip(adjacentStrip,0))

        y1LowLimit = 0; y1HighLimit = lastNonZeroIndex;  
        y2LowLimit = firstNonZeroIndex; y2HighLimit = len(signal); 


    sig = 0. # save the final significance here
    if signalOffset > 0 : sig = significanceDef(signalOffset, backgrounOffset )

    interval = [0,0]

    for y1 in range(y1LowLimit, y1HighLimit): 
        for y2 in range(y1+1,   y2HighLimit): 
            if y2 < y2LowLimit: continue 
            tempSig = significanceDef(signal[ y1:y2 ].sum()+signalOffset, background[ y1:y2 ].sum()+backgrounOffset)
            if tempSig > sig:
                sig = tempSig
                interval = [y1,y2]

    mask = np.zeros(signal.shape)
    mask[ interval[0] : interval[1] ] = 1

    return mask

def withinM4lLimits(x,y, params):
    # lower limit parameters 
    s1 = params["slope1"]
    s2 = params["slope2"]

    x0 = params["xOffset"]
    y0 = params["yOffset"]

    # upper limit parameters
    yMax = params["yMax"]

    # construct yMin
    if  x <= x0: yMin = (float(x) - x0) * s1  + y0
    elif x > x0: yMin = (float(x) - x0) * s2  + y0


    if y > yMax or y < yMin : return False
    else:                     return True


def addStripToMask(signal, background, xStart,  mask, previousX = None):

    # check of adding a new slice to the mask yield bigger significance
    tempMask = mask.copy()

    if previousX is None: adjacentStrip = None
    else: adjacentStrip = mask[previousX,:]


    maskSlice = makeMaxStrip( signal[xStart,:] , background[xStart,:], adjacentStrip = adjacentStrip, signalOffset = 0, backgrounOffset = 0)
    tempMask[xStart] = maskSlice


    if calculateSignificance(signal, background, tempMask) < calculateSignificance(signal, background, mask): 
        maskImproved = False
    else: 
        mask[xStart] = maskSlice
        maskImproved = True

    return maskImproved



if __name__ == '__main__':

    myTFile = ROOT.TFile("m4lStudyOutZX.ROOT","OPEN")
    myTDir = myTFile.Get("m34VSm4l")

    histDict = {} # store my hists in here

    for path, myTObject  in postProcess.generateTDirPathAndContentsRecursive(myTDir, newOwnership = None):  histDict[myTObject.GetName()] = myTObject

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    signalTH2s = [ histDict[x] for x in histDict if x != "Background"]
    maskDict = {}
    maskDict1D = {}
    boundingBoxDict = {}
    optimizedBoxDict = {}

    for DSID in histDict:
        if DSID == 'Background': continue
        #if DSID != "343242": continue

        #histDict[DSID].Divide(histDict[DSID])
        #histDict[DSID].Draw("COLZ")

        signal = convertTH2toNumpyArray( histDict[DSID] )
        background = convertTH2toNumpyArray( histDict['Background'] )

        mask = np.zeros(signal.shape)

        # get x starting point, pick the point with the largest individual significance as such
        significanceArray = significanceDef(signal, background) 
        significanceArray[np.isnan(significanceArray)] = 0      
        xStart , _ = getMaximumLocation( signal )

        print(DSID + "  " + str(xStart))


        xPointLeft = xStart-1
        xPointRight = xStart+1
        addStripToMask(signal, background, xStart,  mask) # note that mask here is implicitly changed

        

        while xPointLeft is not None or xPointRight is not None:

            if xPointRight is not None:

                moreSignificance = addStripToMask(signal, background, xPointRight,  mask, previousX = xPointRight-1) # note that mask here is implicitly changed
                if moreSignificance: xPointRight = xPointRight+1
                else:                xPointRight = None

            if xPointLeft is not None:
                moreSignificance = addStripToMask(signal, background, xPointLeft,  mask, previousX = xPointLeft+1) # note that mask here is implicitly changed
                if moreSignificance: xPointLeft = xPointLeft-1
                else:                xPointLeft = None

        maskDict[DSID] = mask
        maskDict1D[DSID] = np.sign( mask.sum(axis=1) )

    
    aggregateMask = aggregateMasks( maskDict.values() )
    aggregateSignalTH2s = aggregateMasks( signalTH2s )
    
    #drawArray(aggregateMask)

    maskHist = aggregateSignalTH2s.Clone("test")
    fillTHWithNumpyArray(maskHist,aggregateMask)
    maskHist.Multiply(aggregateSignalTH2s)
    maskHist.Draw("COLZ")

    xNonZeroLocation = np.nonzero(aggregateMask.sum(axis=1))[0] #get the location of rows that are non zero by adding along them and seeing which are non-zero
    yvaluesDown = aggregateMask.argmax(axis=1)[xNonZeroLocation]
    yValuesUp = aggregateMask.shape[1]-np.flip(aggregateMask, axis=1).argmax(axis=1)[xNonZeroLocation]


    xNonZeroLocationTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( x , 1, aggregateSignalTH2s)[0] for x in xNonZeroLocation ])
    yValuesUpTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( 1 , y, aggregateSignalTH2s)[1] for y in yValuesUp ])
    yvaluesDownTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( 1 , y, aggregateSignalTH2s)[1] for y in yvaluesDown ])


    # plot lower limits and fit

    #subsetSelector = xNonZeroLocationTH2Coordinats <= 30    
    #plt.plot( xNonZeroLocationTH2Coordinats[subsetSelector], yvaluesDownTH2Coordinats[subsetSelector]  )
    #polyVars = np.polyfit( xNonZeroLocationTH2Coordinats[subsetSelector], yvaluesDownTH2Coordinats[subsetSelector] ,1 )
    #
    #plt.plot( xNonZeroLocationTH2Coordinats, np.polyval(polyVars, xNonZeroLocationTH2Coordinats )  ) 
    #
    #subsetSelector = xNonZeroLocationTH2Coordinats >= 30  
    #plt.plot( xNonZeroLocationTH2Coordinats[subsetSelector], yvaluesDownTH2Coordinats[subsetSelector]  )
    #polyVars = np.polyfit( xNonZeroLocationTH2Coordinats[subsetSelector], yvaluesDownTH2Coordinats[subsetSelector] ,1 )
    #plt.plot( xNonZeroLocationTH2Coordinats, np.polyval(polyVars, xNonZeroLocationTH2Coordinats )  ) 
    #
    #
    ## plot upper limits and fit # this looks ok
    #plt.plot( xNonZeroLocationTH2Coordinats, yValuesUpTH2Coordinats  )
    #polyVarsDown = np.polyfit( xNonZeroLocationTH2Coordinats, yValuesUpTH2Coordinats ,0 )
    #
    #plt.plot( xNonZeroLocationTH2Coordinats, np.polyval(polyVarsDown, xNonZeroLocationTH2Coordinats )  ) 

    #plt.show()

    
    params = {"slope1"  : - 4.5/15. ,"slope2"  : 4./25 ,"xOffset" : 30. ,"yOffset" : 115. , "yMax" : 130.}

    #withinM4lLimits(30., 120. , params)
    

    histOut = makeM4lTH2MaskFromFunction( lambda x,y : withinM4lLimits(x,y, params) , aggregateSignalTH2s )
    histOut.Multiply(aggregateSignalTH2s)
    histOut.Draw("COLZ")

    m34Spectrum = histOut.ProjectionX()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    #do the m34 intervals overlap? (They shouldn't)
    m34IntervalIndicators = maskDict.values()[0].sum(axis=1)
    m34IntervalIndicators *= 0
    for anyArray in maskDict.values(): m34IntervalIndicators += np.sign( anyArray.sum(axis=1) )
    assert all(m34IntervalIndicators <= 1) # if m34 intervals don't overlap, all elements should be 0 or 1 


    maskDict1D[DSID]
    tmpTH1 = maskHist.ProjectionX()

    fillTHWithNumpyArray(tmpTH1,m34IntervalIndicators)
    tmpTH1.Draw()

    m34Spectrum.Multiply(tmpTH1)
    m34Spectrum.Draw()



    # remember that we can project the TH2 along X      


        #histDict[DSID].Draw("COLZ")
        #drawArray(significanceArray)


#        mask = getMaxSignificanceMask(signal,background) # assuming signal
#        maskDict[DSID] = mask
#
#        boundingMask = drawRectangularBoundingBox(mask) 
#        boundingBoxDict[DSID] = boundingMask
#
#
#        boundingBoxParams = np.array( getBoundingBoxParameters(mask) )
#
#        xMax, yMax = mask.shape
#
#        xLow, xHigh, yLow, yHigh = getBoundingBoxParameters(mask)
#
#        xMiddle = (xLow+xHigh)/2
#        yMiddle = (yLow+yHigh)/2
#
#        xLowSlice  = slice(0      , xMiddle, 1 )
#        xHighSlice = slice(xMiddle, xHigh  , 1 )
#        yLowSlice  = slice(0      , yMiddle, 1 )
#        yHighSlice = slice(yMiddle, yMax   , 1 )
#
#        #xLowSlice  = slice(xMiddle-3      , xMiddle-1, 1 )
#        #xHighSlice = slice(xMiddle+1, xMiddle+2  , 1 )
#        #yLowSlice  = slice(yMiddle-2 , yMiddle-1, 1 )
#        #yHighSlice = slice(yMiddle+2, yMiddle+4   , 1 )
#
#        sliceSet = (xLowSlice, xHighSlice, yLowSlice, yHighSlice)
#
#        #getSignificanceFromBox(boundingBoxParams, signal, background)
#
#        curretnSignificance = lambda x: -getSignificanceFromBox(x, signal, background)
#
#        optimalParameter = brute(curretnSignificance, sliceSet )
#
#
#
#        optimizationMask = getRectangle( boundingMask , optimalParameter[0], optimalParameter[1], optimalParameter[2], optimalParameter[3] )
#
#        optimizedBoxDict[DSID] = optimizationMask


        






    aggregateMask = aggregateMasks( optimizedBoxDict.values() )








    ## plot the numpy array
    #plt.imshow(aggregateMask, cmap='hot') #, interpolation='nearest'); 
    #plt.show()


    ## AA = [ histDict[x] for x in histDict if x != "Background"]
    ## allSignals = AA[0].Clone("allSignals")
    ## for x in AA[1:]: allSignals.Add(x)
    ## allSignals.SetTitle("All ZZd signal samples")
    ## allSignals.Draw("COLZ")
    ##
    ## significanceHist = allSignals.Clone("significance")
    ## significanceHist.Multiply(allSignals)
    ## significanceHist.Divide(histDict['Background'])
    ##
    ##






    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here