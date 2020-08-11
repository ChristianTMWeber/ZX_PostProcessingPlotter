# This pythion programm is a pre-step for the limit setting.
# The cutflow for the ZZd analysis outputs a root file with a large number of histograms.
# This program is for selecting the relevant ones, doing the necessary scaling and aggreating 
# and saving them in a structure that is conducive for the limit setting with HistFactory

#   Run as:
#   python limitSettingHistPrep.py ../post_20190831_170144_ZX_Run1516_Background_DataBckgSignal.root -c mc16a --interpolateSamples 
#   python limitSettingHistPrep.py ../post_20190905_233618_ZX_Run2_BckgSignal.root -c mc16ade --interpolateSamples 
#   Or for development work as:
#   python limitSettingHistPrep.py ../post_20190831_170144_ZX_Run1516_Background_DataBckgSignal.root -c mc16a --quick 


import ROOT # to do all the ROOT stuff
import argparse # to parse command line options
import warnings # to warn about things that might not have gone right
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import time # for measuring execution time
import copy # for making deep copies


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import plotPostProcess as postProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
from functions.compareVersions import compareVersions # to compare root versions
import functions.histHelper as histHelper # to help me fill some histograms

import limitFunctions.RooIntegralMorphWrapper as integralMorphWrapper
import limitFunctions.reportMemUsage as reportMemUsage
from limitFunctions.visualizeSignalOverview import getMasspointDict

import limitFunctions.makeHistDict as makeHistDict # things to fill what I call later the masterHistDict
import limitFunctions.assembleTheoryShapeVariationHists as assembleTheoryShapeVariationHists # method to add the theory shape variations


import makeReducibleShapes.makeReducibleShapes as makeReducibleShapes


def addExpectedData(masterHistDict  ):

    eventType = "Nominal"

    for channel in masterHistDict.keys():
        for flavor in masterHistDict[channel]["H4l"][eventType].keys():

            H4l = masterHistDict[channel]["H4l"][eventType][flavor]
            ZZ =  masterHistDict[channel]["ZZ"][eventType][flavor]
            const = masterHistDict[channel]["VVV_Z+ll"][eventType][flavor]

            histList = [ZZ, const]

            # dataDriven estimates are only available in the signal region
            if "reducibleDataDriven" in masterHistDict[channel]: 
                if flavor in masterHistDict[channel]["reducibleDataDriven"][eventType]:
                    histList.append( masterHistDict[channel]["reducibleDataDriven"][eventType][flavor] )

            # create the 'expectedData' histogram
            expectedData = H4l.Clone()
            newHistName   = re.sub('H4l', 'expectedData', expectedData.GetName())
            expectedData.SetName(newHistName)

            for hist in histList: expectedData.Add(hist)

            # set the bin error for each bin each to the square-root of the content to approximate poisson erros
            #for n in xrange(0,hist.GetNbinsX()+2): expectedData.SetBinError(n, abs(expectedData.GetBinContent(n))**0.5 )

            masterHistDict[channel]["expectedData"][eventType][flavor] = expectedData # save the hist to the masterHistDict

    return None



