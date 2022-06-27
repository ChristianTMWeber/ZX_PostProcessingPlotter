import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly

import re # regular expressions for pattern matching


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper

def generateTDirContents(TDir):
    # this is a python generator 
    # this one allows me to loop over all of the contents in a given ROOT TDir with a for loop

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    for TKey in TDirKeys: 
        yield TKey.ReadObj() # this is how I access the element that belongs to the current TKey

def histToDict(hist):

    outputDict = {}

    nBins = hist.GetNbinsX()

    for binNr in xrange(nBins): 

        binLabel = hist.GetXaxis().GetBinLabel(binNr+1) 

        outputDict[binLabel] = hist.GetBinContent(binNr+1)

    return outputDict


def addATLASBlurp(filename):

    def activateATLASPlotStyle():
        # runs the root macro that defines the ATLAS style, and checks that it is active
        # relies on a seperate style macro
        ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

        if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
        else:                                warnings.warn("Did not load ATLAS style properly")

        return None

    activateATLASPlotStyle()
    statsTexts = []

    statsTexts.append( "#font[72]{ATLAS} Simulation")
    #statsTexts.append( "#font[72]{ATLAS} Internal")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.0f fb^{-1}" %( 139. ) ) 
    statsTexts.append( "H #rightarrow ZZ_{d} #rightarrow 4l" ) 

    if "2l2e" in filename:                         statsTexts.append( "2#mu2e, 4e final states" )
    elif "2l2mu" in filename:                      statsTexts.append( "4#mu, 2e2#mu final states" )
    elif "all" in filename or "All" in filename:   statsTexts.append( "4#mu, 2e2#mu, 2#mu2e, 4e final states" )



    blurbDx = .3; blurbDy = .15
    legendDx = .3 ; legendDy = 0


    # (0.58,0.51 + delta,0.9,0.67 + delta)
    # (0.15,0.73,0.45,0.88,"NBNDC")
    dx = 0.06
    dy = 0.2
    statsTPave=ROOT.TPaveText(0.58, .73  ,0.58 + blurbDx, .73 +blurbDy,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);
    #statsTPave.AddText( "ZX channel") # https://root.cern/doc/master/classTAttText.html#T1
    statsTPave.SetTextAlign(12)
    statsTPave.Draw();

    return statsTPave


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    xOffset = 0.48; yOffset = 0.15
    xWidth  = 0.4; ywidth = 0.2
    TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border
    return TLegend

def castFiducialYieldHistsToDict(fileName):

    file = ROOT.TFile( fileName ,"OPEN")

    hists = [hist for hist in generateTDirContents(file)]

    hists.sort( key = lambda x:x.GetName() , reverse=True) # i.e. we

    histContents = { hist.GetName() : histToDict(hist)  for  hist in hists }

    for key in histContents:
        histContents[key]["2l2mu"] = histContents[key]["4mu"] + histContents[key]["2e2mu"]
        histContents[key]["2l2e"]  = histContents[key]["4e"] + histContents[key]["2mu2e"]
        histContents[key]["ZdTruthFlavor_all"]  = histContents[key]["ZdTruthFlavor_2l2e"] + histContents[key]["ZdTruthFlavor_2l2mu"]

    return histContents


def prepCanvas(title):

    canvas = ROOT.TCanvas(title, title,int(720*1.47), 720) #,1920/1, 1080)
    ROOT.gPad.SetTickx();ROOT.gPad.SetTicky(); # enable ticks on both side of the plots

    canvas.SetLeftMargin(0.2)
    canvas.SetBottomMargin(0.1)

    return canvas


def setGraphProperties( graph ):

    graph.GetYaxis().SetRangeUser(0.29,max(allAcceptances)*1.15)
    graph.GetYaxis().SetTitle("Acceptance [unitless]")
    graph.GetYaxis().SetTitleSize(0.05)
    graph.GetYaxis().SetTitleOffset(0.8)
    #graph.GetYaxis().CenterTitle()

    graph.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    graph.GetXaxis().SetTitleSize(0.05)
    graph.GetXaxis().SetTitleOffset(0.85)

    return None



