#
#   Use this script to transform results from the grid version of the hypo test inveter (not in this repository)
#   to inputs usable with the plotXSLimits.py
#
#
#

import ROOT
import re
import os
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly

import limitSetting as limitSetting
from limitFunctions.listsToTTree import fillTTreeWithDictOfList # concert of dict of lists into a TTree


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper

if __name__ == '__main__':

    #skimmedToyResultsPath = "toyResults_MC16adeV2"
    #skimmedToyResultsPath = "toyResults_MC16aV2"
    #skimmedToyResultsPath = "mc16adeToyResultsV5.23"
    #skimmedToyResultsPath = "mc16adeToyResultsV5.24"
    #skimmedToyResultsPath = "mc16adeToyResultsV5.25"
    skimmedToyResultsPath = "mc16adeToyResultsV6.30"

    

    outputFileName = skimmedToyResultsPath +".root"


    limitType = "gridToys"

    skimmedToyResults = os.listdir(skimmedToyResultsPath)


    bestEstimateDict   = collections.defaultdict(list)
    upperLimits1SigDict = collections.defaultdict(list)
    upperLimits2SigDict = collections.defaultdict(list)
    lowLimits1SigDict = collections.defaultdict(list)
    lowLimits2SigDict = collections.defaultdict(list)


    observedLimitGraph    = graphHelper.createNamedTGraphAsymmErrors("observedLimitGraph")
    expectedLimitsGraph_1Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_1Sigma")
    expectedLimitsGraph_2Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_2Sigma")


    for toyResultFile in  skimmedToyResults:

        mass = re.search("\d\d",toyResultFile).group()
        massPoint = int(mass)

        toyResultTFile = ROOT.TFile(os.path.join(skimmedToyResultsPath,toyResultFile),"OPEN")

        hypoTestInvResult = toyResultTFile.Get("result_mu")

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        likelihoodLimit_observed      = limitSetting.translateLimits( hypoTestInvResult, nSigmas = 1 ,getObservedAsymptotic = True)

        likelihoodLimit_1sig      = limitSetting.translateLimits( hypoTestInvResult, nSigmas = 1 )
        likelihoodLimit_2Sig = limitSetting.translateLimits( hypoTestInvResult, nSigmas = 2 )

        print(mass)
        likelihoodLimit_observed.Print()


        bestEstimateDict[mass].append( likelihoodLimit_observed.getVal() )
        upperLimits1SigDict[mass].append(likelihoodLimit_1sig.getMax())
        upperLimits2SigDict[mass].append(likelihoodLimit_2Sig.getMax())
        lowLimits1SigDict[mass].append(likelihoodLimit_1sig.getMin())
        lowLimits2SigDict[mass].append(likelihoodLimit_2Sig.getMin())


        graphHelper.fillTGraphWithRooRealVar(observedLimitGraph, massPoint, likelihoodLimit_observed)
        graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_1Sigma, massPoint, likelihoodLimit_1sig)
        graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_2Sigma, massPoint, likelihoodLimit_2Sig)






    writeTFile = ROOT.TFile( outputFileName,  "RECREATE")# "UPDATE")
    writeTFile.cd()
    bestEstimatesTTree   = fillTTreeWithDictOfList(bestEstimateDict, treeName = "bestEstimates_"+limitType)
    upperLimits1SigTTree = fillTTreeWithDictOfList(upperLimits1SigDict, treeName = "upperLimits1Sig_"+limitType)
    upperLimits2SigTTree = fillTTreeWithDictOfList(upperLimits2SigDict, treeName = "upperLimits2Sig_"+limitType)

    lowLimits1SigTTree = fillTTreeWithDictOfList(lowLimits1SigDict, treeName = "lowLimits1Sig_"+limitType)
    lowLimits2SigTTree = fillTTreeWithDictOfList(lowLimits2SigDict, treeName = "lowLimits2Sig_"+limitType)


    observedLimitGraph.Write()
    expectedLimitsGraph_1Sigma.Write()
    expectedLimitsGraph_2Sigma.Write()

    
    writeTFile.Write()

    writeTFile.Close()








    print("All Done!")
    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