def addInterpolatedSignalSamples(masterHistDict, channels = None):
    startTimeInterp = time.time()

    if channels is None: channels = masterHistDict.keys()
    elif not isinstance(channels, list):  channels = [channels]

    for channel in channels:
        masspointDict = getMasspointDict(masterHistDict , channel = channel )
        sortedMasses = masspointDict.keys(); 
        sortedMasses.sort()

        # build pairs of masspoints to interpolate in between
        massPairs = []
        for n in xrange(0, len(sortedMasses)-1): massPairs.append( (sortedMasses[n],sortedMasses[n+1]) )
        

        # don't forget to loop over all flavors:
        flavors = masterHistDict[channel][masspointDict.values()[0]]["Nominal"].keys()
        for systematic in masterHistDict[channel][masspointDict.values()[0]].keys():
            #if systematic != "Nominal": continue
            for flavor in flavors:
                # remember: masspointDict[ mass ] gives the event type name  
                refHist  = masterHistDict[channel][ masspointDict.values()[0]  ][systematic][flavor]

                histsAndMasses = [ (masterHistDict[channel][ masspointDict[mass]  ][systematic][flavor], mass) for mass in masspointDict ]

                interpolationPoints = []

                for mass in range(min(masspointDict.keys()), max(masspointDict.keys())+1):
                    if mass not in masspointDict.keys(): interpolationPoints.append(mass)



                print( channel +" "+ systematic +" "+ flavor )
                # do the actual interpolation                                                                       #                             errorInterpolation = simulateErrors,  morph1SigmaHists, or morphErrorsToo
                newSignalHistDict = integralMorphWrapper.getInterpolatedHistogram(histsAndMasses, interpolateAt = interpolationPoints, morphType = "momentMorph", errorInterpolation = "morph1SigmaHists", nSimulationRounds = 10)

                for interpolatedMass in newSignalHistDict: 
                    # determine new names and eventType
                    newEventType = re.sub('\d{2}', str(interpolatedMass), masspointDict.values()[0]) # make the new eventType string, by replacing the mass number in a given old one
                    newTH1Name   = re.sub('\d{2}', str(interpolatedMass), refHist.GetName())
                    newSignalHistDict[interpolatedMass].SetName(newTH1Name)
                    newSignalHistDict[interpolatedMass].SetTitle(refHist.GetTitle())
                    # add the new histogram to the sample
                    masterHistDict[channel][ newEventType ][systematic][flavor] = newSignalHistDict[interpolatedMass]

                reportMemUsage.reportMemUsage(startTime = startTimeInterp)


                # interpolate signal samples at the masses we simulate them for comparison purposes
    #                for massToInterpolate in range(20,50+1):
    #
    #                    # getInterpolatedHistogram takes not as input a list of tuples [(hist,parameter at which hist is realized),...]
    #                    # remember to exclude the hist that we want to interpolate at
    #                    histsAndMasses = [ (masterHistDict[channel][ masspointDict[mass]  ][systematic][flavor], mass) for mass in masspointDict if  mass%10 !=5 ]
    #
    #                    # we want to interpolate between lowHist and highHist in 1GeV steps
    #                    # do the actual interpolation                                                                                                       #                             errorInterpolation = simulateErrors,  morph1SigmaHists, or morphErrorsToo
    #                    #newSignalHist = integralMorphWrapper.getInterpolatedHistogram(lowHist, highHist,  paramA = lowMass , paramB = highMass, interpolateAt = newMass, morphType = "momentMorph", errorInterpolation = "morph1SigmaHists", nSimulationRounds = 10)
    #                    newSignalHist = integralMorphWrapper.getInterpolatedHistogram(histsAndMasses, interpolateAt = massToInterpolate, errorInterpolation = "morph1SigmaHists" , morphType = "momentMorph", nSimulationRounds = 100)
    #
    #                    # determine new names and eventType
    #                    newEventType = re.sub('\d{2}', str(massToInterpolate), masspointDict[15])+"_Interpolated" # make the new eventType string, by replacing the mass number in a given old one
    #                    newTH1Name   = re.sub('\d{2}', str(massToInterpolate), masterHistDict[channel][ masspointDict[15] ][systematic][flavor].GetName())+"_Interpolated"
    #                    newSignalHist.SetName(newTH1Name)
    #
    #                    #referenceHist = masterHistDict[channel][ masspointDict[massToInterpolate] ][systematic][flavor] # histogram from simulation at the Zd mass that we are interpolating at
    #                    #interpolatedNorm = newSignalHist.Integral()
    #                    #simulatedNorm = referenceHist.Integral()
    #
    #                    #newSignalHist.Scale(simulatedNorm/interpolatedNorm)
    #
    #                    #print( "Zd mass = %i: interpolatedNorm = %f, simulatedNorm = %f" %(newMass, interpolatedNorm, simulatedNorm) )
    #
    #                    # add the new histogram to the sample
    #                    masterHistDict[channel][ newEventType ][systematic][flavor] = newSignalHist
    #
    #                    reportMemUsage.reportMemUsage(startTime = startTimeInterp)

    return None


