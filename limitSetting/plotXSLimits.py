
import ROOT
import numpy as np

import re

import math


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper
import functions.RootTools as RootTools

from functions.getArrayConfInterval import getArrayConfInterval

def makeGraphOverview( extractedLimit,  expectedLimit1Sig, expectedLimit2Sig , colorScheme = ROOT.kRed, writeTo = False):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.6; yOffset = 0.7
        xWidth  = 0.3; ywidth = 0.2
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    canv = ROOT.TCanvas("GraphOverview", "GraphOverview")
 

    expectedLimit2Sig.GetYaxis().SetTitle("95% CL on #sigma_{ZZ_{d}} [fb] ")
    expectedLimit2Sig.GetYaxis().SetTitleSize(0.06)
    expectedLimit2Sig.GetYaxis().SetTitleOffset(0.6)
    expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetXaxis().SetTitleOffset(0.85)
    #expectedLimit2Sig.GetXaxis().CenterTitle()

    expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
    #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit2Sig.Draw("A3") # use 'A' option only for first TGraph apparently

    #expectedLimit1Sig.SetFillColorAlpha(ROOT.kRed+1,0.5) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
    expectedLimit1Sig.SetFillColor(colorScheme-9)
    #expectedLimit1Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit1Sig.Draw("3 same")

    expectedLimitMedian = graphHelper.getTGraphWithoutError( expectedLimit1Sig  , ySetpoint = "median")

    expectedLimitMedian.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    expectedLimitMedian.SetLineWidth(2)
    expectedLimitMedian.SetLineColor(colorScheme)
    expectedLimitMedian.Draw("same")

    extractedLimit.SetLineStyle(1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    extractedLimit.SetLineWidth(2)
    extractedLimit.SetLineColor(colorScheme)
    extractedLimit.Draw("same")

    legend = setupTLegend()
    legend.AddEntry(extractedLimit , "observed Limit"  , "l");
    legend.AddEntry(expectedLimitMedian , "expected limit"  , "l");
    legend.AddEntry(expectedLimit1Sig , "#pm1#sigma expected limit"  , "f");
    legend.AddEntry(expectedLimit2Sig , "#pm2#sigma expected limit"  , "f");    

    legend.Draw()

    canv.Update() #"a3" also seems to work https://root.cern/doc/master/classTGraphPainter

    if writeTo: writeTo.cd(); canv.Write()

    return canv



def yieldBranchAndContent(TTree, cutAt = 10):


    for branch in TTree.GetListOfBranches():         
        
        varName =  branch.GetName() 
        cutString = varName + " < " + str(cutAt)

        arrayFromTTree = RootTools.GetValuesFromTree(TTree, varName, cutString)

        mass = int(re.search("\d{2}", varName).group())  # systematics

        yield mass, arrayFromTTree



def getMeanAndStdDictFromTTree(TTree, nSigma = 1, cutAt = 10):

    meanDict = {}
    stdDict = {}

    for mass, npArray in yieldBranchAndContent(TTree, cutAt = cutAt):

        meanDict[mass] =  np.mean( npArray )
        stdDict[mass]  =  np.std( npArray  ) * nSigma

    return meanDict, stdDict, stdDict

def getconfInterval(TTree,  nSigma = 1. , cutAt = 10):

    meanDict = {}
    errorLow = {}
    errorHigh = {}

    confidenceSetpoint = math.erf( float(nSigma) / 2.**0.5)

    for mass, npArray in yieldBranchAndContent(TTree, cutAt = cutAt):

        arrayMean = np.mean( npArray )


        lowLimit , highLimit = getArrayConfInterval( npArray, confidenceValue = confidenceSetpoint,  intervalCenter = arrayMean)
        meanDict[mass]   =  arrayMean
        errorLow[mass]   =  arrayMean - lowLimit
        errorHigh[mass]  =  highLimit - arrayMean

    return meanDict, errorLow, errorHigh



def getToyLimits( filename , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_1sigma" ,nSigma = 1, intervalType = "confInterval"):

    testFile = ROOT.TFile(filename)

    upperLimitTree1Sig = testFile.Get(TTreeName)

    
    if intervalType == "confInterval":
        mean, errorLow, errorHigh = getconfInterval(upperLimitTree1Sig, nSigma = nSigma , cutAt = 10)
    elif intervalType == "standardDeviation":
        mean, errorLow, errorHigh = getMeanAndStdDictFromTTree(upperLimitTree1Sig, nSigma = nSigma, cutAt = 10)


    toyLimitTGrapah = graphHelper.createNamedTGraphAsymmErrors("toyLimit_1sigma")

    for mass in sorted(mean.keys()):
        pointNr = toyLimitTGrapah.GetN()

        toyLimitTGrapah.SetPoint( pointNr, mass, mean[mass] )
        toyLimitTGrapah.SetPointError( pointNr, 0,0, errorLow[mass] , errorHigh[mass] )

    return toyLimitTGrapah





if __name__ == '__main__':

    testFile = ROOT.TFile("../allCombinedMC16a_1895.root")

    upperLimitTree1Sig = testFile.Get("upperLimits1Sig_toys")

    toyLimitTGrapah1Sigma = getToyLimits( "../allCombinedMC16a_1895.root" , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_1sigma", nSigma = 1, intervalType = "confInterval")
    toyLimitTGrapah2Sigma = getToyLimits( "../allCombinedMC16a_1895.root" , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_2sigma", nSigma = 2, intervalType = "confInterval")

    canvas = makeGraphOverview( toyLimitTGrapah1Sigma,  toyLimitTGrapah1Sigma, toyLimitTGrapah2Sigma , colorScheme = ROOT.kRed, writeTo = False)

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



