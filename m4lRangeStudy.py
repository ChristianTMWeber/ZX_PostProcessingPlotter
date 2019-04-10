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


def defineSetOfM4lFilteredHists( RDF, lowerLimitList, upperLimitList, myTH1DModel = None , weightVariable = None):
    # RDF is expected to be a OOT.RDataFrame
    # lowerLimitList and upperLimitList  don't really need to be lists, just iterables


    histoDict = {} # store my RDF.Histo1D s here as { (m4lLowLimit, m4lUpperLimit) : RDF.Histo1D, ... }

    for m4lAbove in lowerLimitList:
        for m4lBelow in upperLimitList:

            m4lLowLimit  = "m4l > %i" %m4lAbove
            m4lUpperLimit= "m4l < %i" %m4lBelow

            filteredRDF = RDF.Filter( m4lLowLimit ).Filter( m4lUpperLimit )

            if    myTH1DModel is not None and weightVariable is not None : RDFResultHisto=filteredRDF.Histo1D(myTH1DModel, "m34", weightVariable)
            elif  myTH1DModel is not None and weightVariable is     None : RDFResultHisto=filteredRDF.Histo1D(myTH1DModel, "m34")
            elif  myTH1DModel is     None and weightVariable is not None : RDFResultHisto=filteredRDF.Histo1D("m34", weightVariable)
            else:                                                          RDFResultHisto=filteredRDF.Histo1D("m34")

            histoDict[ (m4lAbove,m4lBelow)] = RDFResultHisto
    
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return histoDict

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


def histByHistGetIntegralsAndApplyArithmetics(histDict1, histDict2, arithmetic = None  ):
    # pass a function that takes two floats and returns one as 'arithmetic' parameters,
    # the two inputs weil will be the ratio of the integrals from histDict1[ givenKey ] and histDict2[ givenKey ] 
    # where the integral boulds are given by the smallest integral in histDict1[ givenKey ] that subtents 95% of the events in there
    # for example if want want to take the ratio choose
    if arithmetic is None: arithmetic = lambda A, B : A/B

    assert( set(histDict1.keys()) == set(histDict2.keys()) )

    outputDict = {}

    for key in histDict1: 
        hist1 = histDict1[ key ]
        hist2 = histDict2[ key ]

        xLow, xHigh = getSmallestInterval( hist1, desiredWidth = 0.99) # get the smallest intervall that subtends a fraction 'desiredWidth' of all events

        # let's practice lambda functions, and define one that gives me, for a given histogram 'aHist' and an 'xValue', the bin number for the hist of interest
        # the syntax is the following: 
        #  <name of the function>  =   lambda(as sign for python that we get an inline function here)   <parameters of the function>  :   <definition of the function?
        getBinNr = lambda aHist, xValue : aHist.GetXaxis().FindBin(xValue)

        integral1 = hist1.Integral( getBinNr(hist1, xLow),getBinNr(hist1, xHigh) )
        integral2 = hist2.Integral( getBinNr(hist2, xLow),getBinNr(hist2, xHigh) )


        outputDict[key] = arithmetic(integral1,integral2)

    return outputDict



