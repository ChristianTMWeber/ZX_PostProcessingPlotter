# This pythion programm is a pre-step for the limit setting.
# The cutflow for the ZZd analysis outputs a root file with a large number of histograms.
# This program is for selecting the relevant ones, doing the necessary scaling and aggreating 
# and saving them in a structure that is conducive for the limit setting with HistFactory

#   Run as:
#   python limitSettingHistPrep.py ../post_20190813_144634_ZX_Run1516_Background_DataBckgSignal.root -c mc16a
#   Or for development work as:
#   python limitSettingHistPrep.py ../post_20190813_144634_ZX_Run1516_Background_DataBckgSignal.root -c mc16a -q True --interpolateSamples False

# run for now as : 
#   python limitSettingHistPrep.py post_20190530_165131_ZX_Run2_Background_Syst.root -c mc16ade

import ROOT # to do all the ROOT stuff
import argparse # to parse command line options
import warnings # to warn about things that might not have gone right
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import plotPostProcess as postProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
from functions.compareVersions import compareVersions # to compare root versions
import functions.histHelper as histHelper # to help me fill some histograms

import RooIntegralMorphWrapper as integralMorphWrapper

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

def addMockData(masterHistDict  ):

    eventType = "Nominal"

    for channel in masterHistDict.keys():
        for flavor in masterHistDict[channel]["H4l"]["Nominal"].keys():

            H4l = masterHistDict[channel]["H4l"][eventType][flavor]
            ZZ =  masterHistDict[channel]["ZZ"][eventType][flavor]
            const = masterHistDict[channel]["const"][eventType][flavor]

            mockData = H4l.Clone()

            for hist in [H4l, ZZ, const]: mockData.Add(hist)

            masterHistDict[channel]["mockData"][eventType][flavor] = mockData


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
    highLimitX = hist.GetBinLowEdge(nBinsX+2)

    lowLimitY = min(masspoints.keys())
    highLimitY = max(masspoints.keys())+1
    nBinsY = highLimitY - lowLimitY

    signalOverviewTH2 = ROOT.TH2D("signalOverviewTH2", "signalOverviewTH2", nBinsX, lowLimitX, highLimitX, nBinsY , lowLimitY, highLimitY )


    return signalOverviewTH2

def addInterpolatedSignalSamples(masterHistDict, channels = None):

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
                    # do the actual interpolation
                    newSignalHist = integralMorphWrapper.getInterpolatedHistogram(lowHist, highHist,  paramA = lowMass , paramB = highMass, interpolateAt = newMass, morphErrorsToo = True)
                    # determine new names and eventType
                    newEventType = re.sub('\d{2}', str(newMass), masspointDict[lowMass]) # make the new eventType string, by replacing the mass number in a given old one
                    newTH1Name   = re.sub('\d{2}', str(newMass), lowHist.GetName())
                    newSignalHist.SetName(newTH1Name)
                    # add the new histogram to the sample
                    masterHistDict[channel][ newEventType ]["Nominal"][flavor] = newSignalHist
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

    parser.add_argument("-q", "--quick", type=bool, default=False , 
        help = "Debugging option. Skips the filling of parsing of the input file after ~1500 relevant items" ) 

    parser.add_argument("--interpolateSamples", type=bool, default=True , 
        help = "if True we will interpolate between available signal samples in 1GeV steps" ) 

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


    ######################################################
    # Interpolate signal samples in 1GeV steps and add them to the master hist dict
    ######################################################

    masspointDictBeforeInterpolation = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples
    if args.interpolateSamples: addInterpolatedSignalSamples(masterHistDict, channels = "ZXSR")

    ##############################################################################
    # add 'mockdata' hists, i.e. hist constructed from background samples
    ##############################################################################
    addMockData(masterHistDict)

    ##############################################################################
    # write the histograms in the masterHistDict to file for the limit setting
    ##############################################################################
    rootDictAndTDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = "testoutput.root" )

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    ##############################################################################
    # create an overview of the signal samples (regular and interpolated)
    ##############################################################################

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
    signalSampleStack.GetXaxis().SetRange(signalOverviewTH2.GetXaxis().FindBin(15),signalOverviewTH2.GetXaxis().FindBin(61))
    signalSampleStack.Draw("LEGO1")
    canvasSignalOverview3.Update()
   
    massesSorted = masspoints.keys();   massesSorted.sort()

    signalTH1List = []
    for mass in massesSorted: signalTH1List.append(masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All'])



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here







    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
