import ROOT # to do all the ROOT stuff
#import numpy as np # good ol' numpy
import warnings # to warn about things that might not have gone right
import itertools # to cycle over lists in a nice automated way
import re # to do regular expression matching
import copy # for making deep copies
import argparse # to parse command line options
#import functions.RootTools as RootTools# root tool that I have taken from a program by Turra
import os
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

import plotPostProcess as postProcess
from functions.histTools import getSmallestInterval # my own tools for ROOT histograms 
import math # for simple math
import time # for measuring execution time


def defineTargetHistograms(lowerLimitList, upperLimitList, templateHist = ROOT.TH1D( "templateHist", "TemplateHist", 150,0,150) ):
    # for each set of lowerLimit, upperLimit pairs we want to have a well defined histogram to plot the m34 distribution in
 
    th1dDict = {} # store my ROOT.TH1D s here as { (m4lLowLimit, m4lUpperLimit) : RDF.Histo1D, ... }

    for m4lAbove in lowerLimitList:
        for m4lBelow in upperLimitList:

            newName = "%i GeV < m4l < %i GeV" %(m4lAbove,m4lBelow)

            newHist = templateHist.Clone(newName)
            newHist.SetTitle(newName)

            th1dDict[ (m4lAbove,m4lBelow)] = newHist

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return th1dDict


def defineSetOfM4lFilteredHists( RDF, lowerLimitList, upperLimitList, myTH1DModel = None , weightVariable = None, targetVariable = "m34", makeComplimentaryHists = False):
    # RDF is expected to be a OOT.RDataFrame
    # lowerLimitList and upperLimitList  don't really need to be lists, just iterables
    # makeComplimentaryHists - if true, we will figure out the widest of all the possible limits on m4l, 
    #                          and then for any pair of limits in (m4lBelow, m4lAbove), we will fill another histogram 
    #                          with the events that do not make it into the current set of limits, but would make it into the one with the widest set of possible limits

    # subfunction to help me deal with the different cases of myTH1DModel and weightVariable being provided or not
    def returnFilteredHist( myRDataFrame, targetVariable , myTH1DModel = None , weightVariable = None ):

        if    myTH1DModel is not None and weightVariable is not None : RDFResultHisto=myRDataFrame.Histo1D(myTH1DModel, targetVariable, weightVariable)
        elif  myTH1DModel is not None and weightVariable is     None : RDFResultHisto=myRDataFrame.Histo1D(myTH1DModel, targetVariable)
        elif  myTH1DModel is     None and weightVariable is not None : RDFResultHisto=myRDataFrame.Histo1D(targetVariable, weightVariable)
        else:                                                          RDFResultHisto=myRDataFrame.Histo1D(targetVariable)

        return RDFResultHisto



    histoDict = {} # store my RDF.Histo1D s here as { (m4lLowLimit, m4lUpperLimit) : RDF.Histo1D, ... }
    histoDictComplimenatry = {}


    for m4lAbove in lowerLimitList:
        for m4lBelow in upperLimitList:

            m4lLowLimit  = "m4l > %i" %m4lAbove
            m4lUpperLimit= "m4l < %i" %m4lBelow

            filteredRDF = RDF.Filter( m4lLowLimit ).Filter( m4lUpperLimit )

            RDFResultHisto = returnFilteredHist( filteredRDF ,targetVariable , myTH1DModel = myTH1DModel , weightVariable = weightVariable )

            histoDict[ (m4lAbove,m4lBelow)] = RDFResultHisto

            if makeComplimentaryHists:
                # we want events whose m4l is either of two non-overlapping intervals: m4l \in (A,B) or m4l \in (C,D), with A<B<C<D, let's define those
                #                                A                  B           C                       D
                leftAndRightIntervals  = (min(lowerLimitList), m4lAbove, m4lBelow      , max(upperLimitList) )
                cutString = "( m4l > %i && m4l < %i ) || ( m4l > %i && m4l < %i )" %( leftAndRightIntervals )

                filteredRDFComplimentary = RDF.Filter( cutString )

                histoDictComplimenatry[ (m4lAbove,m4lBelow) ]  = returnFilteredHist( filteredRDFComplimentary ,targetVariable , myTH1DModel = myTH1DModel , weightVariable = weightVariable )
                



    
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return histoDict, histoDictComplimenatry

