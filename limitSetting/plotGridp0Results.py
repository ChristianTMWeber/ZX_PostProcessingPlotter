

import ROOT


import re
import os

import math


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper

from functions.rootDictAndTDirTools import getTDirContentNames


def getP0ValueFromFile( filePath ):

    TFile = ROOT.TFile(filePath , "OPEN")
    #TFile.Get("HypoTestCalculator_result;1").Print()


    TFileContents = getTDirContentNames(TFile)

    nHypoTestResults = TFileContents.count("HypoTestCalculator_result")

    HypoTestCalculatorResult = TFile.Get("HypoTestCalculator_result;1")

    for iterator in xrange(2,nHypoTestResults+1):  # in case we have more then one HypoTestCalculator_result in the given file
        tempHypoTestCalculatorResult = TFile.Get("HypoTestCalculator_result;" + str(iterator) )
        HypoTestCalculatorResult.Append( tempHypoTestCalculatorResult )

    p0Value = TFile.Get("HypoTestCalculator_result;1").NullPValue()

    TFile.Close()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return p0Value

def p0ToSignificane( inputP0 ): return ROOT.Math.gaussian_quantile_c ( inputP0, 1)

def significanceToP0( inputSignifiacne): return 1-ROOT.Math.normal_cdf ( inputSignifiacne , 1, 0)

def getNSigmaGraph( nSigma, xPoints):
    p0AtNSigma =  significanceToP0( nSigma)
    # inverse of the function above is: ROOT.Math.gaussian_quantile_c ( 1, p0AtNSigma)

    nSigmaGrpah = graphHelper.createNamedTGraph( "%.1f#sigma" %nSigma)

    for xVal in sorted(xPoints):  graphHelper.fillTGraphWithRooRealVar(nSigmaGrpah , xVal, p0AtNSigma)


    #nSigmaGrpah.SetLineStyle( int(round(nSigma)) +1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    nSigmaGrpah.SetLineStyle( 2) # https://root.cern.ch/doc/master/classTAttLine.html#L3

    #nSigmaGrpah.SetLineWidth(2)
    nSigmaGrpah.SetLineColor( ROOT.kRed)

    return nSigmaGrpah


def globalP0Estimate(p0Dict,  localp0Val, refSignifiance = 1):
    # following the asymptotic recommendation from https://twiki.cern.ch/twiki/bin/view/AtlasProtected/GlobalSignificanceComputations
    # based on E. Gross and O. Vitells, Eur. Phys. J. C70 (2010) 525-530: https://arxiv.org/abs/1005.1891

    refP0 = significanceToP0( refSignifiance )

    localSignificance = p0ToSignificane(localp0Val)


    # make list of p0 values that is properly sorted
    p0List = []
    for mass in sorted(p0Dict.keys()):     p0List.append( p0Dict[mass])


    # measure nUp
    nUp = 0
    for x in range( len(p0List)-1): 
        leftP0Value  = p0Dict.values()[x]
        rightP0Value = p0Dict.values()[x+1]

        # increase nUp if the p0 graph crosses refP0 from up to down
        if leftP0Value > refP0 and rightP0Value < refP0: nUp+=1 



    globalP0 = localp0Val + nUp * math.exp(  -0.5 * (localSignificance**2 - refSignifiance**2 ))
    
    globalP0Error = nUp**0.5 * math.exp(  -0.5 * (localSignificance**2 - refSignifiance**2 ))

    return globalP0, globalP0Error

def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None