if __name__ == '__main__':

    #file = ROOT.TFile( "ZX_FiducialCombined_HiggsTagged.root","OPEN")
    #file = ROOT.TFile( "ZX_FiducialCombined.root","OPEN")

    fiducialYieldHists = castFiducialYieldHistsToDict("ZX_Fiducial_mc16ade_HiggsWindowV3.root")

    #file = ROOT.TFile( "ZX_Fiducial_mc16ade_HiggsWindow.root","OPEN")
    #hists = [hist for hist in generateTDirContents(file)]
    #hists.sort( key = lambda x:x.GetName() , reverse=True) # i.e. we
    acceptances = collections.defaultdict(lambda: collections.defaultdict(dict))
    acceptanceError = collections.defaultdict(lambda: collections.defaultdict(dict))
    #histMassDict = { int(re.search("\d+",hist.GetName()).group()) : hist for hist in hists}



    for histName in sorted(fiducialYieldHists.keys()): 

        histContents = fiducialYieldHists[histName]


        #outputString = hist.GetName() + " truth count " + str(histContents["ZdTruthFlavor_2l2mu"]  + histContents["ZdTruthFlavor_2l2e"]) + " eventsProcessed: " +  str(histContents["eventsProcessed"])

        #outputString = hist.GetName() + " truth count " + str(histContents["ZdTruthFlavor_2l2mu"]  + histContents["ZdTruthFlavor_2l2e"])
        mass = int(re.search("\d+", histName ).group())


        fiducialYield = 0

        for flavor in ['all','2l2e','2l2mu']: 

            fiducialYield = histContents[flavor]
            totalProd = histContents["ZdTruthFlavor_"+flavor]

            if totalProd == 0:
                acceptances[flavor][mass] = 0
                acceptanceError[flavor][mass] = 0
            else:
                acceptances[flavor][mass] = fiducialYield / totalProd
                fiducialYieldBinomialError = (fiducialYield - fiducialYield/totalProd)**.5
                acceptanceError[flavor][mass] = fiducialYieldBinomialError / totalProd

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        outputString = histName + ", #2l2mu = " + str(acceptances["2l2mu"][mass]  ) + \
                ", #2l2e = " + str(acceptances["2l2e"][mass]) + \
                ", #all = " + str( acceptances["all"][mass]  ) 

        print outputString


    # print out acceptances so I can copy it to the 'plotXSLimit.py'
    for flavor in acceptances.keys():
        outStringList = []
        for mass in sorted(acceptances[flavor].keys()): outStringList.append( str(acceptances[flavor][mass]))
        print( flavor )
        print(", ".join(outStringList))

    #print(histToDict( histMassDict[55] ))
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    #for binTitle in histContents: print( binTitle, histContents[binTitle] )

    allAcceptances = []
    for key in acceptances: allAcceptances.extend( acceptances[key].values()  )

    graphWithUncertaintyDict = { flavor: graphHelper.dictToTGraph(acceptances[flavor], uncertDict = acceptanceError[flavor]) for flavor in acceptances.keys() }
    graphDict = { flavor: graphHelper.dictToTGraph(acceptances[flavor], uncertDict = None) for flavor in acceptances.keys() }

    for key in graphDict.keys():  graphDict[key].SetName(key);graphDict[key].SetTitle(key)

    graphDict["all"].SetLineColor(ROOT.kBlack); graphWithUncertaintyDict["all"].SetFillColorAlpha(ROOT.kBlack, 0.2)
    graphDict["2l2e"].SetLineColor(ROOT.kRed); graphWithUncertaintyDict["2l2e"].SetFillColorAlpha(ROOT.kRed, 0.2)
    graphDict["2l2mu"].SetLineColor(ROOT.kBlue); graphWithUncertaintyDict["2l2mu"].SetFillColorAlpha(ROOT.kBlue, 0.2)

    graphDict["all"].SetFillColorAlpha(ROOT.kBlack, 0.2)
    graphDict["2l2e"].SetFillColorAlpha(ROOT.kRed, 0.2)
    graphDict["2l2mu"].SetFillColorAlpha(ROOT.kBlue, 0.2)

    graphDict["all"].SetLineStyle(1)
    graphDict["2l2e"].SetLineStyle(2)
    graphDict["2l2mu"].SetLineStyle(3)

    for graph in graphWithUncertaintyDict.values():  setGraphProperties( graph )
    for graph in graphWithUncertaintyDict.values():  setGraphProperties( graph )
    for key in graphWithUncertaintyDict.keys():  graphWithUncertaintyDict[key].SetName(key+"_uncert");graphWithUncertaintyDict[key].SetTitle(key+"_uncert");

    legend = setupTLegend()

    legend.AddEntry(graphDict["2l2mu"] , "4#mu, 2e2#mu final states"  , "lf");
    legend.AddEntry(graphDict["all"]   , "4#mu, 2e2#mu, 2#mu2e, 4e final states"  , "lf");
    legend.AddEntry(graphDict["2l2e"]  , "2#mu2e, 4e final states"  , "lf");
    

    for key in graphDict: graphDict[key].SetLineWidth(1)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    canvas =  prepCanvas("AcceptanceOverview")


    errorMultigraph = ROOT.TMultiGraph()
    for graph in graphWithUncertaintyDict.values(): errorMultigraph.Add(graph)

    setGraphProperties( errorMultigraph )


    errorMultigraph.Draw("A3")
    #graphWithUncertaintyDict["all"].Draw("A3")
    #graphWithUncertaintyDict["2l2e"].Draw("3 same")
    #graphWithUncertaintyDict["2l2mu"].Draw("3 same")


    lineMultigraph = ROOT.TMultiGraph()
    for graph in graphDict.values(): lineMultigraph.Add(graph)

    lineMultigraph.Draw()

    #graphDict["all"].Draw("same")
    #graphDict["2l2e"].Draw(" same")
    #graphDict["2l2mu"].Draw(" same")

    atlasBlurb = addATLASBlurp("") 

    legend.Draw()



    canvas.Update()


    for fileType in ["png","pdf","root"]: canvas.Print("acceptanceOverview."+fileType)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    print("All Done")