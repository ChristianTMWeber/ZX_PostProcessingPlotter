#
# Let's see what kind of impact the Final State Radiation (FSR) recovery and Z-mass constraint have on the m34 spectrum
#

import ROOT

import re
import os
import argparse # to parse command line options


import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import files from parent directories

import functions.histHelper as histHelper # to help me with histograms


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.10,0.77,0.95, 0.98)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(2);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend


def fillMZ2HistPair(aTTree, uncorrectedHist, ZConstrFSRHist, cutOn = ""):

    aTTree.Draw("mZ2_unconstrained >>" + uncorrectedHist.GetName(), cutOn)
    aTTree.Draw("mZ2_constrained   >>" + ZConstrFSRHist.GetName(), cutOn)

    #rescale X-axis

    for hist in [uncorrectedHist, ZConstrFSRHist]:
        axRangeLow, axRangeHigh = histHelper.getFirstAndLastNonEmptyBinInHist(hist, offset = 2)
        hist.GetXaxis().SetRange(axRangeLow,axRangeHigh)

    return None

def getDSIDStr(sampleName): return re.search("(\d{6})|(data\d{2}(\w{2}\d{2})*)",sampleName ).group()
    #   find six digits OR
    #   the word "data" plus two digits, with zero or one times the following (i.e. it is optional) two text characters with two difits after it

def setupHistograms(miniTreeName):

    if isinstance(miniTreeName, ROOT.TObject): miniTreeName = miniTreeName.GetName()

    DSID = getDSIDStr(miniTreeName)

    uncorrectedHist = ROOT.TH1D("uncorrectedHist_"+DSID, "uncorrectedHist_"+DSID, 1000,0,1000)
    #uncorrectedHist.SetCanExtend(ROOT.TH1.kAllAxes)

    ZConstrFSRHist = uncorrectedHist.Clone("ZConstrFSRHist_"+DSID)

    uncorrectedHist_m4lAll = uncorrectedHist.Clone("uncorrectedHist_"+DSID +"_m4lAll")
    ZConstrFSRHist_m4lAll = uncorrectedHist.Clone("ZConstrFSRHist_"+DSID +"_m4lAll")

    return uncorrectedHist, ZConstrFSRHist, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll


def prepHistOptics(hist):

    if isinstance(hist,list): 
        for element in hist: prepHistOptics(element)
        return None

    maxVal , _ = histHelper.getMaxBin(hist , useError = False, skipZeroBins = True)

    if maxVal is not None: hist.GetYaxis().SetRangeUser(0, maxVal * 1.1)

    #uncorrectedHist.SetFillStyle(3244)
    hist.SetMarkerColor(1)
    hist.GetYaxis().SetTitle("Events / " + str(hist.GetBinWidth(1) )+" GeV" )
    hist.GetYaxis().SetTitleSize(0.05)
    hist.GetYaxis().SetTitleOffset(1.)
    hist.GetYaxis().CenterTitle()
    hist.SetStats( False)

    hist.GetXaxis().SetTitle("m_{34} [GeV]")
    hist.GetXaxis().SetTitleSize(0.045)
    hist.GetXaxis().SetTitleOffset(0.8)

    return None

def setAlternateHistColorScheme(hist):

    if isinstance(hist,list): 
        for element in hist: setAlternateHistColorScheme(element)
        return None

    hist.SetMarkerStyle(5)
    hist.SetMarkerColor(2)

    return None


def prepRatioHistOptics(ratioHist):

    ratioHist.SetMarkerColor(1)

    maxRatioVal , _ = histHelper.getMaxBin(ratioHist , useError = False, skipZeroBins = True)
    minRatioVal , _ = histHelper.getMinBin(ratioHist , useError = False, skipZeroBins = True)

    if maxRatioVal is not None: ratioHist.GetYaxis().SetRangeUser(minRatioVal * 0.99, maxRatioVal * 1.01)

    ratioHist.SetTitle("")
    
    ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
    ratioHist.GetYaxis().SetLabelSize(0.1)

    ratioHist.GetYaxis().SetTitle("ratio")
    #ratioHist.GetYaxis().SetTitle("#splitline{FSR_Z-Constr. / }{uncorrected}")

    #splitline{aaa}{bbb}
    ratioHist.GetYaxis().SetTitleSize(0.12)
    ratioHist.GetYaxis().SetTitleOffset(0.4)
    ratioHist.GetYaxis().CenterTitle()

    ratioHist.SetMarkerStyle(8)
    ratioHist.SetStats( False)

    ratioHist.GetXaxis().SetLabelSize(0.12)
    ratioHist.GetXaxis().SetTitleSize(0.13)
    ratioHist.GetXaxis().SetTitleOffset(1.0)
    ratioHist.GetXaxis().SetTitle("m_{34} [GeV]")

    return None