def writeTH2AndGetCanvas( TH2 ):

    TH2.Write()

    tmpCanvas = ROOT.TCanvas( TH2.GetName() , TH2.GetTitle() ,1300/2,1300/2)
    TH2.SetMarkerSize(0.9)
    TH2.Draw("COLZ TEXT45"); #https://root.cern/doc/master/classTHistPainter.html#HP01
    tmpCanvas.Update()

    return tmpCanvas



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
    #Select relevant (ROOT) objects
    ######################################################

    postProcessedData = ROOT.TFile(args.input, "READ"); # open the file with te data from the ZdZdPostProcessing

    m4lRangeLow = range(115,125,1); m4lRangeHigh = range(125,131,1)
    dX = float(m4lRangeLow[1] - m4lRangeLow[0])
    dY = float(m4lRangeHigh[1] - m4lRangeHigh[0])
    
    # define a hist which will define the the binning and a few other things for all histograms to follow
    targetHistTemplate = ROOT.TH1D( "templateHist", "templateHist", 150,0,150)
    targetHistTemplate.GetXaxis().SetTitle("m34 [GeV]")


    targetHistsBackground = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    targetHistsSignal     = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
    dictOfSignalTargetHists = {}

    # define this as a model for the RDataFrome histograms
    myTH1DModel = ROOT.RDF.TH1DModel(targetHistTemplate)

    myTH2Template = ROOT.TH2D( "templateHist2D", "templateHist2D", len(m4lRangeLow), min(m4lRangeLow)-dX/2, max(m4lRangeLow)+dX/2, len(m4lRangeHigh) , min(m4lRangeHigh)-dY/2, max(m4lRangeHigh)+dY/2  )
    myTH2Template.GetXaxis().SetTitle("lower limit on m4l")
    myTH2Template.GetYaxis().SetTitle("upper limit on m4l")
    myTH2Template.SetStats( False) # remove stats box

    ROOT.ROOT.EnableImplicitMT()
    # loop over all of the TObjects in the given ROOT file
    for path, myTObject  in postProcess.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if postProcess.irrelevantTObject(path, myTObject, requiredRootType=ROOT.TTree): continue # skip non-relevant histograms
        
        print path + "\t Memory usage: %s (kB)" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8)

        # path happen to include also the rootfile name, e.g. 'testDir.root/345060/Nominal/t_ZXTree'
        # we need to remove that part of the string, so select everything after the first "/"
        tDirPath = re.search( "(?<=/).+", path ).group()
        

        myDataFrame = ROOT.RDataFrame(tDirPath,args.input) # setup the RDataFrame that we will use to parse the TTree

        RDFrameVariables = myDataFrame.Define("m34","llll_m34 / 1000").Define("m4l","llll_m4l / 1000") # define our variables

        # we want to have multiple m4l filtered histograms. Let's define them here
        RDFHistDict = defineSetOfM4lFilteredHists( RDFrameVariables, m4lRangeLow, m4lRangeHigh , myTH1DModel = myTH1DModel,  weightVariable = 'weight')

        # get the DSID to decide whether the given histogram is signal or background
        DSID = postProcess.idDSID(path)

        if myDSIDHelper.isSignalSample( int(DSID) ):
            if DSID not in dictOfSignalTargetHists:  dictOfSignalTargetHists[DSID] = defineTargetHistograms(m4lRangeLow, m4lRangeHigh, templateHist = targetHistTemplate)
            currentTarget = dictOfSignalTargetHists[DSID]
        else :  currentTarget = targetHistsBackground

        addToTargetHists(currentTarget, RDFHistDict, scale = myDSIDHelper.getMCScale(DSID) )


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

    # signal

    signalOverviewDict = {}
    for DSID in dictOfSignalTargetHists:
        signalTitleString = "#signal events in ZX m34 signal region: "
        signalTitleString += myDSIDHelper.physicsProcessSignalByDSID[ int(DSID) ]

        currentSignalTH2 = myTH2Template.Clone( signalTitleString )
        currentSignalTH2.SetTitle(signalTitleString)
        fillTH2WithTargetHists( currentSignalTH2, dictOfSignalTargetHists[DSID] )


        signalOverviewDict[DSID]=currentSignalTH2



    # make TH2 overview plots of the signal / background and  significance = signal / sqrt( signal + background)
    # in each case we are looking in the region where we find 95% of the signal

    ratioTH2Dict = {}  
    for DSID in dictOfSignalTargetHists:
        ratioTitleString = "#signal/#background ratio in ZX m34 signal region: "
        ratioTitleString += myDSIDHelper.physicsProcessSignalByDSID[ int(DSID) ]

        currentSignalTH1Dict = dictOfSignalTargetHists[DSID]

        getRatioDict = histByHistGetIntegralsAndApplyArithmetics(currentSignalTH1Dict, targetHistsBackground,  arithmetic = lambda A, B : A/B)

        currentSignalTH2 = myTH2Template.Clone( ratioTitleString )
        currentSignalTH2.SetTitle(ratioTitleString)
        fillTH2WithTargetHists( currentSignalTH2, getRatioDict  )

        ratioTH2Dict[DSID] = currentSignalTH2


    significanceTH2Dict = {}

    for DSID in dictOfSignalTargetHists:
        significanceTitleString = "signal significance in ZX m34 signal region: "
        significanceTitleString += myDSIDHelper.physicsProcessSignalByDSID[ int(DSID) ]

        currentSignalTH1Dict = dictOfSignalTargetHists[DSID]

        getSignificanceDict = histByHistGetIntegralsAndApplyArithmetics(currentSignalTH1Dict, targetHistsBackground,  arithmetic = lambda A, B : A/math.sqrt(A+B) ) 

        currentSignalTH2 = myTH2Template.Clone( significanceTitleString )
        currentSignalTH2.SetTitle(significanceTitleString)
        fillTH2WithTargetHists( currentSignalTH2, getSignificanceDict  )

        significanceTH2Dict[DSID] = currentSignalTH2


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