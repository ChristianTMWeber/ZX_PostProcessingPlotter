import ROOT
import re
import math


import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.RootTools as RootTools

def makeOutlierPMGWeightPlot( TTree, PMGWeightName , cut = None, cutString = ""):

    minVal = math.floor(TTree.GetMinimum(PMGWeightName))
    maxVal = math.ceil( TTree.GetMaximum(PMGWeightName))

    binSize = 50

    nBins = int(round((maxVal-minVal)/binSize))

    if nBins < 10: nBins = int(maxVal-minVal)

    #import pdb; pdb.set_trace()   ## enter here with the debugger

    histName = re.sub("PMGWeight_","",PMGWeightName) + cutString

    hist = ROOT.TH1F( histName ,histName , nBins, minVal, maxVal  )

    canv = ROOT.TCanvas()
    canv.SetLogy()

    if cut is None: TTree.Draw( PMGWeightName + " >> " +histName)
    else:           TTree.Draw( PMGWeightName + " >> " +histName, cut)

    hist.GetYaxis().SetRangeUser(0.1, hist.GetMaximum() * 1.5)


    canv.Update()


    canv.Print( PMGWeightName + cutString + ".pdf" )
    canv.Print( PMGWeightName + cutString + ".root" )
    canv.Print( PMGWeightName + cutString + ".png" )
    #import pdb; pdb.set_trace()   ## enter here with the debugger


    return hist



if __name__ == '__main__':

    ROOT.gROOT.SetBatch(True)


    file = ROOT.TFile("post_20201229_215858__ZX_Run2_Jul2020_ZZ_364251_QCDWeightsMinitree.root","OPEN")

    TTree = file.Get("t_ZXTree")


    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR0.5_MUF0.5_PDF261000 > 1500", dtype=long)
    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR0.5_MUF1_PDF261000 > 1500", dtype=long)
    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR1_MUF0.5_PDF261000 < -210", dtype=long)
    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR1_MUF2_PDF261000 >320", dtype=long)
    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR2_MUF1_PDF261000 < -1000", dtype=long)
    RootTools.GetValuesFromTree(TTree, "eventNumber" , cut = "PMGWeight_MUR2_MUF2_PDF261000 < -1000 ", dtype=long)

    import pdb; pdb.set_trace()   ## enter here with the debugger


    #TTree.Draw( "llll_m4l", "llll_m4l > 115000 && llll_m4l < 130000 ")
    #import pdb; pdb.set_trace()   ## enter here with the debugger

    #pmgWeightNames = [ "weight"]

    pmgWeightNames = [ "PMGWeight_MUR0.5_MUF0.5_PDF261000", "PMGWeight_MUR0.5_MUF1_PDF261000", "PMGWeight_MUR1_MUF0.5_PDF261000",
                       "PMGWeight_MUR1_MUF2_PDF261000",     "PMGWeight_MUR2_MUF1_PDF261000",   "PMGWeight_MUR2_MUF2_PDF261000" , "weight"]

    for pmgWeightName in pmgWeightNames:

        print pmgWeightName

        makeOutlierPMGWeightPlot( TTree, pmgWeightName )
        makeOutlierPMGWeightPlot( TTree, pmgWeightName , cut = "llll_m4l > 115000 && llll_m4l < 130000 ", cutString = "_HiggsWindow")
        makeOutlierPMGWeightPlot( TTree, pmgWeightName , cut = "llll_m4l > 115000 && llll_m4l < 130000 && llll_m34 > 26000 && llll_m34 < 27000", cutString = "_HiggsWindow_m34[26,27]")


    #import pdb; pdb.set_trace()   ## enter here with the debugger

