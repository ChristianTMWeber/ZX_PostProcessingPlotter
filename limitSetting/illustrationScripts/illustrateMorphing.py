import ROOT

import numpy as np

import sys 
from os import path

sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import histHelper

sys.path.append( path.dirname(  path.dirname( path.abspath(__file__) ) ) )  # need to append the parent directory here explicitly to be able to import rootDictAndTDirTools

import functions.rootDictAndTDirTools as rootDictAndTDirTools

import RooIntegralMorphWrapper as integralMorphWrapper
import functions.histHelper as histHelper # to help me fill some histograms


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

if __name__ == '__main__':

    #ROOT.gROOT.SetBatch(True)

    sourceFileName = "../preppedHists_mc16ade_sqrtErros_0.5GeVBins.root"

    sourceTFile = ROOT.TFile(sourceFileName, "OPEN")

    region = "ZXSR"
    eventType = "H4l"
    flavor = "All"

    AA = [region,eventType, "Nominal", flavor]

    getHist = lambda variation : rootDictAndTDirTools.TDirToList( sourceTFile.Get( "/".join([region,eventType, variation, flavor] ) ) )[0]



    nominalHist = getHist("Nominal")
    upHist = getHist("EL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up")
    downHist = getHist("EL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1down")

    for hist in [nominalHist, upHist, downHist]: hist.Rebin(4)




    canvIputs = ROOT.TCanvas("canvIputs","canvIputs")
    nominalHist.Draw()
    upHist.Draw("same")
    downHist.Draw("same")
    canvIputs.Update()



    histDict = {}

    histDict[-1] = downHist # add from low to high

    yBinWidth = 0.25

    for x in np.arange(-0.9, 0 , yBinWidth): 
        morphedHist = integralMorphWrapper.getInterpolatedHistogram(downHist, nominalHist,  paramA = -1 , paramB = 0, interpolateAt = x, morphErrorsToo = False)
        histDict[x] = morphedHist

    histDict[ 0] = nominalHist

    for x in np.arange(0.1, 1 , yBinWidth): 
        morphedHist = integralMorphWrapper.getInterpolatedHistogram(nominalHist, upHist,  paramA = 0 , paramB = +1, interpolateAt = x, morphErrorsToo = False)
        histDict[x] = morphedHist

    histDict[+1] = upHist


    nBinsX = nominalHist.GetNbinsX()
    lowLimitX  = nominalHist.GetBinLowEdge(1)
    highLimitX = nominalHist.GetBinLowEdge(nBinsX+1)


    lowLimitY = -1
    highLimitY = 1 + yBinWidth
    nBinsY = int( (highLimitY - lowLimitY)/yBinWidth )


    morphOverviewTH2 = ROOT.TH2D("morphOverview", "H4l systematic: EL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__", nBinsX, lowLimitX, highLimitX, nBinsY , lowLimitY - yBinWidth/2, highLimitY - yBinWidth/2 )
    morphOverviewTH2.GetXaxis().SetRange(morphOverviewTH2.GetXaxis().FindBin(10),morphOverviewTH2.GetXaxis().FindBin(61))

    morphOverviewTH2.GetXaxis().SetTitle("m_{34} , " + str(morphOverviewTH2.GetXaxis().GetBinWidth(1) )+" GeV bin-width" )
    #morphOverviewTH2.GetXaxis().SetTitleSize(0.05)
    morphOverviewTH2.GetXaxis().SetTitleOffset(2.)
    morphOverviewTH2.GetXaxis().CenterTitle()


    morphOverviewTH2.GetYaxis().SetTitle("systematic strength #alpha" )
    morphOverviewTH2.GetYaxis().SetTitleOffset(2.)
    morphOverviewTH2.GetYaxis().CenterTitle()

    morphOverviewTH2.GetZaxis().SetTitle("#Events" )
    #morphOverviewTH2.GetZaxis().SetTitleOffset(2.)
    morphOverviewTH2.GetZaxis().CenterTitle()

    for key in histDict:     histHelper.fillTH2SliceWithTH1(morphOverviewTH2,  histDict[key], key )

    morphOverviewTH2.SetStats( False) # remove stats box




    morphCanvas = ROOT.TCanvas("EL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__","EL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__", 2560/2, 1080)
    morphOverviewTH2.Draw("LEGO1")
    morphCanvas.Update()

    #morphCanvas.Print("test.png")

    morphOverviewTH2.GetYaxis().GetBinWidth(1)
    morphOverviewTH2.GetYaxis().GetBinLowEdge(1)

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here