def makeCanvasWithHistograms(uncorrectedHist, ZConstrFSRHist, canvasName = "canv"):

    canvas = ROOT.TCanvas(canvasName, canvasName,2560/2, 1080)

    histPadYStart = 3.5/13
    histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
    histPad.Draw();              # Draw the upper pad: pad1
    histPad.cd();                # pad1 becomes the current pad

    uncorrectedHist.Draw("HIST")
    ZConstrFSRHist.Draw("same P HIST")


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

    ratioHist.Draw("P HIST")

    canvas.Update()

    outDict = { "canvas" : canvas, "histPad" : histPad, "ratioPad" : ratioPad, "ratioHist" : ratioHist, "legend" : legend  }

    return outDict


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--input",  "-i", type=str, default=os.getcwd(), help="path to the input files")
    parser.add_argument("--output", "-o", type=str, default="output.root", help="name of the output file")

    parser.add_argument( "--batch", default=False, action='store_true' , 
    help = "If run with '--batch' we will activate root batch mode and suppress all creation of graphics." ) 

    parser.add_argument( "--printAs", nargs='*', type=str,
    help = "Add file endings that we can print the figures to, e.g. .png, .pdf, etc" ) 

    args = parser.parse_args()

    if args.batch : ROOT.gROOT.SetBatch(True)

    outputFileName = args.output


    # delet the outputFile, so that we can write to it later on successively with the "update" option of the ROOT.TFile
    if os.path.isfile(outputFileName): os.remove(outputFileName)

    pathToRootFiles = args.input

    fileList = []

    if os.path.isfile(pathToRootFiles): fileList.append(pathToRootFiles)
    else:
        for file in  os.listdir(pathToRootFiles): 
            fileAndPath = os.path.join(pathToRootFiles,file)
            if os.path.isfile(fileAndPath) and fileAndPath.endswith(".root"): fileList.append(fileAndPath)


    for file in  fileList: 

        #miniTreeFile = ROOT.TFile("data15to16_13TeV.root","OPEN")
        miniTreeFile = ROOT.TFile(file,"OPEN")

        miniTree = miniTreeFile.Get("tree_incl_all")


        ############## Prep and Fill Histograms ##############

        uncorrectedHist, ZConstrFSRHist, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll = setupHistograms(miniTreeFile)

        DSID = getDSIDStr( miniTreeFile.GetName() )


        higgsWindowCut = "(m4l_constrained >115 && m4l_constrained<130)"
        m4lAllCut = ""

        if "data" in DSID:
            higgsWindowCut += " && m4l_constrained < 115 && m4l_constrained>130" # maybe find another way to exlcute the Higgs Window here
            m4lAllCut += "m4l_constrained < 115 || m4l_constrained>130"




        fillMZ2HistPair(miniTree, uncorrectedHist       , ZConstrFSRHist       , cutOn = "weight_corr *" +higgsWindowCut)
        fillMZ2HistPair(miniTree, uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll, cutOn = "weight_corr")

        #uncorrectedHist.SetTitle("full m4l range")
        uncorrectedHist.SetTitle("m4l in Higgs Window, # "+ DSID )
        uncorrectedHist_m4lAll.SetTitle("m4l unconstrained, # "+ DSID )

        prepHistOptics([uncorrectedHist, ZConstrFSRHist,uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll])

        setAlternateHistColorScheme( [ZConstrFSRHist, ZConstrFSRHist_m4lAll] )


        outDict = makeCanvasWithHistograms(uncorrectedHist, ZConstrFSRHist, canvasName = "canv_"+DSID)
        outDictAll_m4lAll = makeCanvasWithHistograms(uncorrectedHist_m4lAll, ZConstrFSRHist_m4lAll, canvasName = "canv_"+DSID+"_m4lAll")

        ############## Save Results ##############


        outputTFile = ROOT.TFile(outputFileName, "UPDATE")
        outputTFile.mkdir(DSID)
        TDir=outputTFile.Get(DSID)
        TDir.cd()

        uncorrectedHist.Write()
        ZConstrFSRHist.Write()
        outDict["canvas"].Write()

        uncorrectedHist_m4lAll.Write()
        ZConstrFSRHist_m4lAll.Write()
        outDictAll_m4lAll["canvas"].Write()
        outputTFile.Close()


        if args.printAs: 
            for ending in args.printAs :
                outDict["canvas"].Print(outDict["canvas"].GetName() + ending)
                outDictAll_m4lAll["canvas"].Print(outDictAll_m4lAll["canvas"].GetName() + ending)

        outDict["canvas"].Close()
        outDictAll_m4lAll["canvas"].Close()


    print( "\tAdd Done! \n\toutputs saved to " + outputFileName)


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here