def addDataDrivenReducibleBackground( masterHistDict , reducibleFileName = "dataDrivenBackgroundsFromH4l/allShapes.root" ):

    def useHistAContentWithHistBBinning(histA, histB):

        newHist = histB.Clone( histA.GetName() )
        newHist.Reset()

        for x in xrange(1,newHist.GetNbinsX()+1):

            currentVal = newHist.GetBinCenter(x)

            sourceBinNr = histA.GetXaxis().FindBin(currentVal) # tells me the bin number for the given x-axis value. Usefull for filling histograms, which have to be filled by bin numbr: hist.SetBinContent( binNumber, binContent)
            sourceContent = histA.GetBinContent(sourceBinNr)

            newHist.SetBinContent(x,sourceContent)

        currentNorm = newHist.Integral()
        targetNorm = histA.Integral()
        newHist.Scale(targetNorm / currentNorm) 
        return newHist

    def addRelativeHistError(hist, relError):
        for n in xrange(0,hist2l2e.GetNbinsX()+2): 
            hist.SetBinError(n, hist.GetBinContent(n) * relError )
        return None

    reducibleTFile = ROOT.TFile(reducibleFileName, "OPEN")

    histName_2l2e  = "h_m34_2l2e"
    histName_2l2mu = "h_m34_2l2mu"


    hist2l2e = reducibleTFile.Get(  histName_2l2e )

    ########### Fix Binning of 2l2mu histogram ########

    # the h_m34_2l2mu hist in the file has a mismatched binning
    # instead of having some bins in 'm_34 [GeV]', there are just bin numbers
    # The h_m34_2l2e has the propper binning though, and we will copy that one
    hist2l2muImproperBins = reducibleTFile.Get( histName_2l2mu )


    # copy the bin contents into a new histogram with the proper binning
    hist2l2mu = hist2l2e.Clone( hist2l2muImproperBins.GetName() )
    hist2l2mu.Reset()

    for n in xrange(0,hist2l2e.GetNbinsX()+2): hist2l2mu.SetBinContent(n , hist2l2muImproperBins.GetBinContent(n) )


    ########## normalize histograms to Target Luminosity ########

    # H4l shapes are normalized to 1 inverse femto barn, we need to scale the up to the target lumi
    targetLumi = myDSIDHelper.lumiMap[ args.mcCampaign ]

    hist2l2e.Scale(targetLumi)
    hist2l2mu.Scale(targetLumi)


    ########### transform the binnin of the histograms in a crude way

    refHist = masterHistDict.values()[0].values()[0].values()[0].values()[0].Clone("referenceHist")

    hist2l2e = useHistAContentWithHistBBinning( hist2l2e , refHist)
    hist2l2mu = useHistAContentWithHistBBinning( hist2l2mu , refHist)

    # add 2l2mu hist and 2l2e hist for the 'All' Channel
    histAll = hist2l2e.Clone(  re.sub('2l2e', 'All', hist2l2e.GetName())  )
    histAll.Add(hist2l2mu)

    for hist in [hist2l2e, hist2l2mu, histAll]: hist.SetDirectory(0) # to decouple it from the open file directory. Now you can close the file and continue using the histogram. https://root.cern.ch/root/roottalk/roottalk02/2266.html

    #                                  #add stat error only. Add syst error to limitSetting.py instead
    addRelativeHistError( hist2l2e  ,  (2.54*0.0843 + 3.19*0.0597)/(2.54+3.19)  ) 
    addRelativeHistError( hist2l2mu ,  (2.29*0.0152 + 2.57*0.0152)/(2.29+2.57) )
    addRelativeHistError( histAll   , 0.0284 )


    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["2l2e"] = hist2l2e
    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["2l2mu"] = hist2l2mu
    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["All"] = histAll

    reducibleTFile.Close()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None

