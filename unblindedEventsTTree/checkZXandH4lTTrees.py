
import ROOT

import numpy as np


import sys 
from os import path

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.RootTools as RootTools


def setAsetBGetIntersection( setA, setB):

    if not isinstance(setA,set): setA = set(setA)
    if not isinstance(setB,set): setB = set(setB)

    onlyA = setA.difference(setB)
    onlyB = setB.difference(setA)
    commonToBoth = setA.intersection(setB)

    return sorted(list(onlyA)), sorted(list(onlyB)), sorted(list(commonToBoth))


def getTreeContents( Tree, variable, kinematicCuts, events = None) :

    if events is not None: 
        events = [ "event == %i"%x for x in events]
        kinematicCuts += " && ("+  " | ".join(events) +")"

    npArray =  RootTools.GetValuesFromTree(Tree, variable , cut = kinematicCuts, dtype=long)

    return npArray



def GetValuesFromTreeInChuncks(tree, variable,  flatten=True, nevents=None, dtype=float, forceMultidim=False,  cutElements = [""], cutConnector = "" , chunkSize = 10000):

    nCuts = len(cutElements)

    outputArray = np.array([],dtype = dtype)

    for chunkStart in xrange(0,nCuts,chunkSize): 

        cuts = cutConnector.join(cutElements[chunkStart : chunkStart+chunkSize])

        ttreeValues = RootTools.GetValuesFromTree(tree, variable, cut = cuts, flatten=flatten, nevents=nevents, dtype=float, forceMultidim=forceMultidim)

        outputArray =  np.append(outputArray, ttreeValues)

    return outputArray



def makeZXandH4lComparisonPlot( ZXValues, H4lValues , nBins = 100, nBinsAsResolution = False, 
    titleDict = {"xLabel" : "", "yLabel" : "", "title" : ""} ):


    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.12; yOffset = 0.8
        xWidth  = 0.2; ywidth = 0.1
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend


    allValues = np.append(ZXValues, H4lValues)

    lowerLimit = min( np.floor(allValues ))
    upperLimit = max( np.ceil(allValues ))


    if nBinsAsResolution: nBins = int((upperLimit - lowerLimit) / nBins)

    ZXHist = ROOT.TH1F( "ZXHist" , "ZXHist", nBins, lowerLimit, upperLimit)
    H4lHist = ROOT.TH1F( "H4lHist" , "H4lHist", nBins, lowerLimit, upperLimit)

    ZXHist.SetStats( False) # remove stats box
    ZXHist.GetYaxis().SetTitle(titleDict["yLabel"])
    ZXHist.GetXaxis().SetTitle(titleDict["xLabel"])
    ZXHist.SetTitle("")


    ZXHist.SetLineColor(ROOT.kBlue )
    H4lHist.SetLineColor(ROOT.kRed )


    ZXHist.SetLineWidth( 2 )
    H4lHist.SetLineWidth( 2 )

    H4lHist.SetLineStyle(ROOT.kDashed )



    for val in ZXValues: ZXHist.Fill(val,1)
    for val in H4lValues: H4lHist.Fill(val,1)

    histMaximumValue = max( ZXHist.GetMaximum(), H4lHist.GetMaximum())
    ZXHist.GetYaxis().SetRangeUser(0, histMaximumValue * 1.1)


    canvas = ROOT.TCanvas( "canvas", "canvas", 1280,720)

    ZXHist.SetTitle(titleDict["title"])
    #H4lHist.SetTitle("test2")
    ZXHist.Draw()
    H4lHist.Draw("same")



    legend = setupTLegend()
    legend.AddEntry(ZXHist  , "ZX, %i events"%ZXHist.Integral()  , "l");
    legend.AddEntry(H4lHist , "H4l, %i events"%H4lHist.Integral(), "l");

    legend.Draw()


    canvas.Update()

    canvas.Print(titleDict["title"]+".png")
    canvas.Print(titleDict["title"]+".pdf")


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None




