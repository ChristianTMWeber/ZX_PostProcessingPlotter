######################
#   
#   makeHistDict.py
#
#   Functions that help me to select relevant histograms and assemble them in a convinient dict structure
#
#
#
######################


import ROOT

import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re




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


def fillHistDict( path, currentTH1 , mcTag, aDSIDHelper , channelMap = { "ZXSR" : "signalRegion"}, DSID = None, 
    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):

    # channel map = {"substring in path" : "what we want to replace it with in the output"}

    # prune the path by looking for the DSID part and than taking the DSID part and everything after
    # We exect the folder structure to be somethign like <stuff>/DSID/systematicVariation/TH1, so we prune the <stuff> away
    path =   re.search("/(\d|\d{6})/.*", path).group()      # select 1 or 6 digits within backslashes, and all following (non-linebreak) characters

    # channel options are the 'keys' in the channelMap dict
    channels = [channelMap[x] for x in channelMap.keys() if x in currentTH1.GetName() ]
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


if __name__ == '__main__':

    # import sys and os.path to be able to import functions from parent directory (and parentparent directory)
    import sys 
    from os import path
    sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

    from plotPostProcess import DSIDHelper

    import functions.rootDictAndTDirTools as rootDictAndTDirTools

    postProcessedData = ROOT.TFile("exampleZdZdPostProcessOutput.root","READ"); # open the file with te data from the ZdZdPostProcessing


    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = DSIDHelper()
    myDSIDHelper.importMetaData("../../metadata/md_bkg_datasets_mc16e_All.txt") # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.setMappingOfChoice( "analysisMapping" )

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)





    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if skipTObject(path, myTObject ): continue # skip non-relevant histograms

        masterHistDict = fillHistDict(path, myTObject , "mc16ade",myDSIDHelper ) 



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here