def addDataDrivenReducibleBackground2( masterHistDict ):
    # this is based on my efforts to create reducible shapes

    referenceHist = masterHistDict["ZXSR"].values()[0]["Nominal"]["All"]

    th1Dict = makeReducibleShapes.getReducibleTH1s(TH1Template = referenceHist , convertXAxisFromMeVToGeV = True)


    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["All"]   = th1Dict["all"]    
    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["2l2e"]  = th1Dict["llee"]
    masterHistDict["ZXSR"]["reducibleDataDriven"]["Nominal"]["2l2mu"] = th1Dict["llmumu"]

    return None

def add2l2eAnd2l2muHists(masterHistDict):

    for channel in masterHistDict.keys():
        for eventType in masterHistDict[channel]: 
            if eventType == "reducibleDataDriven": continue
            for systematic in masterHistDict[channel][eventType]: 

                ############### assemble 2l2e final state ##################
                hist4e    = masterHistDict[channel][eventType][systematic]["4e"]
                hist2mu2e = masterHistDict[channel][eventType][systematic]["2mu2e"]

                hist2l2e = hist4e.Clone( re.sub('4e', '2l2e', hist4e.GetName())  )
                hist2l2e.SetTitle(       re.sub('4e', '2l2e', hist4e.GetTitle()) ) 
                hist2l2e.Add(hist2mu2e)

                masterHistDict[channel][eventType][systematic]["2l2e"] = hist2l2e

                ############### assemble 2l2mu final state ##################
                hist4mu    = masterHistDict[channel][eventType][systematic]["4mu"]
                hist2e2mu = masterHistDict[channel][eventType][systematic]["2e2mu"]

                hist2l2mu = hist4mu.Clone( re.sub('4mu', '2l2mu', hist4mu.GetName())  )
                hist2l2mu.SetTitle(        re.sub('4mu', '2l2mu', hist4mu.GetTitle()) ) 
                hist2l2mu.Add(hist2e2mu)

                masterHistDict[channel][eventType][systematic]["2l2mu"] = hist2l2mu

    return None