if __name__ == '__main__':


    # get TTrees

    ZXTFile = ROOT.TFile("post_20201013_145100__ZX_Run2_Feb2020_UnblindedData_mc16ade_miniTree.root","OPEN")
    ZX_TTree = ZXTFile.Get("t_ZXTree")

    H4lFile = ROOT.TFile("data15-18_13TeV.periodD4-C.physics_Main.root","OPEN")
    H4l_TTree = H4lFile.Get("tree_incl_all")

    # get event numbers

    ZX_m4lVar = "llll_m4l"
    ZX_signalRegionCuts = ["%s > 115000" %ZX_m4lVar, "%s < 130000" %ZX_m4lVar] 
    ZX_eventNumbers= RootTools.GetValuesFromTree(ZX_TTree, "event", cut = " && ".join(ZX_signalRegionCuts), dtype=long)



         

 
    H4l_m4lVar = "m4l_fsr" # "m4l_constrained"
    H4l_signalRegionCuts = [ "%s > 115 " %H4l_m4lVar ,  "%s < 130"%H4l_m4lVar ]
    H4l_eventNubmers = RootTools.GetValuesFromTree(H4l_TTree, "event", cut = " && ".join(H4l_signalRegionCuts), dtype=long)


    eventNumbers_ZXalone , eventNumbers_H4lalone, eventNumbers_Common= setAsetBGetIntersection( ZX_eventNumbers, H4l_eventNubmers)




    ### Plot m4l ###
    ZX_targetVar = ZX_m4lVar
    H4l_targetVar = H4l_m4lVar


    ZX_m4l_common = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_common = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_common , H4l_m4l_common, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m4l", "yLabel" : "#events", "title" : "m4l ZX H4l signal region common"}  )


    ZX_m4l_ZXAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_ZXAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_ZXAlone , H4l_m4l_ZXAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m4l", "yLabel" : "#events", "title" : "m4l ZX H4l signal region ZX only"}  )


    ZX_m4l_H4lAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_H4lAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_H4lAlone , H4l_m4l_H4lAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m4l", "yLabel" : "#events", "title" : "m4l ZX H4l signal region H4l only"}  )



    ### Plot m12 ###

    ZX_targetVar = "llll_m12"
    H4l_targetVar = "mZ1_unconstrained"


    ZX_m4l_common = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_common = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_common , H4l_m4l_common, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m12", "yLabel" : "#events", "title" : "m12 ZX H4l signal region common"}  )


    ZX_m4l_ZXAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_ZXAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_ZXAlone , H4l_m4l_ZXAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m12", "yLabel" : "#events", "title" : "m12 ZX H4l signal region ZX only"}  )


    ZX_m4l_H4lAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_H4lAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_H4lAlone , H4l_m4l_H4lAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m12", "yLabel" : "#events", "title" : "m12 ZX H4l signal region H4l only"}  )



    ZX_targetVar = "llll_m34"
    H4l_targetVar = "mZ2_unconstrained"


    ZX_m4l_common = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_common = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_Common] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_common , H4l_m4l_common, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m34", "yLabel" : "#events", "title" : "m34 ZX H4l signal region common"}  )


    ZX_m4l_ZXAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_ZXAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_ZXalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_ZXAlone , H4l_m4l_ZXAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m34", "yLabel" : "#events", "title" : "m34 ZX H4l signal region ZX only"}  )


    ZX_m4l_H4lAlone = GetValuesFromTreeInChuncks(ZX_TTree, ZX_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)/1000
    H4l_m4l_H4lAlone = GetValuesFromTreeInChuncks(H4l_TTree, H4l_targetVar,  cutElements =  [ "event == %i"%x for x in eventNumbers_H4lalone] , cutConnector = "|" ,chunkSize = 100 , dtype=float)
    makeZXandH4lComparisonPlot( ZX_m4l_H4lAlone , H4l_m4l_H4lAlone, nBins = 1 , nBinsAsResolution = True, 
        titleDict = {"xLabel" : "m34", "yLabel" : "#events", "title" : "m34 ZX H4l signal region H4l only"}  )



    # get run numbers matched to the event numbers

    eventNumbers_ZXalone , eventNumbers_H4lalone, eventNumbers_Common

    runAndEventNumbers_ZXalone = []
    runAndEventNumbers_Common = []
    runAndEventNumbers_Common2 = []
    runAndEventNumbers_H4lalone = []

    for eventNumber in eventNumbers_ZXalone:
        runNumber = RootTools.GetValuesFromTree(ZX_TTree, "RunNumber", cut = "event == %i" %eventNumber,  dtype=long)
        runAndEventNumbers_ZXalone.append( (runNumber[0], eventNumber)   )

    for eventNumber in eventNumbers_Common:
        runNumber = RootTools.GetValuesFromTree(ZX_TTree, "RunNumber", cut = "event == %i" %eventNumber,  dtype=long)
        runAndEventNumbers_Common.append( (runNumber[0], eventNumber)   )
   
    for eventNumber in eventNumbers_Common:
        runNumber = RootTools.GetValuesFromTree(H4l_TTree, "run", cut = "event == %i" %eventNumber,  dtype=long)
        runAndEventNumbers_Common2.append( (runNumber[0], eventNumber)   )

    for eventNumber in eventNumbers_H4lalone:
        runNumber = RootTools.GetValuesFromTree(H4l_TTree, "run", cut = "event == %i" %eventNumber,  dtype=long)
        runAndEventNumbers_H4lalone.append( (runNumber[0], eventNumber)   )


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