def addToTargetHists(targetHistDict, sourceHistDict, scale = 1.):

    for key in sourceHistDict:  

        # I am getting an error when properly checking for the type ROOT.ROOT.RDF.RResultPtr<ROOT.TH1D>, so let's do this instead for now
        if not isinstance(sourceHistDict[key], ROOT.TH1): sourceHist = sourceHistDict[key].GetPtr() # GetPtr() of an ROOT.ROOT.RDF.RResultPtr<ROOT.TH1D>, should give me the TH1D
        else:                                             sourceHist = sourceHistDict[key]

        targetHistDict[key].Add( sourceHist , scale)
        #From the documentation: IMPORTANT NOTE: If you intend to use the errors of this histogram later you should call Sumw2 before making this operation. This is particularly important if you fit the histogram after TH1::Add

    return None

def getTH2BinContentByXYValue( aTH2, xVal, yVal):
    # because TH2.GetBinContent() expects bin numbers

    xBin = aTH2.GetXaxis().FindBin(xVal)
    yBin = aTH2.GetYaxis().FindBin(yVal)

    return aTH2.GetBinContent(xBin,yBin)

def fillTH2WithTargetHists( TH2Hist, histDict, ):

    for m4lLowLimit, m4lUpperLimit in histDict:
        currentTH1 = histDict[(m4lLowLimit, m4lUpperLimit)]
        #print(currentTH1.Integral())
        if isinstance(currentTH1, ROOT.TH1) : TH2Hist.Fill(m4lLowLimit,m4lUpperLimit, currentTH1.Integral() )
        if isinstance(currentTH1, float) :    TH2Hist.Fill(m4lLowLimit,m4lUpperLimit, currentTH1 )

    #import pdb; pdb.set_trace() # import

    #canvas = ROOT.TCanvas()
    ##TH2Hist.Draw("COLZ"); canvas.Update()
    #backgroundTH2.Draw("COLZ TEXT"); canvas.Update() #https://root.cern/doc/master/classTHistPainter.html#HP01c


    return None

def getBinNr( aHist, xValue) : # for a given ROOT.TH1 and xValue, get the relevant bin nr
    return aHist.GetXaxis().FindBin(xValue)

def getHistXRange(hist): # for a given TH1, get the range on the x-Axis
    nBins = hist.GetNbinsX()
    return hist.GetBinLowEdge(1), hist.GetBinLowEdge(nBins) + hist.GetBinWidth(nBins)


def doArithmeticOnQualifiedHistIntegrals(hist1, hist2, arithmetic = None , desiredWidth = 0.99 , integralInterval = None):
    # pass a function that takes two floats and returns one as 'arithmetic' parameters,
    # the two inputs weil will be the ratio of the integrals from histDict1[ givenKey ] and histDict2[ givenKey ] 
    # where the integral boulds are given by the smallest integral in histDict1[ givenKey ] that subtents 95% of the events in there
    # for example if want want to take the ratio choose
    if arithmetic is None: arithmetic = lambda A, B : A/B

    if integralInterval is None:
        xLow, xHigh = getSmallestInterval( hist1, desiredWidth = desiredWidth ) # get the smallest intervall that subtends a fraction 'desiredWidth' of all events
    else:  xLow, xHigh = integralInterval

    # let's practice lambda functions, and define one that gives me, for a given histogram 'aHist' and an 'xValue', the bin number for the hist of interest
    # the syntax is the following: 
    #  <name of the function>  =   lambda(as sign for python that we get an inline function here)   <parameters of the function>  :   <definition of the function?
    #getBinNr = lambda aHist, xValue : aHist.GetXaxis().FindBin(xValue)

    integral1 = hist1.Integral( getBinNr(hist1, xLow),getBinNr(hist1, xHigh) )
    integral2 = hist2.Integral( getBinNr(hist2, xLow),getBinNr(hist2, xHigh) )

    return arithmetic(integral1,integral2)