def addATLASBlurp(boundaries = (0.5,0.57,0.9,0.67)):

    activateATLASPlotStyle()
    statsTexts = []

    statsTexts.append( "#font[72]{ATLAS} Internal")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.0f fb^{-1}" %( 139. ) ) 
    statsTexts.append( "ZX significances") # https://root.cern/doc/master/classTAttText.html#T1


    statsTPave=ROOT.TPaveText(boundaries[0],boundaries[1],boundaries[2],boundaries[3],"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);
    statsTPave.Draw();

    return statsTPave

def setupTLegend( nColumns = 2, boundaries = (0.15,0.70,0.55,0.95)):
    # set up a TLegend, still need to add the different entries
    # boundaries = (lowLimit X, lowLimit Y, highLimit X, highLimit Y)

    TLegend = ROOT.TLegend(boundaries[0],boundaries[1],boundaries[2],boundaries[3])
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(nColumns);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend

if __name__ == '__main__':

    #folderWithGridP0Results = "gridP0Calculations"

    folderWithGridP0Results = "user.chweber.ZdZdp0_ZX_Workspace_mZd_XXGeV.42.000000_p0"

    #               look behind                        look ahead
    searchString = "(?<=ZdZdp0_ZX_Workspace_mZd_)\d{2}(?=GeV.)" 


    
    p0Dict = {} # mass : p0 value 

    p0Graph = graphHelper.createNamedTGraph( "p0Graph")

    p0Graph.GetYaxis().SetTitle("")

    p0Graph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")


    for root, dirs, files in os.walk(folderWithGridP0Results, topdown=False):         
        for file in files: 
            filePath = os.path.join(root, file)

            regexMatch = re.search(searchString  , filePath)

            if regexMatch : 
                mass = int(regexMatch.group())

                p0Dict[mass] = getP0ValueFromFile( filePath )
                

    globalP0Value = globalP0Estimate(p0Dict, min(p0Dict.values()) , refSignifiance = 1)

    globalP0Value = globalP0Estimate(p0Dict, min(p0Dict.values()) , refSignifiance = 0)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    for mass in sorted(p0Dict.keys()):     
        p0Value = p0Dict[mass]

        signifianceValue = p0ToSignificane( p0Value )

        #print( mass, p0Value, signifianceValue)

        if p0Value == 0: continue


        graphHelper.fillTGraphWithRooRealVar(p0Graph , mass, p0Dict[mass])

    sigmaGraphLimits = [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()]

    graph_1Sigma = getNSigmaGraph( 1, [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()])
    graph_2Sigma = getNSigmaGraph( 2, [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()])
    graph_3Sigma = getNSigmaGraph( 3, [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()])


    listOfAllGraphes = [graph_1Sigma, graph_2Sigma, graph_3Sigma, p0Graph]

    for graph in listOfAllGraphes:
        graph.GetYaxis().SetTitle("Local p_{0}")
        graph.GetXaxis().SetTitle("m_{X} [GeV]")
        graph.GetYaxis().SetTitleSize(0.06)
        graph.GetXaxis().SetTitleSize(0.05)
        graph.GetYaxis().SetTitleOffset(0.4)
        graph.GetXaxis().SetTitleOffset(0.85)
        graph.GetXaxis().SetRangeUser(min(p0Dict.keys()),max(p0Dict.keys()))
        graph.GetYaxis().SetRangeUser(1E-3,8)



    #p0Graph.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    #p0Graph.SetLineWidth(2)

    canv =  ROOT.TCanvas("GraphOverview", "GraphOverview",int(720*1.47), 720) #,1920/1, 1080)
    canv.SetLogy()
    canv.SetLeftMargin(0.10)
    #canv.SetBottomMargin(0.1)

    p0Graph.GetYaxis().SetRangeUser(1E-3,8)
    p0Graph.SetMarkerStyle(ROOT.kFullDotMedium)
    p0Graph.Draw("")

    graph_3Sigma.Draw("same")
    graph_2Sigma.Draw("same")
    graph_1Sigma.Draw("same")

    
    atlasBlurb = addATLASBlurp(boundaries = (0.01,0.78,0.5,0.88))

    legend = setupTLegend( nColumns = 1, boundaries = (0.6,0.80,0.9,0.85))
    legend.AddEntry(graph_1Sigma, "Local significance", "l")

    legend.Draw()

    latexText = ROOT.TLatex()
    #latexText.SetTextAlign(10)

    latexText.DrawLatex(45,significanceToP0( 1)+1E-2,"#scale[1]{#color[2]{1#sigma}}")
    latexText.DrawLatex(45,significanceToP0( 2)+1E-3,"#scale[1]{#color[2]{2#sigma}}")
    latexText.DrawLatex(45,significanceToP0( 3)+1E-4,"#scale[1]{#color[2]{3#sigma}}")

    canv.Update()

    canv.Print("p0Graph_20kToys.pdf")
    canv.Print("p0Graph_20kToys.png")
    canv.Print("p0Graph_20kToys.root")





    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
