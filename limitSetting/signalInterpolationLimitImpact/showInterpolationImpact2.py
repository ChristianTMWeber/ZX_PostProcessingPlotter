

#   There might be an systematic uncertainty associated with the norm of the reducible background
#   We estimate this uncertainty to be <= 10%
#   So I calculted some expected limits on the ZZd cross section with the nominal reducible background normalization
#   And with the normalization set to 120% of nominal
#   This script serves to visualize the impact of that change of norm
#
#




import ROOT


import sys 
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

    refTFile = ROOT.TFile("preppedHists_interpolatedResults_simulateErrors100_asymptoticLimits.root","OPEN")  # results with best estimate H4l reducible norm

    upTFile = ROOT.TFile("interpolationClosure_InterpolatedResults_asymptotic.root","OPEN")   # resutls with reducible normalized to 120% of best estimate value, i.e. +20%



    refGraph = refTFile.Get("expectedLimits_1Sigma")
    upGraph  = upTFile.Get("expectedLimits_1Sigma")

    refGraphNoError = graphHelper.getTGraphWithoutError(refGraph)
    upGraphNoError  = graphHelper.getTGraphWithoutError(upGraph)









    ratioCanvas = ROOT.TCanvas("ratioReducibles", "ratioReducibles")

    ratioCanvas.SetGridy()

    ratioTGraph = ratioOfTGraphs(upGraph, refGraph)

    # set label options, do it with ratioTGraph, as we will plot that one first



    titleStr = "ratio of expected limits [unitless]"

    ratioTGraph.GetYaxis().SetTitle(titleStr)
    ratioTGraph.GetYaxis().SetTitleSize(0.05)
    ratioTGraph.GetYaxis().SetTitleOffset(0.8)
    ratioTGraph.GetYaxis().CenterTitle()
    ratioTGraph.GetYaxis().SetRangeUser(0.997,1.001)

    ratioTGraph.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE

    ratioTGraph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    ratioTGraph.GetXaxis().SetTitleSize(0.05)
    ratioTGraph.GetXaxis().SetTitleOffset(0.86)

    # #sigma_{ZZ_{d}} with nominal reducible estimate /#sigma_{ZZ_{d}} with 1.2 #upoint reducible estimate
    ratioTGraph.SetTitle("")
    ratioTGraph.SetLineWidth(2)
    ratioTGraph.SetMarkerStyle(20)
    ratioTGraph.Draw()
    ratioCanvas.Update()


    #import pdb; pdb.set_trace() # import the debugger and instruct 




    canv = ROOT.TCanvas("compareReducibles", "compareReducibles", 1920, 1080)

    colorScheme = ROOT.kGreen

    # set label options, do it with refGraph, as we will plot that one first
    refGraph.GetYaxis().SetTitle("Expeted upper 95% CL on #sigma_{ZZ_{d}} [fb] ")
    refGraph.GetYaxis().SetTitleSize(0.05)
    refGraph.GetYaxis().SetTitleOffset(0.8)
    refGraph.GetYaxis().CenterTitle()

    refGraph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    refGraph.GetXaxis().SetTitleSize(0.05)
    refGraph.GetXaxis().SetTitleOffset(0.85)
    #refGraph.GetXaxis().CenterTitle()

    refGraph.SetFillColorAlpha(ROOT.kGreen-9, 0.5)
    refGraph.Draw("A3")

    upGraph.SetFillColorAlpha(ROOT.kBlue-9, 0.5)
    upGraph.Draw("3 SAME")

    refGraphNoError.SetLineColor(ROOT.kGreen)
    refGraphNoError.SetLineWidth(2)
    refGraphNoError.SetMarkerStyle(20)
    refGraphNoError.SetMarkerColor(ROOT.kGreen)
    refGraphNoError.Draw("SAME PL")

    upGraphNoError.SetLineColor(ROOT.kBlue)
    upGraphNoError.SetLineWidth(2)
    upGraphNoError.SetMarkerStyle(21)
    upGraphNoError.SetMarkerColor(ROOT.kBlue)
    upGraphNoError.Draw("SAME PL")


    legend = setupTLegend()
    legend.AddEntry(refGraphNoError , "expected limit, interpolated signal templates, toy errors"  , "l");
    legend.AddEntry(refGraph , "#pm1 #sigma error"  , "f");
    legend.AddEntry(upGraphNoError , "expected limit, interpolated signal templates, interpolated error bars"  , "l");
    
    legend.AddEntry(upGraph , "#pm1 #sigma error"  , "f");    

    legend.Draw()

    canv.Update()

    canv.Print("compare_2.pdf")

    #canv.Print("compareReducibles.pdf")
    import pdb; pdb.set_trace() # import the debugger and instruct 
