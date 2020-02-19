#
# Let's see what kind of impact the Final State Radiation (FSR) recovery and Z-mass constraint have on the m34 spectrum
#

import ROOT

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


if __name__ == '__main__':

    #miniTreeFile = ROOT.TFile("data15to16_13TeV.root","OPEN")
    miniTreeFile = ROOT.TFile("mc16_13TeV.345706.Sherpa_222_NNPDF30NNLO_ggllll_130M4l.root","OPEN")


    miniTree = miniTreeFile.Get("tree_incl_all")

    referenceHist = ROOT.TH1D("referenceHist", "referenceHist", 100,0,10)
    referenceHist.SetCanExtend(ROOT.TH1.kAllAxes)

    m34_FSR_Constrained = referenceHist.Clone("m34_FSR_Constrained")

    cutOn = "m4l_constrained >115 && m4l_constrained<130"

    miniTree.Draw("mZ2_unconstrained>>referenceHist", cutOn)
    miniTree.Draw("mZ2_constrained>>m34_FSR_Constrained", cutOn)

    #aHist = miniTree.Draw("mZ1_unconstrained")


    #referenceHist.SetTitle("full m4l range")
    referenceHist.SetTitle("m4l in Higgs Window")


    #referenceHist.SetFillStyle(3244)
    referenceHist.SetMarkerColor(1)
    referenceHist.GetYaxis().SetTitle("Events / " + str(referenceHist.GetBinWidth(1) )+" GeV" )
    referenceHist.GetYaxis().SetTitleSize(0.05)
    referenceHist.GetYaxis().SetTitleOffset(1.)
    referenceHist.GetYaxis().CenterTitle()
    referenceHist.SetStats( False)
    referenceHist.GetXaxis().SetTitle("m_{34} [GeV]")



    m34_FSR_Constrained.SetMarkerStyle(5)
    #m34_FSR_Constrained.SetMarkerSize(1)
    m34_FSR_Constrained.SetMarkerColor(2)
    m34_FSR_Constrained.SetStats( False)

    canvas = ROOT.TCanvas("canv","canv",720,720)

    histPadYStart = 3.5/13
    histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
    histPad.Draw();              # Draw the upper pad: pad1
    histPad.cd();                # pad1 becomes the current pad

    referenceHist.SetStats( False)
    referenceHist.Draw("")
    m34_FSR_Constrained.Draw("same P")


    legend = setupTLegend()
    legend.AddEntry(referenceHist , "reference" , "l");
    legend.AddEntry(m34_FSR_Constrained , "FSR recovered and Z constrained" , "p");
    legend.Draw()

    canvas.cd()
    canvas.Update()


    ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);

    ratioPad.SetTopMargin(0.)
    ratioPad.SetBottomMargin(0.3)
    ratioPad.SetGridy(); #ratioPad.SetGridx(); 
    ratioPad.Draw();              # Draw the upper pad: pad1
    ratioPad.cd();                # pad1 becomes the current pad


    ratioHist = m34_FSR_Constrained.Clone( m34_FSR_Constrained.GetName()+"_Clone" )
    ratioHist.Divide(referenceHist)

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
    ratioHist.Draw("P")

    ratioHist.GetXaxis().SetLabelSize(0.12)
    ratioHist.GetXaxis().SetTitleSize(0.13)
    ratioHist.GetXaxis().SetTitleOffset(1.0)
    ratioHist.GetXaxis().SetTitle("m_{34} [GeV]")

    canvas.Update()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here