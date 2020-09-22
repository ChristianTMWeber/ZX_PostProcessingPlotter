import ROOT

import collections
import re
import numpy as np

# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.rootDictAndTDirTools as TDirTools
import functions.histNumpyTools as histNumpyTools
import functions.histHelper as histHelper


def makeReducibleShapeVariationProxy(hist, skewAroundBin = None , leftPartScale = .5):



    if skewAroundBin is None:  

        cumulativeHist = hist.GetCumulative() 

        skewAroundBin = cumulativeHist.FindFirstBinAbove( hist.Integral()/2 ) -1



    rightPartScale = ( hist.Integral() - leftPartScale * hist.Integral(1,skewAroundBin) ) / hist.Integral(skewAroundBin+1,  hist.GetNbinsX() )  

    for binNr in xrange(1,hist.GetNbinsX()+1): 

        if binNr <= skewAroundBin: scale = leftPartScale
        else:                      scale = rightPartScale

        hist.SetBinContent( binNr, hist.GetBinContent(binNr) * scale )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return hist

def makePlot( histList , titleString = "overviewPLot"):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.5; yOffset = 0.4
        xWidth  = 0.4; ywidth = 0.3
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    colors = [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen ]
    lineStyles = [ ROOT.kSolid , ROOT.kDashed, ROOT.kDotted , ROOT.kDashDotted ]  

    canvas = ROOT.TCanvas( titleString, titleString , int(1920 / 2.**0.5) , int(1080 / 2.**0.5)  )

    legend = setupTLegend()

    counter = 0

    histMaxima = [ hist.GetMaximum() for hist in histList ]

    for hist in histList:

        hist.SetTitle(titleString)

        hist.SetLineColor( colors[counter]  )
        hist.SetLineStyle( lineStyles[counter] )
        hist.SetLineWidth( 2 )

        hist.GetYaxis().SetRangeUser( 0 , max( histMaxima ) * 1.1 )

        hist.Draw( "same HIST" )

        legend.AddEntry(hist , hist.GetName() + ", yield = %.2f"%hist.Integral() , "l");

        counter +=1

    legend.Draw()
    canvas.Update()

    canvas.Print(titleString + ".png")
    canvas.Print(titleString + ".pdf")
    canvas.Print(titleString + ".root")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return None


if __name__ == '__main__':


    inputFileName = "post_20200809_203927_ZX_Run2_BckgSignal_PreppedHist_PMGWeights_V4.root"

    myFile = ROOT.TFile(inputFileName, "OPEN")


    masterHistDict = TDirTools.buildDictTreeFromTDir(myFile)

    newMasterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) 


    for channel in masterHistDict.keys():
        for eventType in masterHistDict[channel]: 
            for systematic in masterHistDict[channel][eventType]:
                for flavor in masterHistDict[channel][eventType][systematic].keys():

                    hist = masterHistDict[channel][eventType][systematic][flavor]

                    nBinsX = hist.GetNbinsX()

                    xMin = hist.GetBinLowEdge(1)
                    xMax = hist.GetBinLowEdge(nBinsX+1)

                    nBinsY = 1

                    hist2d = ROOT.TH2F(hist.GetName(), hist.GetTitle(), nBinsX, xMin, xMax, nBinsY, 0, 2 )
                    hist2d.GetXaxis().GetBinUpEdge(1)

                    for xBinNr in xrange(1, nBinsX +1): 
                        binContent = hist.GetBinContent(xBinNr)
                        binError   = hist.GetBinError(xBinNr)
                        for yBinNr in xrange(1, nBinsY +1): 
                            hist2d.SetBinContent(xBinNr, yBinNr, binContent )
                            hist2d.SetBinError(xBinNr, yBinNr, binContent )

                    newMasterHistDict[channel][eventType][systematic][flavor] = hist2d

    # plot1dHist =  masterHistDict["ZXSR"]["expectedData"]["Nominal"]["All"] 
    # plot1dHist.Draw()
    #
    # plot2dHist =  newMasterHistDict["ZXSR"]["expectedData"]["Nominal"]["All"]
    # plot2dHist.GetXaxis().SetRange(int(xMin), int(xMax))
    # plot2dHist.Draw("Lego")

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    TDirTools.writeDictTreeToRootFile( newMasterHistDict, targetFilename = re.sub(".root", "_fakeTH2s.root", inputFileName) )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here