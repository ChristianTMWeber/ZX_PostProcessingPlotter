# This pythion programm is a pre-step for the limit setting.
# The cutflow for the ZZd analysis outputs a root file with a large number of histograms.
# This program is for selecting the relevant ones, doing the necessary scaling and aggreating 
# and saving them in a structure that is conducive for the limit setting with HistFactory

# run for now as : 
#   python limitSettingHistPrep.py post_20190530_165131_ZX_Run2_Background_Syst.root -c mc16ade

import ROOT # to do all the ROOT stuff
import argparse # to parse command line options
import warnings # to warn about things that might not have gone right
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import plotPostProcess as postProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
from functions.compareVersions import compareVersions # to compare root versions


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


def fillHistDict( path, currentTH1 , mcTag, aDSIDHelper, channelMap = {"signalRegion" : "ZXSR"}, DSID = None, 
    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):

    

    channel = [x for x in channelMapping.keys() if channelMapping[x] in currentTH1.GetName() ][0]
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
        masterHistDict[channel][eventType][systematicVariation][flavor] = currentTH1
    else: masterHistDict[channel][eventType][systematicVariation][flavor].Add(currentTH1)


    # masterHistDict['signalRegion']['ZZ'].keys()
    # masterHistDict['signalRegion']['ZZ']['EG_RESOLUTION_ALL1down'].keys()

    return masterHistDict



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

    args = parser.parse_args()

    channelMapping = { "signalRegion" : "ZXSR", "ZZControlRegion" : "ZXVR1"}

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

        if skipTObject(path, myTObject, selectChannels = channelMapping.values() ): continue # skip non-relevant histograms

        masterHistDict = fillHistDict(path, myTObject , args.mcCampaign[0], myDSIDHelper, channelMap = channelMapping ) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)

    rootDictAndTDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = "testoutput.root" )



    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here









    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

