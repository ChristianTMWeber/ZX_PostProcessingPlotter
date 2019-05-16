import ROOT
import numpy as np
import plotPostProcess as postProcess
import matplotlib.pyplot as plt # to plot the np.array
from scipy.optimize import brute  # for the fittin'
import re


def convertTHtoNumpyArray(hist ): # plot comes out rotated, fix eventually

    if isinstance(hist,ROOT.TH2):
        x_bins = hist.GetNbinsX()
        y_bins = hist.GetNbinsY()
        
        bins = np.zeros((x_bins,y_bins))

        for y_bin in xrange(y_bins): 
            for x_bin in xrange(x_bins): 
                bins[x_bin,y_bin] = hist.GetBinContent(x_bin + 1,y_bin + 1)

        return bins

    elif    isinstance(hist,ROOT.TH1):
        x_bins = hist.GetNbinsX()
         
        bins = np.zeros((x_bins))
        for x_bin in xrange(x_bins): 
            bins[x_bin] = hist.GetBinContent(x_bin + 1)
        
        return bins

    else: return None



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

    if isinstance(maskList, dict): maskList = maskList.values()

    if isinstance(maskList[0],np.ndarray): 

        aggregateMask = maskList[0].copy()
        for aMask in maskList[1:]: aggregateMask = aggregateMask + aMask

    elif isinstance(maskList[0],ROOT.TH1):

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

    significance = significanceDef(signalCount, backgroundCount)

    return significance

def significanceDef(signal, background):
    significance = signal / np.sqrt(background)

    if isinstance(significance,np.ndarray):
        significance[ np.abs(significance) == np.inf] = 0
        np.nan_to_num(significance, copy=False)

    return significance


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

        firstNonZeroIndex = 0
        lastNonZeroIndex  = len(signal)-1

    else: 
        # we want strips that are connected, enforce that there
        if adjacentStrip.sum() == 0 : return np.zeros(signal.shape) 

        firstNonZeroIndex = np.argmax(adjacentStrip)
        lastNonZeroIndex  = len(adjacentStrip)-1-np.argmax(np.flip(adjacentStrip,0))

        y1LowLimit = 0; y1HighLimit = lastNonZeroIndex;  
        y2LowLimit = firstNonZeroIndex; y2HighLimit = len(signal); 


    sig = 0. # save the final significance here
    if signalOffset > 0 : sig = significanceDef(signalOffset, backgrounOffset )

    interval = [0,0]
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    for windowSize in range(1,len(signal) + 1 ): 
        for xStart in range(0,len(signal) ): 

            if xStart+ windowSize > len(signal): continue # dont go outside the array limits
            if xStart+ windowSize < firstNonZeroIndex: continue # either the upper part of the strip needs to be connected
            if xStart > lastNonZeroIndex and xStart+ windowSize < xStart+ windowSize: continue # or the lower part

            y1 = xStart
            y2 = xStart+ windowSize
            #signal[ xStart : xStart+ windowSize ]

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

def constructOptimalSignificanceMask(signal, background):

    mask = np.zeros(signal.shape)

    xStart , _ = getMaximumLocation( signal )


    xPointLeft = xStart-1
    xPointRight = xStart+1
    addStripToMask(signal, background, xStart,  mask) # note that mask here is implicitly changed

    continueLeft = True
    continueRight = True
    
    while continueLeft or continueRight:
    #xPointLeft >= 0 and xPointRight <= signal.shape[0]:

        #print(xPointLeft, xPointRight)

        if continueRight:
            moreSignificance = addStripToMask(signal, background, xPointRight,  mask, previousX = xPointRight-1) # note that mask here is implicitly changed
            if moreSignificance: xPointRight = xPointRight+1
            else:                continueRight = False

        if continueLeft:
            moreSignificance = addStripToMask(signal, background, xPointLeft,  mask, previousX = xPointLeft+1) # note that mask here is implicitly changed
            if moreSignificance: xPointLeft = xPointLeft-1
            else:                continueLeft = False

        if xPointRight >= signal.shape[0]: continueRight = False
        if xPointLeft < 0 :                continueLeft = False

    return mask



