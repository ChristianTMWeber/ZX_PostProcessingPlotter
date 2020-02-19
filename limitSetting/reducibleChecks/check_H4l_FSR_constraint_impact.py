#
# Let's see what kind of impact the Final State Radiation (FSR) recovery and Z-mass constraint have on the m34 spectrum
#

import ROOT

import re

import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import files from parent directories

import functions.histHelper as histHelper # to help me with histograms


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.10,0.70,0.65,0.90)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend


def fillMZ2HistPair(aTTree, uncorrectedHist, ZConstrFSRHist, cutOn = ""):

    aTTree.Draw("mZ2_unconstrained >>" + uncorrectedHist.GetName(), cutOn)
    aTTree.Draw("mZ2_constrained   >>" + ZConstrFSRHist.GetName(), cutOn)

    return None

def getDSIDStr(sampleName): return re.search("\d{6}",sampleName ).group()

def prepHistograms(miniTreeName):

    if isinstance(miniTreeName, ROOT.TObject): miniTreeName = miniTreeName.GetName()

    DSID = getDSIDStr(miniTreeName)

    uncorrectedHist = ROOT.TH1D("uncorrectedHist_"+DSID, "uncorrectedHist_"+DSID, 100,0,10)
    uncorrectedHist.SetCanExtend(ROOT.TH1.kAllAxes)

    ZConstrFSRHist = uncorrectedHist.Clone("ZConstrFSRHist_"+DSID)

    uncorrectedHist_m4lAll = uncorrectedHist.Clone("uncorrectedHist_"+DSID +"_m4lAll")
    ZConstrFSRHist_m4lAll = uncorrectedHist.Clone("ZConstrFSRHist_"+DSID +"_m4lAll")

    return uncorrectedHist, ZConstrFSRHist, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll


def prepHistOptics(hist):

    if isinstance(hist,list): 
        for element in hist: prepHistOptics(element)
        return None

    #uncorrectedHist.SetFillStyle(3244)
    hist.SetMarkerColor(1)
    hist.GetYaxis().SetTitle("Events / " + str(hist.GetBinWidth(1) )+" GeV" )
    hist.GetYaxis().SetTitleSize(0.05)
    hist.GetYaxis().SetTitleOffset(1.)
    hist.GetYaxis().CenterTitle()
    hist.SetStats( False)
    hist.GetXaxis().SetTitle("m_{34} [GeV]")

    return None


def prepRatioHistOptics(ratioHist):

    ratioHist.SetMarkerColor(1)

    maxRatioVal , _ = histHelper.getMaxBin(ratioHist , useError = False, skipZeroBins = True)
    minRatioVal , _ = histHelper.getMinBin(ratioHist , useError = False, skipZeroBins = True)

    ratioHist.GetYaxis().SetRangeUser(minRatioVal * 0.99, maxRatioVal * 1.01)

    ratioHist.SetTitle("")
    
    ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
    ratioHist.GetYaxis().SetLabelSize(0.1)

    ratioHist.GetYaxis().SetTitle("FSR_ZConstrained / reference ")
    ratioHist.GetYaxis().SetTitleSize(0.08)
    ratioHist.GetYaxis().SetTitleOffset(0.6)
    ratioHist.GetYaxis().CenterTitle()

    ratioHist.SetMarkerStyle(8)
    ratioHist.SetStats( False)

    ratioHist.GetXaxis().SetLabelSize(0.12)
    ratioHist.GetXaxis().SetTitleSize(0.13)
    ratioHist.GetXaxis().SetTitleOffset(1.0)
    ratioHist.GetXaxis().SetTitle("m_{34} [GeV]")

    return None


def makeCanvasWithHistograms(uncorrectedHist, ZConstrFSRHist, canvasName = "canv"):

    canvas = ROOT.TCanvas(canvasName, canvasName,720,720)

    histPadYStart = 3.5/13
    histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
    histPad.Draw();              # Draw the upper pad: pad1
    histPad.cd();                # pad1 becomes the current pad

    uncorrectedHist.Draw("")
    ZConstrFSRHist.Draw("same P")


    legend = setupTLegend()
    legend.AddEntry(uncorrectedHist , "uncorrected m34" , "l");
    legend.AddEntry(ZConstrFSRHist , "FSR recovered and Z constrained" , "p");
    legend.Draw()

    canvas.cd()
    canvas.Update()


    ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);

    ratioPad.SetTopMargin(0.)
    ratioPad.SetBottomMargin(0.3)
    ratioPad.SetGridy(); #ratioPad.SetGridx(); 
    ratioPad.Draw();              # Draw the upper pad: pad1
    ratioPad.cd();                # pad1 becomes the current pad


    ratioHist = ZConstrFSRHist.Clone( ZConstrFSRHist.GetName()+"_Clone" )
    ratioHist.Divide(uncorrectedHist)

    prepRatioHistOptics(ratioHist)

    ratioHist.Draw("P")

    canvas.Update()

    outDict = { "canvas" : canvas, "histPad" : histPad, "ratioPad" : ratioPad, "ratioHist" : ratioHist, "legend" : legend  }

    return outDict


if __name__ == '__main__':

    #miniTreeFile = ROOT.TFile("data15to16_13TeV.root","OPEN")
    miniTreeFile = ROOT.TFile("mc16_13TeV.345706.Sherpa_222_NNPDF30NNLO_ggllll_130M4l.root","OPEN")

    miniTree = miniTreeFile.Get("tree_incl_all")

    cutOn = "m4l_constrained >115 && m4l_constrained<130"


    uncorrectedHist, ZConstrFSRHist, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll = prepHistograms(miniTreeFile)


    fillMZ2HistPair(miniTree, uncorrectedHist       , ZConstrFSRHist       , cutOn = cutOn)
    fillMZ2HistPair(miniTree, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll, cutOn = "")

    DSID = getDSIDStr( miniTreeFile.GetName() )
    #uncorrectedHist.SetTitle("full m4l range")
    uncorrectedHist.SetTitle("m4l in Higgs Window, sample # "+ DSID )

    prepHistOptics([uncorrectedHist, ZConstrFSRHist])

    ZConstrFSRHist.SetMarkerStyle(5)
    ZConstrFSRHist.SetMarkerColor(2)

    outDict = makeCanvasWithHistograms(uncorrectedHist, ZConstrFSRHist, canvasName = "canv_"+DSID)



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here