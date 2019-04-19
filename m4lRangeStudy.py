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


def returnFilteredHist( myRDataFrame, targetVariable , myTH1DModel = None , weightVariable = None ):

    if    myTH1DModel is not None and weightVariable is not None : RDFResultHisto=myRDataFrame.Histo1D(myTH1DModel, targetVariable, weightVariable)
    elif  myTH1DModel is not None and weightVariable is     None : RDFResultHisto=myRDataFrame.Histo1D(myTH1DModel, targetVariable)
    elif  myTH1DModel is     None and weightVariable is not None : RDFResultHisto=myRDataFrame.Histo1D(targetVariable, weightVariable)
    else:                                                          RDFResultHisto=myRDataFrame.Histo1D(targetVariable)

    return RDFResultHisto



def defineSetOfM4lFilteredHists( RDF, lowerLimitList, upperLimitList, myTH1DModel = None , weightVariable = None, targetVariable = "m34", makeComplimentaryHists = False):
    # RDF is expected to be a OOT.RDataFrame
    # lowerLimitList and upperLimitList  don't really need to be lists, just iterables
    # makeComplimentaryHists - if true, we will figure out the widest of all the possible limits on m4l, 
    #                          and then for any pair of limits in (m4lBelow, m4lAbove), we will fill another histogram 
    #                          with the events that do not make it into the current set of limits, but would make it into the one with the widest set of possible limits

    # subfinction to help me deal with the different cases of myTH1DModel and weightVariable being provided or not
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
                leftAndRightIntervals  = (min(lowerLimitList), m4lLowLimit, m4lUpperLimit      , max(upperLimitList) )
                cutString = "( m4l > %i $$ m4l < %i ) || m4l > %i $$ m4l < %i )" %( leftAndRightIntervals )

                filteredRDFComplimentary = RDF.Filter( cutString )

                histoDictComplimenatry[ (m4lAbove,m4lBelow) ]  = returnFilteredHist( filteredRDFComplimentary ,targetVariable , myTH1DModel = myTH1DModel , weightVariable = weightVariable, makeComplimentaryHists = False )
                



    
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



def fillTH2WithTargetHists( TH2Hist, histDict, ):

    for m4lLowLimit, m4lUpperLimit in histDict:
        currentTH1 = histDict[(m4lLowLimit, m4lUpperLimit)]
        #print(currentTH1.Integral())
        if isinstance(currentTH1, ROOT.TH1) : TH2Hist.Fill(m4lLowLimit,m4lUpperLimit, currentTH1.Integral() )
        if isinstance(currentTH1, float) :    TH2Hist.Fill(m4lLowLimit,m4lUpperLimit, currentTH1 )
        TH2Hist.GetBinContent(m4lLowLimit,m4lUpperLimit)

    #import pdb; pdb.set_trace() # import

    #canvas = ROOT.TCanvas()
    ##TH2Hist.Draw("COLZ"); canvas.Update()
    #backgroundTH2.Draw("COLZ TEXT"); canvas.Update() #https://root.cern/doc/master/classTHistPainter.html#HP01c


    return None

def doArithmeticOnQualifiedHistIntegrals(hist1, hist2, arithmetic = None , desiredWidth = 0.99 ):
    # pass a function that takes two floats and returns one as 'arithmetic' parameters,
    # the two inputs weil will be the ratio of the integrals from histDict1[ givenKey ] and histDict2[ givenKey ] 
    # where the integral boulds are given by the smallest integral in histDict1[ givenKey ] that subtents 95% of the events in there
    # for example if want want to take the ratio choose
    if arithmetic is None: arithmetic = lambda A, B : A/B

    xLow, xHigh = getSmallestInterval( hist1, desiredWidth = desiredWidth ) # get the smallest intervall that subtends a fraction 'desiredWidth' of all events

    # let's practice lambda functions, and define one that gives me, for a given histogram 'aHist' and an 'xValue', the bin number for the hist of interest
    # the syntax is the following: 
    #  <name of the function>  =   lambda(as sign for python that we get an inline function here)   <parameters of the function>  :   <definition of the function?
    getBinNr = lambda aHist, xValue : aHist.GetXaxis().FindBin(xValue)

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


