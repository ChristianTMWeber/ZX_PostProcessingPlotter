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

def getLongestSubstringAmongSubstringCandidates(referenceString, subStringCandidates):

    assert isinstance(subStringCandidates, list)

    subStringCandidates.sort( key = lambda x:len(x), reverse=True)

    for subString in subStringCandidates:
        if subString in referenceString: return subString

    return None


def fillHistDict( path, currentTH1 , mcTag, aDSIDHelper , channelMap = { "ZXSR" : "signalRegion"}, DSID = None, customMapping = None,
    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) , doScaling = True):

    # channel map = {"substring in path" : "what we want to replace it with in the output"}

    # prune the path by looking for the DSID part and than taking the DSID part and everything after
    # We exect the folder structure to be somethign like <stuff>/DSID/systematicVariation/TH1, so we prune the <stuff> away
    path =   re.search("/(\d|\d{6})/.*", path).group()      # select 1 or 6 digits within backslashes, and all following (non-linebreak) characters

    # channel options are the 'keys' in the channelMap dict
    channelKey = getLongestSubstringAmongSubstringCandidates(currentTH1.GetName(),channelMap.keys())
    if channelKey is None:  return masterHistDict

    channel = channelMap[channelKey]

    systematicVariation = path.split("/")[2]

    # determine event type via DSID
    if DSID is None: DSID = int( aDSIDHelper.idDSID(path) )

    scale = 1

    if DSID == 0:  eventType = "data"
    else: 

        if customMapping is not None: eventType = customMapping[DSID]
        else:                         eventType = aDSIDHelper.mappingOfChoice[DSID]
        if doScaling: scale = aDSIDHelper.getMCScale(DSID, mcTag)
        #currentTH1.Scale(scale) # scale the histogram

    flavor = currentTH1.GetName().split("_")[2]

#    print path +"\t" + currentTH1.GetName()

    #if flavor == "Nominal": import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    th1Clone = currentTH1.Clone("tempHist")
    if scale != 1: th1Clone.Scale(scale)# scale the histogram


    if flavor not in masterHistDict[channel][eventType][systematicVariation]:
        newName = "_".join([channel, eventType , systematicVariation, flavor ])
        th1Clone.SetName(newName)
        masterHistDict[channel][eventType][systematicVariation][flavor] = th1Clone
    else: masterHistDict[channel][eventType][systematicVariation][flavor].Add(th1Clone)


    # masterHistDict['signalRegion']['ZZ'].keys()
    # masterHistDict['signalRegion']['ZZ']['EG_RESOLUTION_ALL1down'].keys()

    return masterHistDict

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