def writeTH2AndGetCanvas( TH2 ):

    TH2.Write()

    tmpCanvas = ROOT.TCanvas( TH2.GetName() , TH2.GetTitle() ,1300/2,1300/2)
    TH2.SetMarkerSize(0.9)
    TH2.Draw("COLZ TEXT45"); #https://root.cern/doc/master/classTHistPainter.html#HP01
    tmpCanvas.Update()

    return tmpCanvas


def makeResultsTH2( signalHistDict , backgroundHistDict, titleString, signalBackgroundComparisonOperation ):

    currentSignalTH2 = myTH2Template.Clone( titleString )
    currentSignalTH2.SetTitle(titleString)

    for m4lLowLimit, m4lUpperLimit in signalHistDict:

        signalHist = signalHistDict[(m4lLowLimit, m4lUpperLimit)]
        backgroundHist = backgroundHistDict[(m4lLowLimit, m4lUpperLimit)]

        aNumber = signalBackgroundComparisonOperation(signalHist , backgroundHist) 

        currentSignalTH2.Fill(m4lLowLimit, m4lUpperLimit, aNumber )

    return currentSignalTH2


def calculateDeltaSigError( signalHistDict , backgroundHistDict, signalErrorHistDict , backgroundErrorHistDict, titleString, integralInterval ):

    def getIntegralNotBasedOnBin(hist, lowLimit, highLimit):

        lowBin  =  hist.GetXaxis().FindBin(lowLimit)
        highBin =  hist.GetXaxis().FindBin(highLimit)

        integralUncertainty = ROOT.Double()

        integral = hist.IntegralAndError( lowBin , highBin, integralUncertainty)
        return integral, integralUncertainty



    currentSignalTH2 = myTH2Template.Clone( titleString )
    currentSignalTH2.SetTitle(titleString)

    for m4lLowLimit, m4lUpperLimit in signalHistDict:

        signalHist = signalHistDict[(m4lLowLimit, m4lUpperLimit)]
        backgroundHist = backgroundHistDict[(m4lLowLimit, m4lUpperLimit)]

        signalErrorHist = signalErrorHistDict[(m4lLowLimit, m4lUpperLimit)]
        backgroundErrorHist = backgroundErrorHistDict[(m4lLowLimit, m4lUpperLimit)]

        xLow, xHigh = integralInterval(signalHist)


        signalIntegral, _     = getIntegralNotBasedOnBin(signalHist,          xLow, xHigh)
        backgroundIntegral, _ = getIntegralNotBasedOnBin(backgroundHist,      xLow, xHigh)
        _, signalError        = getIntegralNotBasedOnBin(signalErrorHist,     xLow, xHigh)
        _, backgroundError    = getIntegralNotBasedOnBin(backgroundErrorHist, xLow, xHigh)

        # 
        #errorSquared = lambda s,b, sError, bError : (-s / (2*(b+s)**(1.5)) + 1/( (b+s)**(0.5) ))**2 * sError**2 + ( s**2 / (4 * ((b+s)**3) )) * bError**2
        errorSquared = lambda s,b, sError, bError : ( 1./b) * sError**2 + (s**2/(4*b**3)) * bError**2

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        error = errorSquared(signalIntegral, backgroundIntegral, signalError, backgroundError)**0.5


        #aNumber = signalBackgroundComparisonOperation(signalHist , backgroundHist, integralInterval = getSmallestInterval( integralHist , desiredWidth = 0.99) )

        currentSignalTH2.Fill(m4lLowLimit, m4lUpperLimit, error )

        


    return currentSignalTH2



