

#   There might be an systematic uncertainty associated with the norm of the reducible background
#   We estimate this uncertainty to be <= 10%
#   So I calculted some expected limits on the ZZd cross section with the nominal reducible background normalization
#   And with the normalization set to 120% of nominal
#   This script serves to visualize the impact of that change of norm
#
#




import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly


import sys 
import os
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess


import functions.tGraphHelpers as graphHelper

def ratioOfTGraphs(numeratorGraph, denominatorGraph):

    nPoints = numeratorGraph.GetN()

    ratioGraph = ROOT.TGraph()



    xCopy =ROOT.Double() # use these for pass by reference
    yNumCopy = ROOT.Double() # use these for pass by reference
    yDenomCopy = ROOT.Double() # use these for pass by reference


    for n in xrange(0, numeratorGraph.GetN() ): 

        numeratorGraph.GetPoint(n,   xCopy, yNumCopy)
        denominatorGraph.GetPoint(n, xCopy, yDenomCopy)

        ratioGraph.SetPoint(n,xCopy, yNumCopy / yDenomCopy)


    return ratioGraph


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    xOffset = 0.4; yOffset = 0.6
    xWidth  = 0.5; ywidth = 0.3
    TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border
    return TLegend


if __name__ == '__main__':



    referenceGraph = {"fileName"     : "interpolationClosure_ReferenceResults_asymptotic.root", 
                      "color"        : ROOT.kRed, 
                      "legend"       : "simulated signal templates",
                      "fileNamePart" : "SimulatedSignal"}

    comparisonGraphs = collections.defaultdict(dict)

    comparisonGraphs["interpolatedSignal"] = {
                          "fileName"     : "interpolationClosure_InterpolatedResults_asymptotic.root", 
                          "color"        : ROOT.kBlue, 
                          "legend"       : "interpolated signal templates",
                          "fileNamePart" : "interpolatedSignal"} 

    comparisonGraphs["interpolatedSignalToyErrors"] = {
                          "fileName"     : "preppedHists_interpolatedResults_simulateErrors100_asymptoticLimits.root", 
                          "color"        : ROOT.kOrange, 
                          "legend"       : "interpolated signal templates, toy errors",
                          "fileNamePart" : "interpolatedSignalToyErros"} 

    comparisonGraphs["interpolatedSignalSimulatedNorm"] = {
                          "fileName"     : "interpolationClosure_InterpolatedResults_WithSimulatedNorms_asymptotic.root", 
                          "color"        : ROOT.kMagenta+2, 
                          "legend"       : "interpolated signal templates, norms from simulation",
                          "fileNamePart" : "interpolatedSignalSimulatedNorm"} 

    comparisonGraphs["interpolatedSignalNewMorph"] = {
                          "fileName"     : "interpolationClosure_InterpolatedResults_newMorphInterface_asymptotic.root", 
                          "color"        : ROOT.kCyan, 
                          "legend"       : "interpolated signal templates, new morph implementation, spline interpolation for norm",
                          "fileNamePart" : "interpolatedSignalNewMorph"} 

    comparisonGraphs["interpolatedSignalNewMorphLinearNormInterp"] = {
                          "fileName"     : "interpolationClosure_morph1SigmaHists_multiPDFMorph_linearNorm_asymptotic.root", 
                          "color"        : ROOT.kGreen+1, 
                          "legend"       : "interpolated signal templates, new morph implementation, linear norm interp",
                          "fileNamePart" : "interpolatedSignalNewMorphLinearNorm"} 

    canv = ROOT.TCanvas("compareReducibles", "compareReducibles", 1920, 1080)
    legend = setupTLegend()

    keepInScopeArray = []

    refTFile = ROOT.TFile(referenceGraph["fileName"],"OPEN")  # results with best estimate H4l reducible norm
    refGraph = refTFile.Get("expectedLimits_1Sigma")
    keepInScopeArray.append(refGraph)

    refGraphNoError = graphHelper.getTGraphWithoutError(refGraph)


    # set label options, do it with refGraph, as we will plot that one first
    refGraph.GetYaxis().SetTitle("Expeted upper 95% CL on #sigma_{ZZ_{d}} [fb] ")
    refGraph.GetYaxis().SetTitleSize(0.05)
    refGraph.GetYaxis().SetTitleOffset(0.8)
    refGraph.GetYaxis().CenterTitle()

    refGraph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    refGraph.GetXaxis().SetTitleSize(0.05)
    refGraph.GetXaxis().SetTitleOffset(0.85)
    #refGraph.GetXaxis().CenterTitle()

    refGraph.SetFillColorAlpha(referenceGraph["color"]-9, 0.5)
    refGraph.Draw("A3 SAME")



    refGraphNoError.SetLineColor(referenceGraph["color"])
    refGraphNoError.SetLineWidth(3)
    refGraphNoError.SetMarkerSize(2)
    refGraphNoError.SetMarkerStyle(20)
    refGraphNoError.SetMarkerColor(referenceGraph["color"])
    refGraphNoError.Draw("SAME PL")

    legend.AddEntry(refGraphNoError , referenceGraph["legend"]  , "lf");
    #legend.AddEntry(refGraph , "#pm1 #sigma error"  , "f");


    listOfComparisonGraphs = [ "interpolatedSignal",
                               "interpolatedSignalSimulatedNorm",
                               "interpolatedSignalNewMorphLinearNormInterp",
                               "interpolatedSignalNewMorph"
                               ]

    #for comparisonLimit in comparisonGraphs:

    plotCounter = 0
    for comparisonLimit in listOfComparisonGraphs:

        plotCounter += 1

        print(plotCounter)


        upTFile = ROOT.TFile(comparisonGraphs[comparisonLimit]["fileName"],"OPEN")   # resutls with reducible normalized to 120% of best estimate value, i.e. +20%



        upGraph  = upTFile.Get("expectedLimits_1Sigma")


        keepInScopeArray.append(upGraph)


        upGraphNoError  = graphHelper.getTGraphWithoutError(upGraph)









        #ratioCanvas = ROOT.TCanvas("ratioReducibles", "ratioReducibles")
        #ratioCanvas.SetGridy()
        ratioTGraph = ratioOfTGraphs(upGraph, refGraph)

        # set label options, do it with ratioTGraph, as we will plot that one first



        titleStr = "ratio [unitless]"
        ratioTGraph.GetYaxis().SetTitle(titleStr)
        ratioTGraph.GetYaxis().SetTitleSize(0.05)
        ratioTGraph.GetYaxis().SetTitleOffset(0.8)
        ratioTGraph.GetYaxis().CenterTitle()
        ratioTGraph.GetYaxis().SetRangeUser(0.99,1.03)

        ratioTGraph.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE

        ratioTGraph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
        ratioTGraph.GetXaxis().SetTitleSize(0.05)
        ratioTGraph.GetXaxis().SetTitleOffset(0.85)

        ## #sigma_{ZZ_{d}} with nominal reducible estimate /#sigma_{ZZ_{d}} with 1.2 #upoint reducible estimate
        #ratioTGraph.SetTitle("#splitline{ratio of expected upper 95% CLs on #sigma_{ZZ_{d}}:}{ #sigma_{ZZ_{d}} with 1.2 #upoint reducible / #sigma_{ZZ_{d}} with 1.0 #upoint reducible}")
        #ratioTGraph.SetLineWidth(2)
        #ratioTGraph.Draw("same")
        #ratioCanvas.Update()


        #import pdb; pdb.set_trace() # import the debugger and instruct 






        colorScheme = ROOT.kRed



        upGraph.SetFillColorAlpha(comparisonGraphs[comparisonLimit]["color"]-9, 0.5)
        #upGraph.Draw("3 SAME")



        upGraphNoError.SetLineColor(comparisonGraphs[comparisonLimit]["color"])
        upGraphNoError.SetLineWidth(2)
        #upGraphNoError.SetMarkerSize(3)
        #upGraphNoError.SetMarkerStyle(21+plotCounter)
        upGraphNoError.SetLineStyle(plotCounter)
        upGraphNoError.SetMarkerColor(comparisonGraphs[comparisonLimit]["color"])
        upGraphNoError.Draw("SAME PL")

        
        keepInScopeArray.append(upGraphNoError)
        

        legend.AddEntry(upGraphNoError , comparisonGraphs[comparisonLimit]["legend"] , "lf");
        #legend.AddEntry(upGraph , "#pm1 #sigma error"  , "f");    

        legend.Draw()

        canv.Update()

        outputDir = "limitComparisons"

        if not path.exists(outputDir): os.mkdir(outputDir)

        outputFileName = path.join(outputDir , referenceGraph["fileNamePart"] +"_vs_"+comparisonGraphs[comparisonLimit]["fileNamePart"])

        outputFileName= "test_" + str(plotCounter)

        canv.Print(outputFileName+".pdf")
        canv.Print(outputFileName+".png")
        canv.Print(outputFileName+".root")
        #import pdb; pdb.set_trace() # import the debugger and instruct 

    #canv.Print("compareReducibles.pdf")
    import pdb; pdb.set_trace() # import the debugger and instruct 
