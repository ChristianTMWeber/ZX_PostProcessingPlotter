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


def skipTObject(path, baseHist, requiredRootType = ROOT.TH1, selectChannels = ["ZXSR", "ZXVR1"], 
                selectKinematic = "m34", selectCuts = ["HWindow", "LowMassSidebands"]  ):

    if "Cutflow" in path: return True
    elif "cutflow" in path: return True
    elif "h_raw_" in path: return True
    elif "hraw_" in path: return True
    elif "pileupWeight" in path: return True
    elif isinstance( baseHist, ROOT.TH2 ): return True
    elif not isinstance( baseHist, requiredRootType ): return True
    elif selectKinematic not in baseHist.GetName(): return True  # if the histogram is not for the kinematic of interest, we can skip it.
    # we want the signal region, and possibly some controll regions. If the hists belongs to neither, then we can skip it
    elif not any( channels in baseHist.GetName() for channels in selectChannels  ) : return True 
    elif not any( cuts in baseHist.GetName() for cuts in selectCuts  ) : return True  # also we are only interested in a subset of cuts

    return False


def fillHistDict( path, currentTH1 , mcTag, aDSIDHelper, channelMap = { "ZXSR" : "signalRegion"}, DSID = None, 
    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):

    # channel map = {"substring in path" : "what we want to replace it with in the output"}

    # prune the path by looking for the DSID part and than taking the DSID part and everything after
    # We exect the folder structure to be somethign like <stuff>/DSID/systematicVariation/TH1, so we prune the <stuff> away
    path =   re.search("/(\d|\d{6})/.*", path).group()      # select 1 or 6 digits within backslashes, and all following (non-linebreak) characters

    # channel options are the 'keys' in the channelMap dict
    channels = [channelMapping[x] for x in channelMapping.keys() if x in currentTH1.GetName() ]
    assert len(channels)==1
    channel = channels[0]
    systematicVariation = path.split("/")[2]

    # determine event type via DSID
    if DSID is None: DSID = int( aDSIDHelper.idDSID(path) )

    if DSID == 0:  eventType = "data"
    else: 
        eventType = aDSIDHelper.mappingOfChoice[DSID]
        scale = aDSIDHelper.getMCScale(DSID, mcTag)
        currentTH1.Scale(scale) # scale the histogram

    flavor = currentTH1.GetName().split("_")[2]


    if flavor not in masterHistDict[channel][eventType][systematicVariation]:
        newName = "_".join([channel, eventType , systematicVariation, flavor ])
        currentTH1.SetName(newName)
        masterHistDict[channel][eventType][systematicVariation][flavor] = currentTH1
    else: masterHistDict[channel][eventType][systematicVariation][flavor].Add(currentTH1)


    # masterHistDict['signalRegion']['ZZ'].keys()
    # masterHistDict['signalRegion']['ZZ']['EG_RESOLUTION_ALL1down'].keys()

    return masterHistDict

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

def getMasspointDict(masterHistDict , channel = None ):
    # returns a dict of the available masspoints: masspointDict[ int ] = <name of event type with that mass>
    # e.g.: masspointDict[20] = 'ZZd, m_{Zd} = 20GeV'
    if channel is None: channel = masterHistDict.keys()[0]
    
    masspointDict = {}
    for eventType in masterHistDict['ZXSR'].keys(): 
        reObject = re.search("\d{2}", eventType)
        if reObject: # True if we found something
            # do some checks that the 'All' and 'Nominal' are in the dict, and that the TH1 in the dict is actually in there
            # these are mostly settings for development
            #if masterHistDict[channel][eventType]['Nominal']['All'] is not None:
            #    print(masterHistDict[channel][eventType]['Nominal']['All'])
                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            masspointDict[ int(reObject.group()) ] = eventType
    return masspointDict