def makeSignificanceTH1Ds(signalsAndBackground, masksTH1, maskTH2, newTH1Name = "massPointSignificance"):

    backgroundTH2 = histDict['Background'].Clone("localBackground")

    significaneTH1s  = {}
    significaneFloats = {}

    # let's make a TH1 that carries the significanceFloat vs Zd mass
    # let's make a list of the Zd mass points

    getMassPointFromDSID = lambda x : int(re.search( "\d\d", myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ]  ).group() )

    ZdMassPoints = [ getMassPointFromDSID(DSID) for DSID in histDict.keys() if DSID != 'Background']

    massPointSignificanceTH1 = ROOT.TH1D(newTH1Name,newTH1Name, max(ZdMassPoints) - min(ZdMassPoints) +2, min(ZdMassPoints) -1, max(ZdMassPoints) +1)
    massPointSignificanceTH1.SetStats( False) # remove stats box
    #massPointSignificanceTH1.GetXaxis().SetRange( min(ZdMassPoints)-1 , max(ZdMassPoints) - min(ZdMassPoints) )


    histDictKeys =  histDict.keys(); histDictKeys.sort()

    for DSID in histDictKeys:
        if DSID == 'Background': continue

        signalTH2 = histDict[DSID].Clone("tempSignal")

        # apply the TH2 mask
        backgroundTH2.Multiply(maskTH2)
        signalTH2.Multiply(maskTH2)

        backgroundTH1 = backgroundTH2.ProjectionX()
        signalTH1 = signalTH2.ProjectionX()



        backgroundTH1.Multiply(masksTH1[DSID])
        signalTH1.Multiply(masksTH1[DSID])

        significanceArray = significanceDef( convertTHtoNumpyArray(signalTH1 ) , convertTHtoNumpyArray(backgroundTH1 ))
        significaneTH1 = signalTH1.Clone("signifiacance " + DSID);     fillTHWithNumpyArray(significaneTH1,significanceArray)

        significanceFloat = significanceDef( signalTH1.Integral() , backgroundTH1.Integral() )

        significaneTH1s[DSID] = significaneTH1
        significaneFloats[DSID] = significanceFloat

        binNr = massPointSignificanceTH1.GetXaxis().FindBin(getMassPointFromDSID(DSID))
        massPointSignificanceTH1.SetBinContent( binNr , significanceFloat)

        #print( significanceFloat, signalTH1.Integral() , backgroundTH1.Integral(), myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ])
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return significaneTH1s, significaneFloats, massPointSignificanceTH1