if __name__ == '__main__':



    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("-c", "--mcCampaign", nargs='*', type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], required=True,
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="metadata/md_bkg_datasets_mc16e_All.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument( "--DSID_Binning", type=str, help = "set how the different DSIDS are combined, ",
        choices=["physicsProcess","physicsSubProcess","DSID"] , default="physicsProcess" )

    parser.add_argument( "--holdAtPlot", type=bool, default=False , 
        help = "Debugging option. If True sets a debugger tracer and \
        activates the debugger at the point where the plot has has been fully assembled." ) 

    parser.add_argument( "--outputName", type=str, default=None , 
        help = "Pick the name of the output files. \
        We'll produce three of them: a root file output (.root), pdfs of the histograms (.pdf) and a .txt indexing the histogram names.\
        If no outputName is choosen, we will default to <inputFileName>_<mcCampaign>_outHistograms." ) 

    parser.add_argument( "--rebin", type=int, default=1 , 
    help = "We can rebin the bins. Choose rebin > 1 to rebin #<rebin> bins into 1." ) 

    args = parser.parse_args()


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
    m4lRangeLow = range(115,125,1); m4lRangeHigh = range(125,131,1)
    dX = float(m4lRangeLow[1] - m4lRangeLow[0])
    dY = float(m4lRangeHigh[1] - m4lRangeHigh[0])
    
    # define a hist which will define the the binning and a few other things for all histograms to follow
    targetHistTemplate = ROOT.TH1D( "templateHist", "templateHist", 150,0,150)
    targetHistTemplate.GetXaxis().SetTitle("m34 [GeV]")


    # target hists: a dict of TH1Ds mapping the tuple (m4lLow, m4lHigh) -> TH1D for that tuple, for each pair of (m4lLow, m4lHigh) that we consider 
    targetHistsBackground = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    dictOfSignalTargetHists = {} # will contain a mappint of DSID -> targetHistsSignal for all signal DSIDs

    # complimentary hists contain the m34 distribution of events for which  min(m4lRangeLow) < m4l < m4lLow or m4lHigh < m4l < max(m4lRangeHigh)
    # we will use them in the calculation of some errors eventually
    complimentaryHistsBackground = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    dictOfSignalComplementaryHists = {} # will contain a mappint of DSID -> targetHistsSignal for all signal DSIDs

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

    ROOT.ROOT.EnableImplicitMT()
    startTime = time.time()
    # loop over all of the TObjects in the given ROOT file
    for path, myTObject  in postProcess.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if postProcess.irrelevantTObject(path, myTObject, requiredRootType=ROOT.TTree): continue # skip non-relevant histograms
        
        

        # path happen to include also the rootfile name, e.g. 'testDir.root/345060/Nominal/t_ZXTree'
        # we need to remove that part of the string, so select everything after the first "/"
        tDirPath = re.search( "(?<=/).+", path ).group()
        

        myDataFrame = ROOT.RDataFrame(tDirPath,args.input) # setup the RDataFrame that we will use to parse the TTree

        RDFrameVariables = myDataFrame.Define("m34","llll_m34 / 1000").Define("m4l","llll_m4l / 1000") # define our variables

        # we want to have multiple m4l filtered histograms. Let's define them here
        RDFHistDict, RDFHistDictComplimentary  = defineSetOfM4lFilteredHists( RDFrameVariables, m4lRangeLow, m4lRangeHigh , myTH1DModel = myTH1DModel,  weightVariable = 'weight', targetVariable = "m34")

        # get the DSID to decide whether the given histogram is signal or background
        DSID = postProcess.idDSID(path)

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

    # background
    backgroundTitleString = "#background events in ZX m34 signal region"
    backgroundTH2 = myTH2Template.Clone(backgroundTitleString)
    backgroundTH2.SetTitle(backgroundTitleString)

    fillTH2WithTargetHists( backgroundTH2, targetHistsBackground)


    signalOverviewDict = {}
    ratioTH2Dict = {}  
    significanceTH2Dict = {}

    for DSID in dictOfSignalTargetHists:

        currentSignalSampleName = myDSIDHelper.physicsProcessSignalByDSID[ int(DSID) ]

        #### Plot just the number of signal events

        signalTitleString = "#signal events in ZX m34 signal region: " + currentSignalSampleName
        justTheSignalIntegral = lambda signalHist, backgroundHist : signalHist.Integral()
        signalOverviewDict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, signalTitleString, justTheSignalIntegral )

        #### Plot signal to background ratio
        ratioTitleString = "#signal/#background ratio in ZX m34 signal region: "  + currentSignalSampleName
        getRatio = lambda signalHist, backgroundHist : doArithmeticOnQualifiedHistIntegrals(signalHist, backgroundHist ,  arithmetic = lambda A, B : A/B)
        ratioTH2Dict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, ratioTitleString, getRatio )


        #### Plot the expected significance
        significanceTitleString = "signal significance in ZX m34 signal region: "  + currentSignalSampleName
        getSignificance = lambda signalHist, backgroundHist : doArithmeticOnQualifiedHistIntegrals(signalHist, backgroundHist ,  arithmetic = lambda A, B : A/math.sqrt(A+B) )
        significanceTH2Dict[DSID] = makeResultsTH2( dictOfSignalTargetHists[DSID] , targetHistsBackground, significanceTitleString, getSignificance )




    outputFile = ROOT.TFile("m4lStudyOut.ROOT","RECREATE")

    currentDir = "Background"; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
    for TH1 in targetHistsBackground.values(): TH1.Write()
    postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( backgroundTH2), False, "TH2Canvas.pdf", tableOfContents = backgroundTH2.GetName() )


    for DSID in dictOfSignalTargetHists: 
        currentDir = "Signal "+DSID; outputFile.mkdir(currentDir); outputFile.cd(currentDir)
        for TH1 in dictOfSignalTargetHists[DSID].values(): TH1.Write()
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( signalOverviewDict[DSID]), False, "TH2Canvas.pdf", tableOfContents = DSID +" "+signalOverviewDict[DSID].GetName() )
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( ratioTH2Dict[DSID]), False, "TH2Canvas.pdf", tableOfContents = DSID +" "+ratioTH2Dict[DSID].GetName())
        postProcess.printRootCanvasPDF(  writeTH2AndGetCanvas( significanceTH2Dict[DSID]), DSID== dictOfSignalTargetHists.keys()[-1] , "TH2Canvas.pdf", tableOfContents = DSID +" "+significanceTH2Dict[DSID].GetName() )

    outputFile.Close()

    print( "All done!")


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    #canvas = ROOT.TCanvas("test","test" ,1300/2,1300/2)
    #backgroundTH2.SetMarkerSize(0.9)
    #backgroundTH2.Draw("COLZ TEXT45"); canvas.Update() #https://root.cern/doc/master/classTHistPainter.html#HP01c




    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here