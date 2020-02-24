import ROOT # to do all the ROOT stuff

import argparse # to parse command line options
import time # for measuring execution time
import re

# import sys and os.path to be able to import functions from parent directory (and parentparent directory)
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
from plotPostProcess import DSIDHelper



sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) )  ) # add also the direct parent directory
import limitFunctions.makeHistDict as makeHistDict
from limitFunctions.visualizeSignalOverview import getMasspointDict
import limitFunctions.RooIntegralMorphWrapper as integralMorphWrapper
import limitFunctions.reportMemUsage as reportMemUsage





def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.10,0.70,0.60,0.90)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend



def addllHistsToMasterHistDict(masterHistDict):

    lowHist  = masterHistDict[channel][ masspointDict[lowMass]  ][systematic][flavor]

    for channel in masterHistDict.keys():
        for eventType in masterHistDict[channel].keys():
            for systematic in masterHistDict[channel][eventType].keys(): 
                for kinematic in masterHistDict[channel][eventType][systematic].keys(): kinematic
                

    return None



def makellCopyOfHist(aHist):

    def makeRenamedHistCopy(originalHist, regexPattern, replaceStr):

        newName = re.sub(regexPattern, replaceStr, originalHist.GetName() )
        newTitle = re.sub(regexPattern, replaceStr, originalHist.GetTitle() )

        newHist = originalHist.Clone(newName)
        newHist.SetTitle(newTitle)

        return newHist

    llmumuSignifiers = "(2e2mu)|(2e2m)|(4mu)"
    lleeSignifiers = "(2mu2e)|(2m2e)|(4e)"

    if    re.search( llmumuSignifiers, aHist.GetName()): llHist = makeRenamedHistCopy(aHist, llmumuSignifiers, "llmumu")
    elif  re.search( lleeSignifiers, aHist.GetName()):   llHist = makeRenamedHistCopy(aHist, lleeSignifiers, "llee")
    else: return None


    return llHist






if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", "-i", type=str, default="post_20200219_204021__ZX_Run2_AllReducibles_May_slimmed.root",
        help="name or path to the input files")

    args = parser.parse_args()

    ######################################################
    # Open the attached .root file and loop over all elements over it
    ######################################################
    startTime = time.time()
    postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

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


    # sort hists into a convinient Dict

    nRelevantHistsProcessed = 0

    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if makeHistDict.skipTObject(path, myTObject): continue # skip non-relevant histograms

        if "Nominal" not in path: continue

        DSID = myDSIDHelper.idDSID( path)



        if int(DSID) not in myDSIDHelper.analysisMapping["Reducible"]: continue

        vetoRegexStr= "(BVeto)|(WZ)" 
        if re.search( vetoRegexStr, myDSIDHelper.physicsSubProcessByDSID[int(DSID)]): continue

        # make a copy of the histogram, where (when appropriate) the flavor composition has been collapsed to llmumu or llee
        # do this so we can make llmumu or llee plots eventually
        lleeOrllmumuHist = makellCopyOfHist(myTObject) # do this before entering myTObject into the makeHistDict.fillHistDict(...), because the latter modifies the myTObject

        masterHistDict = makeHistDict.fillHistDict(path, myTObject , "mc16ade", myDSIDHelper ) 
      
        if lleeOrllmumuHist: masterHistDict = makeHistDict.fillHistDict(path, lleeOrllmumuHist , "mc16ade", myDSIDHelper ) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)
        #if args.quick and (nRelevantHistsProcessed == 2000): break


    #masterHistDict['signalRegion']['Reducible']['Nominal']["llmumu"].Integral()

    

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here





    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here