if __name__ == '__main__':
    # I am referring in this code often to 'masks'
    # These are arrays, TH1s or TH2s that are only filled with 1 and 0 and they serve to select subsets from other arrays etc
    # the idea here is that I can do the selection by doing an element wise multiplication betwen the mask and the array etc of interest

    myDSIDHelper = postProcess.DSIDHelper() # setup DSID helper for, among other thigns IDing the DSIDs when opportune
    #myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ] 

    myTFile = ROOT.TFile("m4lStudyOutZX.ROOT","OPEN") # this is the .root file that we want
    myTDir = myTFile.Get("m34VSm4l")    # and this the the TDir that our hists are in, and as of now it should only be containings hists.

    histDict = {} # store my hists in here
    # Grab and save all the hists in our TDir
    for path, myTObject  in postProcess.generateTDirPathAndContentsRecursive(myTDir, newOwnership = None):  histDict[myTObject.GetName()] = myTObject

    # let's set up a bunch of dicts to store tings
    signalTH2s = [ histDict[x] for x in histDict if x != "Background"]
    maskDict = {} ;    maskDict1D = {};     maskDictTH1D = {};


    # Loop over all the (Signal) histogrms
    histDictKeys =  histDict.keys(); histDictKeys.sort()

    for DSID in histDictKeys:
        if DSID == 'Background': continue
        #if DSID != "343242": continue

        #histDict[DSID].Divide(histDict[DSID])
        #histDict[DSID].Draw("COLZ")

        signal = convertTHtoNumpyArray( histDict[DSID] )
        background = convertTHtoNumpyArray( histDict['Background'] )

        mask = constructOptimalSignificanceMask(signal, background)


        maskDict[DSID] = mask
        maskDict1D[DSID] = np.sign( mask.sum(axis=1) ) # these 1d mask will eventaully define the m34 region of interest for the given DSID

        maskTH1D = histDict[DSID].ProjectionX(); 
        fillTHWithNumpyArray(maskTH1D,maskDict1D[DSID])

        maskDictTH1D[DSID] = maskTH1D

    
    # Let's create a canvas that I can use to plot some 'overview' plots

    canvasOutFile = ROOT.TFile("CanvasOut.root", "RECREATE")

    overviewCanvas = ROOT.TCanvas("significance","significance",1920/2,1080/2);
    overviewCanvas.Divide(2,3)

    overviewCanvas.cd(1)
    histDict["Background"].Draw("COLZ")

    overviewCanvas.cd(2)

    aggregateSignalTH2s = aggregateMasks( signalTH2s )
    aggregateSignalTH2s.Draw("COLZ")

    overviewCanvas.cd(3)
    aggregateMask = aggregateMasks( maskDict.values() )

    aggregateMaskTH2 = aggregateSignalTH2s.Clone("aggregateMask")
    fillTHWithNumpyArray(aggregateMaskTH2,aggregateMask)

    signalTimesMask = aggregateMaskTH2.Clone("SignalTimesMask")


    signalTimesMask.Multiply(aggregateSignalTH2s)
    signalTimesMask.Draw("COLZ")


    overviewCanvas.cd(4)

    params = {"slope1"  : - 4.5/15. ,"slope2"  : 4./25 * 1.1 ,"xOffset" : 30. ,"yOffset" : 116. , "yMax" : 130.}

    m4lParameterMask = makeM4lTH2MaskFromFunction( lambda x,y : withinM4lLimits(x,y, params) , aggregateSignalTH2s )
    signalTimesParameterMaskTH2 = m4lParameterMask.Clone("signalTimesParameterMask")
    signalTimesParameterMaskTH2.Multiply(aggregateSignalTH2s)
    signalTimesParameterMaskTH2.Draw("COLZ")


    overviewCanvas.cd(5)


    # default mask, doesn't further limit the m4l selection
    
    defaultM4lSelectionTH1 = aggregateSignalTH2s.Clone("defaultM4lSelection") ; fillTHWithNumpyArray(defaultM4lSelectionTH1,np.ones( aggregateMask.shape ))
    

    significaneTH1sRef, significaneFloatsRef, massPointSignificanceTH1Ref = makeSignificanceTH1Ds(histDict, maskDictTH1D, defaultM4lSelectionTH1, newTH1Name = "massPointSignificanceRef")
    significaneTH1sMax, significaneFloatsMax, massPointSignificanceTH1Max = makeSignificanceTH1Ds(histDict, maskDictTH1D, aggregateMaskTH2, newTH1Name = "massPointSignificanceMax")


    significaneTH1s, significaneFloats, massPointSignificanceTH1 = makeSignificanceTH1Ds(histDict, maskDictTH1D, m4lParameterMask)


    massPointSignificanceTH1Ref.SetLineColor(1)
    massPointSignificanceTH1Max.SetLineColor(2)
    massPointSignificanceTH1.SetLineColor(3)

    massPointSignificanceTH1Ref.SetLineStyle(1)
    massPointSignificanceTH1Max.SetLineStyle(2)
    massPointSignificanceTH1.SetLineStyle(3)

    massPointSignificanceTH1Ref.SetLineWidth(2)
    massPointSignificanceTH1Max.SetLineWidth(2)
    massPointSignificanceTH1.SetLineWidth(2)



    massPointSignificanceTH1Max.Draw()
    massPointSignificanceTH1Ref.Draw("SAME")
    massPointSignificanceTH1.Draw("SAME")

    legend = ROOT.TLegend(0.1,0.6,0.5,0.9)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetLineColor(ROOT.kWhite)
    legend.SetNColumns(1);
    legend.SetFillStyle(0);  # make legend background transparent
    legend.SetBorderSize(0); # and remove its border without a border

    legend.AddEntry(massPointSignificanceTH1Ref , "Reference" , "l");
    legend.AddEntry(massPointSignificanceTH1Max , "Max" , "l");
    linearLegendEntry = "Linear: x0=%2.0f, y0=%3.0f, s1=%1.1f, s2=%1.1f, yMax=%3.0f" %(params["xOffset"], params["yOffset"],  params["slope1"], params["slope2"], params["yMax"] )
    legend.AddEntry(massPointSignificanceTH1 , linearLegendEntry , "l");
    legend.Draw()


    # convertTHtoNumpyArray(massPointSignificanceTH1Ref)
    # convertTHtoNumpyArray(massPointSignificanceTH1Max)
    # convertTHtoNumpyArray(massPointSignificanceTH1)

    significaneTH1sAggregateRefs = aggregateMasks( significaneTH1sRef )
    significaneTH1sAggregate = aggregateMasks( significaneTH1s )


    #myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ] 

    overviewCanvas.Update()



    
    #aggregateMasks( significaneTH1s.values() )

    overviewCanvas.Write()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    canvasOutFile.Close()


    aggregateMask = aggregateMasks( maskDict.values() )
    aggregateSignalTH2s = aggregateMasks( signalTH2s )
    
    #drawArray(aggregateMask)

    maskHist = aggregateSignalTH2s.Clone("test")
    fillTHWithNumpyArray(maskHist,aggregateMask)
    maskHist.Multiply(aggregateSignalTH2s)
    maskHist.Draw("COLZ")



    # this here serves to make some plots of the masks

    #xNonZeroLocation = np.nonzero(aggregateMask.sum(axis=1))[0] #get the location of rows that are non zero by adding along them and seeing which are non-zero
    #yvaluesDown = aggregateMask.argmax(axis=1)[xNonZeroLocation]
    #yValuesUp = aggregateMask.shape[1]-np.flip(aggregateMask, axis=1).argmax(axis=1)[xNonZeroLocation]


    #xNonZeroLocationTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( x , 1, aggregateSignalTH2s)[0] for x in xNonZeroLocation ])
    #yValuesUpTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( 1 , y, aggregateSignalTH2s)[1] for y in yValuesUp ])
    #yvaluesDownTH2Coordinats = np.array([ getXYFromNumpyArrayIndex( 1 , y, aggregateSignalTH2s)[1] for y in yvaluesDown ])


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

    # these parameters define the m34 depenend m4l cut


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