def prepareSignalSampleOverviewTH2(masterHistDict, channel = None):
    if channel is None: channel = masterHistDict.keys()[0]

    masspoints = getMasspointDict(masterHistDict , channel = channel )

    hist = masterHistDict[channel][masspoints.values()[0]]['Nominal']['All']
    nBinsX = hist.GetNbinsX()
    lowLimitX  = hist.GetBinLowEdge(1)
    highLimitX = hist.GetBinLowEdge(nBinsX+1)

    lowLimitY = min(masspoints.keys())
    highLimitY = max(masspoints.keys())+1
    nBinsY = highLimitY - lowLimitY

    signalOverviewTH2 = ROOT.TH2D("signalOverviewTH2", "signalOverviewTH2", nBinsX, lowLimitX, highLimitX, nBinsY , lowLimitY, highLimitY )


    return signalOverviewTH2

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
        for flavor in flavors:
            for lowMass, highMass in massPairs:
                # remember: masspointDict[ mass ] gives the event type name  
                lowHist  = masterHistDict[channel][ masspointDict[lowMass]  ]["Nominal"][flavor]
                highHist = masterHistDict[channel][ masspointDict[highMass] ]["Nominal"][flavor]

                # we want to interpolate between lowHist and highHist in 1GeV steps
                for newMass in xrange(lowMass+1,highMass,1):
                    # do the actual interpolation                                                                                                       #                             errorInterpolation = simulateErrors,  morph1SigmaHists, or morphErrorsToo
                    newSignalHist = integralMorphWrapper.getInterpolatedHistogram(lowHist, highHist,  paramA = lowMass , paramB = highMass, interpolateAt = newMass, morphType = "momentMorph", errorInterpolation = "morph1SigmaHists", nSimulationRounds = 10)
                    # determine new names and eventType
                    newEventType = re.sub('\d{2}', str(newMass), masspointDict[lowMass]) # make the new eventType string, by replacing the mass number in a given old one
                    newTH1Name   = re.sub('\d{2}', str(newMass), lowHist.GetName())
                    newSignalHist.SetName(newTH1Name)
                    # add the new histogram to the sample
                    masterHistDict[channel][ newEventType ]["Nominal"][flavor] = newSignalHist

                    reportMemUsage.reportMemUsage(startTime = startTimeInterp)
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
    targetLumi = myDSIDHelper.lumiMap[ args.mcCampaign[0] ]

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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")


    parser.add_argument("-c", "--mcCampaign", nargs='*', type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], required=True,
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

    args = parser.parse_args()

    channelMapping = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZZCR"}

    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    assert 1 ==  len(args.mcCampaign), "We do not have exactly one mc-campaign tag per input file"

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


    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if skipTObject(path, myTObject, selectChannels = channelMapping.keys() ): continue # skip non-relevant histograms

        masterHistDict = fillHistDict(path, myTObject , args.mcCampaign[0], myDSIDHelper, channelMap = channelMapping ) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)
        if args.quick and (nRelevantHistsProcessed == 2000): break


    addDataDrivenReducibleBackground( masterHistDict  )

    ######################################################
    # Interpolate signal samples in 1GeV steps and add them to the master hist dict
    ######################################################

    masspointDictBeforeInterpolation = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples
    if args.interpolateSamples: addInterpolatedSignalSamples(masterHistDict, channels = "ZXSR")

    ##############################################################################
    # add 'expectedData' hists, i.e. hist constructed from background samples
    ##############################################################################
    addExpectedData(masterHistDict)

    ##############################################################################
    # write the histograms in the masterHistDict to file for the limit setting
    ##############################################################################
    rootDictAndTDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = "testoutput.root" )

    reportMemUsage.reportMemUsage(startTime = startTime)

    ##############################################################################
    # create an overview of the signal samples (regular and interpolated)
    ##############################################################################

    if args.outputSignalOverview:
        signalOverviewTH2 = prepareSignalSampleOverviewTH2(masterHistDict, channel = "ZXSR")
        signalOverviewTH2Interpolated = signalOverviewTH2.Clone( signalOverviewTH2.GetName()+"Interpolated" )

        masspoints = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples

        # sort things into the two overviewTH2s
        for mass in masspoints:
            hist = masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All']
            if mass in masspointDictBeforeInterpolation: histHelper.fillTH2SliceWithTH1(signalOverviewTH2,             hist, mass )
            else:                                        histHelper.fillTH2SliceWithTH1(signalOverviewTH2Interpolated, hist, mass )




        signalOverviewTH2.SetLineColor(ROOT.kBlack)
        signalOverviewTH2.SetFillColor(ROOT.kBlue)
        signalOverviewTH2Interpolated.SetLineColor(ROOT.kBlack)
        signalOverviewTH2Interpolated.SetFillColor(ROOT.kRed)

        signalSampleStack = ROOT.THStack("signalSamples","signalSamples")
        signalSampleStack.Add(signalOverviewTH2)
        signalSampleStack.Add(signalOverviewTH2Interpolated)
        canvasSignalOverview3 = ROOT.TCanvas( "signalOverview3", "signalOverview3" ,1300/2,1300/2)
        signalSampleStack.Draw("LEGO1")
        # the following works only after calling signalSampleStack.Draw() once
        signalSampleStack.GetXaxis().SetRange(signalOverviewTH2.GetXaxis().FindBin(10),signalOverviewTH2.GetXaxis().FindBin(61))

        signalSampleStack.GetXaxis().SetTitle("m_{34} , " + str(signalSampleStack.GetXaxis().GetBinWidth(1) )+" GeV bin-width" )
        #signalSampleStack.GetXaxis().SetTitleSize(0.05)
        signalSampleStack.GetXaxis().SetTitleOffset(2.)
        signalSampleStack.GetXaxis().CenterTitle()

        signalSampleStack.GetYaxis().SetTitle("signal sample masspoint [GeV]" )
        signalSampleStack.GetYaxis().SetTitleOffset(2.)
        signalSampleStack.GetYaxis().CenterTitle()



        signalSampleStack.Draw("LEGO1")
        canvasSignalOverview3.Update()
       
        massesSorted = masspoints.keys();   massesSorted.sort()

        signalTH1List = []
        for mass in massesSorted: signalTH1List.append(masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All'])

        signalOverviewFile = ROOT.TFile("signalOverview.root","RECREATE")
        signalOverviewTH2.Write()
        signalOverviewTH2Interpolated.Write()
        signalSampleStack.Write()
        canvasSignalOverview3.Write()
        for hist in signalTH1List: hist.Write()
        signalOverviewFile.Close()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here








    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