if __name__ == '__main__':



    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("-r", "--resume", type=bool, default=False, help="Instead of processing TTree from current input file, \
                        treat it is output from previous run of this programm, \
                        and load the different TH1s from there that we would otherwise populate from the TTree")

    parser.add_argument("-c", "--mcCampaign", nargs='*', type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], required=True,
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="metadata/md_bkg_datasets_mc16e_All.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument("-a", "--analysisType", type=str, choices=["ZX","ZdZd"], default="ZX" ,
        help="Selects the analysis that we follow. This especially changes what our target kinematic variable is\
        (m34 for ZX and (m12+m34)/2 for ZdZd), as well as a few other minor changes (plot titles, etc.)" )

    parser.add_argument("--skipZJets", type=bool, default=True , help="If true, we will skip the Z+Jet mc samples, which we know to be problematic" )

    args = parser.parse_args()

    analysisType = args.analysisType 

    if analysisType == "ZX":
        targetVar = "m34"
        integralRangeFunction = lambda hist1: getSmallestInterval( hist1, desiredWidth = 0.99 ) # get the smallest intervall that subtends a fraction 'desiredWidth' of all events
    elif analysisType == "ZdZd":
        targetVar = "mll_avg"
        integralRangeFunction = lambda hist1: getHistXRange(hist1) # for ZdZd we want to integrate over the whole mll_avg range

    doDeltaSigError = True

    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    assert 1 ==  len(args.mcCampaign), "We do not have exactly one mc-campaign tag per input file"
    #assert len(args.input) ==  len(args.mcCampaign)

    assert all( x==1   for x in collections.Counter( args.mcCampaign ).values() ), "\
    Some mc-campaign tags have been declared more than once. \
    For now we are only setup to support one file per MC-tag. Until we changed that, 'hadd' them in bash"

    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = postProcess.DSIDHelper()
    myDSIDHelper.importMetaData(args.metaData , mcTag = args.mcCampaign[0]) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.fillSumOfEventWeightsDict(args.input)

    ######################################################
    # Prepare some datastructes and run parameters
    ######################################################

    # set of m4l ranges we want to consider for our study
    m4lRangeLow = range(115,125,1); m4lRangeHigh = range(125,131,1) # use only ints for now!
    dX = float(m4lRangeLow[1] - m4lRangeLow[0])
    dY = float(m4lRangeHigh[1] - m4lRangeHigh[0])
    
    # define a hist which will define the the binning and a few other things for all histograms to follow
    targetHistTemplate = ROOT.TH1D( "templateHist", "templateHist", 150,0,150)
    targetHistTemplate.GetXaxis().SetTitle(targetVar+" [GeV]")


    # target hists: a dict of TH1Ds mapping the tuple (m4lLow, m4lHigh) -> TH1D for that tuple, for each pair of (m4lLow, m4lHigh) that we consider 
    targetHistsBackground = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    dictOfSignalTargetHists = collections.defaultdict(dict) # will contain a mappint of DSID -> targetHistsSignal for all signal DSIDs 

    # complimentary hists contain the m34 distribution of events for which  min(m4lRangeLow) < m4l < m4lLow or m4lHigh < m4l < max(m4lRangeHigh)
    # we will use them in the calculation of some errors eventually
    complimentaryHistsBackground = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    dictOfSignalComplementaryHists = collections.defaultdict(dict) # will contain a mappint of DSID -> targetHistsSignal for all signal DSIDs

    # define this as a model for the RDataFrome histograms
    myTH1DModel = ROOT.RDF.TH1DModel(targetHistTemplate)

    myTH2Template = ROOT.TH2D( "templateHist2D", "templateHist2D", len(m4lRangeLow), min(m4lRangeLow)-dX/2, max(m4lRangeLow)+dX/2, len(m4lRangeHigh) , min(m4lRangeHigh)-dY/2, max(m4lRangeHigh)+dY/2  )
    myTH2Template.GetXaxis().SetTitle("lower limit on m4l")
    myTH2Template.GetYaxis().SetTitle("upper limit on m4l")
    myTH2Template.SetStats( False) # remove stats box

    ######################################################
    # Do TTree selection an filtering via RDataFrame
    ######################################################

    postProcessedData = ROOT.TFile(args.input, "READ"); # open the file with the data from the ZdZdPostProcessing, that contains the relevant TTrees

    #ROOT.ROOT.EnableImplicitMT()
    startTime = time.time()
    # loop over all of the TObjects in the given ROOT file
    for path, myTObject  in postProcess.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!


        if args.resume:

            if not isinstance(myTObject, ROOT.TH1): continue
            if isinstance(myTObject, ROOT.TH2): continue


            #                        find a digit and then at lest one more
            m4lLimitsStrList = re.findall("\d\d+", myTObject.GetName() ) #output should be a list of two strings, each one convertible to an int
            assert len(m4lLimitsStrList) == 2 # need a lower and an upper limit
            m4lLimits = tuple( [int(x) for x in m4lLimitsStrList] )

            if "Background" in path: hasBackground = True
            else:                    hasBackground = False; DSID = postProcess.idDSID(path)

            if "Complimentary" in path: isComplimentary = True
            else :                      isComplimentary = False


            if     hasBackground and not isComplimentary:            targetHistsBackground[m4lLimits] = myTObject
            elif   hasBackground and isComplimentary:     complimentaryHistsBackground[m4lLimits] = myTObject
            # if it is not background, it is signal
            elif not hasBackground and not isComplimentary:        dictOfSignalTargetHists[DSID][m4lLimits] = myTObject
            elif not hasBackground and isComplimentary:     dictOfSignalComplementaryHists[DSID][m4lLimits] = myTObject

        else: # args.resume == False, i.e. fill new from TTree

            if postProcess.irrelevantTObject(path, myTObject, requiredRootType=ROOT.TTree): continue # skip non-relevant histograms
            
            DSID = postProcess.idDSID(path) # get the DSID to decide whether the given histogram is signal or background eventually
            
            if args.skipZJets and  "Z+Jets" in myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ] : print( "skipping DSID " + DSID + " " + myDSIDHelper.physicsSubProcessByDSID[ int(DSID) ]); continue

            # path happen to include also the rootfile name, e.g. 'testDir.root/345060/Nominal/t_ZXTree'
            # we need to remove that part of the string, so select everything after the first "/"
            tDirPath = re.search( "(?<=/).+", path ).group()
            

            myDataFrame = ROOT.RDataFrame(tDirPath,args.input) # setup the RDataFrame that we will use to parse the TTree

            RDFrameVariables = myDataFrame.Define("m34","llll_m34 / 1000").Define("m4l","llll_m4l / 1000")  # define our variables
            if analysisType == "ZdZd" : RDFrameVariables=RDFrameVariables.Define("mll_avg","(llll_m12 + llll_m34 ) / 2000")

            # we want to have multiple m4l filtered histograms. Let's define them here
            RDFHistDict, RDFHistDictComplimentary  = defineSetOfM4lFilteredHists( RDFrameVariables, m4lRangeLow, m4lRangeHigh , myTH1DModel = myTH1DModel,  weightVariable = 'weight', targetVariable = targetVar, makeComplimentaryHists = doDeltaSigError)


            if myDSIDHelper.isSignalSample( int(DSID) ):
                
                if DSID not in dictOfSignalTargetHists:  # if the current sample is a signal one, make sure we have it in our dictOfSignalTargetHists 
                    dictOfSignalTargetHists[DSID] = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
                    dictOfSignalComplementaryHists[DSID] = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)

                currentTarget = dictOfSignalTargetHists[DSID]
                currentComplementaryTarget = dictOfSignalComplementaryHists[DSID]

            else :
                currentTarget = targetHistsBackground
                currentComplementaryTarget = complimentaryHistsBackground 

            addToTargetHists(currentTarget             , RDFHistDict             , scale = myDSIDHelper.getMCScale(DSID) )
            addToTargetHists(currentComplementaryTarget, RDFHistDictComplimentary, scale = myDSIDHelper.getMCScale(DSID) )

            print path + "\t Memory usage: %s kB \t Runtime: %10.1f s" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8, (time.time() - startTime ) )


        # targetHistsBackground.values()[0].Integral()
        # RDFHistDict.values()[0].Integral() # call this to force evalution of the lazy RDataFrame functions
        # RDFHistDict.values()[0].Draw()

        #import pdb; pdb.set_trace() # import the debugger and




    ## now we should have all the data from the TTree




    ######################################################
    # Create TH2s overviews of Signal and Background
    ######################################################

    # Here's what we wanna do: we want overview histograms that show the number background events, signal events, signal/background ratio,
    # expected significance, difference in significance (in relation to a specific m4l cut), and the uncertainty in the previous difference in significance
    # So each one of those will be presented in an TH2 where the x-Axis contains the different lower m4l limits, and the y-Axis the different upper limits
    # to facilitate that I have the function 'makeResultsTH2' 
    # proviced with two dicts of (m4lLowLimit, m4lHighLimit) -> ROOT.TH1  , let's call those two dicts signalDict and backgroundDict, 
    # This function will loop over all the limit pairs and allow to apply a function 'signalBackgroundComparisonOperation' to be applied to the two TH1s 
    # this function is expected to return just a scaler, which is then Filled in the TH2 that serves as the output
    #
    # I make the different TH2s (signal, background, significance...) by providing different 'signalBackgroundComparisonOperation' function to make the desired plots
    #
    # Only the error on difference plots use a different function, as that one needs more than just signal and background information (it also needs information about the uncertainties thereof)


    signalOverviewDict = {}
    ratioTH2Dict = {}  
    significanceTH2Dict = {}
    deltaSignificanceTH2Dict = {}
    errorDeltaSignificanceTH2Dict = {}

    #### Plot just the number of signal events   
    backgroundTitleString = "#background events in {} {} signal region".format(analysisType, targetVar)
    # to get just the background events I provide a function that just returns the integral over the background hist, check 'makeResultsTH2' definition to see how it works
    justTheBackgroundIntegral = lambda signalHist, backgroundHist : backgroundHist.Integral()
    backgroundTH2 = makeResultsTH2( targetHistsBackground , targetHistsBackground, backgroundTitleString, justTheBackgroundIntegral )

    for DSID in dictOfSignalTargetHists:
        print DSID + "\t Memory usage: %s kB \t Runtime: %10.1f s" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8, (time.time() - startTime ) )

        currentSignalSampleName = myDSIDHelper.physicsProcessSignalByDSID[ int(DSID) ]

        #### Plot just the number of signal events

        signalTitleString = "#signal events in {} {} signal region: {}".format(analysisType, targetVar, currentSignalSampleName)
        justTheSignalIntegral = lambda signalHist, backgroundHist : signalHist.Integral() # analog to how I deal with the background, here's a function that only returns the signal integral
        signalOverviewDict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, signalTitleString, justTheSignalIntegral )

        #### Plot signal to background ratio
        ratioTitleString = "#signal/#background ratio in {} {} signal region: {}".format(analysisType, targetVar, currentSignalSampleName)
        getRatio = lambda signalHist, backgroundHist : doArithmeticOnQualifiedHistIntegrals(signalHist, backgroundHist , integralInterval = integralRangeFunction(signalHist),   arithmetic = lambda A, B : A/B)
        ratioTH2Dict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, ratioTitleString, getRatio )


        #### Plot the expected significance
        significanceTitleString = "signal significance in {} {} signal region: {}".format(analysisType, targetVar, currentSignalSampleName)
        getSignificance = lambda signalHist, backgroundHist : doArithmeticOnQualifiedHistIntegrals(signalHist, backgroundHist , integralInterval = integralRangeFunction(signalHist),  arithmetic = lambda A, B : A/math.sqrt(B) )
        significanceTH2Dict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, significanceTitleString, getSignificance )


        #### calculate the difference in significance to a specific reference one
        deltaSignificanceTitleString = "#Deltasignificance in {} {} signal region: {}".format(analysisType, targetVar, currentSignalSampleName)
        refSignificance = getTH2BinContentByXYValue(significanceTH2Dict[DSID], min(m4lRangeLow), max(m4lRangeHigh) )
        getDeltaSignificance = lambda signalHist, backgroundHist : doArithmeticOnQualifiedHistIntegrals(signalHist, backgroundHist , integralInterval = integralRangeFunction(signalHist),  arithmetic = lambda A, B : A/math.sqrt(B) - refSignificance )
        deltaSignificanceTH2Dict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, deltaSignificanceTitleString, getDeltaSignificance )


        ### calculate the error on the significance difference
        errorDeltaSignificanceTitleString = "error on #Deltasignificance in {} {} signal region: {}".format(analysisType, targetVar, currentSignalSampleName)
        errorDeltaSignificanceTH2Dict[DSID] = calculateDeltaSigError( dictOfSignalTargetHists[DSID] , targetHistsBackground, dictOfSignalComplementaryHists[DSID] , complimentaryHistsBackground, errorDeltaSignificanceTitleString, integralInterval = integralRangeFunction )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    ######################################################
    # Write out all the hists
    ######################################################

    outputFile = ROOT.TFile("m4lStudyOut.ROOT","RECREATE")

    currentDir = "Background"; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
    for TH1 in targetHistsBackground.values(): TH1.Write()
    postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( backgroundTH2), False, "TH2Canvas.pdf", tableOfContents = backgroundTH2.GetName() )


    currentDir = "BackgroundComplimentary"; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
    for TH1 in complimentaryHistsBackground.values(): TH1.Write()
    

    DSIDlist =  dictOfSignalTargetHists.keys(); 
    DSIDlist.sort()
    for DSID in DSIDlist: #dictOfSignalTargetHists: 
        currentDir = "Signal "+DSID; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
        for TH1 in dictOfSignalTargetHists[DSID].values(): TH1.Write()

        lastPlot = (DSID == DSIDlist[-1])
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( signalOverviewDict[DSID])           , False ,  "TH2Canvas.pdf", tableOfContents = DSID +" "+signalOverviewDict[DSID].GetName() )
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( ratioTH2Dict[DSID])                 , False ,  "TH2Canvas.pdf", tableOfContents = DSID +" "+ratioTH2Dict[DSID].GetName())
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( significanceTH2Dict[DSID])          , False ,  "TH2Canvas.pdf", tableOfContents = DSID +" "+significanceTH2Dict[DSID].GetName() )
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( deltaSignificanceTH2Dict[DSID])     , False ,  "TH2Canvas.pdf", tableOfContents = DSID +" "+deltaSignificanceTH2Dict[DSID].GetName() )
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( errorDeltaSignificanceTH2Dict[DSID]), lastPlot,"TH2Canvas.pdf", tableOfContents = DSID +" "+errorDeltaSignificanceTH2Dict[DSID].GetName() )

        currentDir = "SignalComplimentary "+DSID; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
        for TH1 in dictOfSignalComplementaryHists[DSID].values(): TH1.Write()

    outputFile.Close()

    # make some overview plots to put them into my powerpoints

    outputDir = "m4lStudy_"+analysisType+"/"
    if not os.path.exists(outputDir): os.makedirs(outputDir)

    for DSID in DSIDlist: #dictOfSignalTargetHists: 
        overviewCanvas = ROOT.TCanvas(DSID,DSID,1920,1920/3);
        overviewCanvas.Divide(3,1)
        overviewCanvas.cd(1)
        significanceTH2Dict[DSID].Draw("COLZ TEXT45"); #https://root.cern/doc/master/classTHistPainter.html#HP01
        overviewCanvas.cd(2)
        deltaSignificanceTH2Dict[DSID].Draw("COLZ TEXT45"); #https://root.cern/doc/master/classTHistPainter.html#HP01
        overviewCanvas.cd(3)
        errorDeltaSignificanceTH2Dict[DSID].Draw("COLZ TEXT45"); #https://root.cern/doc/master/classTHistPainter.html#HP01

        overviewCanvas.Update()

        overviewCanvas.Print(outputDir+"overviewDSID_"+DSID+".png")
    


    print( "All done!")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here