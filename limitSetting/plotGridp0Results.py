

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

    p0Graph.SetLineWidth(2)
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

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    for mass in sorted(p0Dict.keys()):     
        p0Value = p0Dict[mass]

        signifianceValue = p0ToSignificane( p0Value )

        print( mass, p0Value, signifianceValue)

        

        if p0Value == 0: continue


        graphHelper.fillTGraphWithRooRealVar(p0Graph , mass, p0Dict[mass])

    sigmaGraphLimits = [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()]

    graph_1Sigma = getNSigmaGraph( 1, [p0Graph.GetXaxis().GetXmin(),p0Graph.GetXaxis().GetXmax()])
    graph_2Sigma = getNSigmaGraph( 2, p0Dict.keys())
    graph_3Sigma = getNSigmaGraph( 2.9, p0Dict.keys())

    
    graph_2Sigma.GetYaxis().SetTitle("Local p_{0}")
    graph_2Sigma.GetXaxis().SetTitle("m_{X} [GeV]")
    graph_2Sigma.GetYaxis().SetTitleSize(0.06)
    graph_2Sigma.GetXaxis().SetTitleSize(0.05)
    graph_2Sigma.GetYaxis().SetTitleOffset(0.8)
    graph_2Sigma.GetXaxis().SetTitleOffset(0.85)
    graph_2Sigma.GetXaxis().SetRangeUser(min(p0Dict.keys()),max(p0Dict.keys()))



    #p0Graph.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    #p0Graph.SetLineWidth(2)

    canv =  ROOT.TCanvas("GraphOverview", "GraphOverview",int(720*1.47), 720) #,1920/1, 1080)
    canv.SetLogy()
    canv.SetLeftMargin(0.15)
    #canv.SetBottomMargin(0.1)


    #graph_3Sigma.Draw()
    graph_2Sigma.Draw()
    graph_1Sigma.Draw("same")

    

    p0Graph.Draw("same * L")
    


    canv.Update()

    canv.Print("p0Graph_20kToys.pdf")
    canv.Print("p0Graph_20kToys.png")
    canv.Print("p0Graph_20kToys.root")





    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