def loopOverRecursiveDict( aDict ):

    for value in aDict.values():
        if isinstance(value,dict): 
            for output in loopOverRecursiveDict( value ): yield output
        else: yield value

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("--outputTo", type=str, default="testoutput.root" ,
        help="name of the output file" )

    parser.add_argument("-c", "--mcCampaign", type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], default="mc16ade",
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="../metadata/md_bkg_datasets_mc16e_All.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument( "--DSID_Binning", type=str, help = "set how the different DSIDS are combined, ",
        choices=["physicsProcess","physicsSubProcess","DSID","analysisMapping"] , default="analysisMapping" )

    parser.add_argument("--quick", default=False , action='store_true',
        help = "Debugging option. Skips the filling of parsing of the input file after ~2000 relevant items" ) 

    parser.add_argument("--interpolateSamples", default=False, action='store_true' ,       # this is the more proper way to affect default booleans
        help = "if True we will interpolate between available signal samples in 1GeV steps" ) 

    parser.add_argument("--outputSignalOverview", default=False, action='store_true' ,       # this is the more proper way to affect default booleans
        help = "output overview of signal samples" ) 

    parser.add_argument( "--rebin", type=int, default=1 , 
    help = "We can rebin the bins. Choose rebin > 1 to rebin #<rebin> bins into 1." ) 

    args = parser.parse_args()

    channelMapping = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZZCR"}

    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    # check root version
    currentROOTVersion = ROOT.gROOT.GetVersion()

    if compareVersions( currentROOTVersion, "6.04/16") > 0:
        warnings.warn("Running on newer than ideal root version. Designed for version 6.04/16, current version is  "
                       + currentROOTVersion + ". This should work but might consume much more memory then otherwise. ")
        # the underlying issue for the extra memory consumption is the root memory managment. 
        # For the version 6.04/16 our method of given root ownership of the parsed opjects to delete them works and memory utilization is lower
        # for the newer versions this way of affecting the ownership results in a crash. So we don't deal with it and accept higher memory utilization
        ownershipSetpoint = None
    else: ownershipSetpoint = True


    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = postProcess.DSIDHelper()
    myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.setMappingOfChoice( args.DSID_Binning )

    # assemble the input files, mc-campaign tags and metadata file locations into dict
    # well structered dict is sorted by mc-campign tag and has 


    ######################################################
    # Open the attached .root file and loop over all elements over it
    ######################################################
    startTime = time.time()
    postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)

    nRelevantHistsProcessed = 0

    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) 
    pmgWeightDict  = copy.deepcopy(masterHistDict)  

    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if makeHistDict.skipTObject(path, myTObject, selectChannels = channelMapping.keys() ): continue # skip non-relevant histograms

        #if myTObject.GetBinWidth(1) != 1.0:
        #    if myTObject.GetBinWidth(1) == 0.5: myTObject.Rebin(2)
        #    else: raise ValueError('Bin size is neither 1 nor 0.5. Check the binwidth, and decide which binwidth you want.')


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


        #if args.rebin > 1: myTObject.Rebin( args.rebin )
        if "PMG_" not in path: 
            masterHistDict = makeHistDict.fillHistDict(path, myTObject , args.mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = masterHistDict) 
        if "PMG_" in path or "Nominal" in path:
            pmgWeightDict  = makeHistDict.fillHistDict(path, myTObject , args.mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = pmgWeightDict, customMapping=myDSIDHelper.DSIDtoDSIDMapping) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)
        if args.quick and (nRelevantHistsProcessed == 2000): break


    assembleTheoryShapeVariationHists.addTheoryVariationsToMasterHistDict( pmgWeightDict, masterHistDict,  myDSIDHelper.mappingOfChoiceInverse, region = "ZXSR", backgroundtypes = ["H4l", "ZZ"], prefix="PMG_", outputEnvelopeDir = "theorySystOverview")

    addDataDrivenReducibleBackground2( masterHistDict  )

    ######################################################
    # Interpolate signal samples in 1GeV steps and add them to the master hist dict
    ######################################################

    masspointDictBeforeInterpolation = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples
    if args.interpolateSamples: addInterpolatedSignalSamples(masterHistDict, channels = "ZXSR")

    ##############################################################################
    # add 'expectedData' hists, i.e. hist constructed from background samples
    ##############################################################################
    addExpectedData(masterHistDict)

    ###############################################################################################################
    # sum up 4e + 2mu2e hists to 2l2e and 4mu + 2e2mu hists to 2l2mu hists, and include them in the masterHistDict
    ###############################################################################################################
    add2l2eAnd2l2muHists(masterHistDict)



    ###############################################################################################################
    # Rebin all the hists, usefull if we wanna interpolate at a smaller binning
    ###############################################################################################################
    if args.rebin > 1: 
        for anyHist in loopOverRecursiveDict( masterHistDict  ): anyHist.Rebin( args.rebin )

    ##############################################################################
    # write the histograms in the masterHistDict to file for the limit setting
    ##############################################################################
    rootDictAndTDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = args.outputTo )

    reportMemUsage.reportMemUsage(startTime = startTime)

    ##############################################################################
    # create an overview of the signal samples (regular and interpolated)
    ##############################################################################

    if args.outputSignalOverview:

        import limitFunctions.visualizeSignalOverview as visualizeSignalOverview

        signalSampleStack, canvasSignalOverview3  = visualizeSignalOverview.make3dOverview(masterHistDict, masspointsBeforeInterpolation = masspointDictBeforeInterpolation )


        

        masspoints = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples
       
        massesSorted = masspoints.keys();   massesSorted.sort()

        signalTH1List = []
        for mass in massesSorted: signalTH1List.append(masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All'])

        signalOverviewFile = ROOT.TFile("signalOverview.root","RECREATE")


        signalSampleStack.Write()
        canvasSignalOverview3.Write()
        for hist in signalTH1List: hist.Write()
        signalOverviewFile.Close()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here








    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


