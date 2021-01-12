

import ROOT


import re
import os


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


def getNSigmaGraph( nSigma, xPoints):
    p0AtNSigma =  1-ROOT.Math.normal_cdf ( nSigma , 1, 0)

    nSigmaGrpah = graphHelper.createNamedTGraph( "%.1f#sigma" %nSigma)

    for xVal in sorted(xPoints):  graphHelper.fillTGraphWithRooRealVar(nSigmaGrpah , xVal, p0AtNSigma)


    #nSigmaGrpah.SetLineStyle( int(round(nSigma)) +1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    nSigmaGrpah.SetLineStyle( 2) # https://root.cern.ch/doc/master/classTAttLine.html#L3

    p0Graph.SetLineWidth(2)
    nSigmaGrpah.SetLineColor( ROOT.kRed)

    return nSigmaGrpah



if __name__ == '__main__':

    #folderWithGridP0Results = "gridP0Calculations"

    folderWithGridP0Results = "../../Downloads/gridP0CalculationsMoreStats"

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
                


    for mass in sorted(p0Dict.keys()):     
        p0Value = p0Dict[mass]

        if p0Value == 0: continue


        graphHelper.fillTGraphWithRooRealVar(p0Graph , mass, p0Dict[mass])

    graph_1Sigma = getNSigmaGraph( 1, p0Dict.keys())
    graph_2Sigma = getNSigmaGraph( 2, p0Dict.keys())
    graph_3Sigma = getNSigmaGraph( 2.9, p0Dict.keys())

    
    graph_3Sigma.GetYaxis().SetTitle("Local p_{0}")
    graph_3Sigma.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")

    graph_3Sigma.GetYaxis().SetTitleSize(0.06)

    graph_3Sigma.GetXaxis().SetTitleSize(0.05)
    graph_3Sigma.GetYaxis().SetTitleOffset(0.8)

    graph_3Sigma.GetXaxis().SetTitleOffset(0.85)



    #p0Graph.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    #p0Graph.SetLineWidth(2)

    canv =  ROOT.TCanvas("GraphOverview", "GraphOverview",1920/2, 1080)
    canv.SetLogy()
    canv.SetLeftMargin(0.15)
    #canv.SetBottomMargin(0.1)


    graph_3Sigma.Draw()
    graph_1Sigma.Draw("same")
    graph_2Sigma.Draw("same")
    

    p0Graph.Draw("same * L")
    


    canv.Update()

    canv.Print("p0Graph_2.5kToys.pdf")
    canv.Print("p0Graph_2.5kToys.png")





    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
