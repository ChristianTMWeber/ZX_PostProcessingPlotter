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

    statsTexts.append( "#font[72]{ATLAS} internal")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.0f fb^{-1}" %( 139. ) ) 

    if "2l2e" in filename:                         statsTexts.append( "2#mu2e, 4e final states" )
    elif "2l2mu" in filename:                      statsTexts.append( "4#mu, 2e2#mu final states" )
    elif "all" in filename or "All" in filename:   statsTexts.append( "4#mu, 2e2#mu, 2#mu2e, 4e final states" )

    statsTPave=ROOT.TPaveText(0.15,0.73,0.45,0.88,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);
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

if __name__ == '__main__':

    #file = ROOT.TFile( "ZX_FiducialCombined_HiggsTagged.root","OPEN")
    #file = ROOT.TFile( "ZX_FiducialCombined.root","OPEN")
    file = ROOT.TFile( "Za_mc16ade_Fiducial_HiggsWindow.root","OPEN")

    

    hists = [hist for hist in generateTDirContents(file)]

    hists.sort( key = lambda x:x.GetName() , reverse=True) # i.e. we

    acceptances = collections.defaultdict(lambda: collections.defaultdict(dict))


    histMassDict = { int(re.search("\d+",hist.GetName()).group()) : hist for hist in hists}

    for hist in hists: 

        histContents = histToDict(hist)


        #outputString = hist.GetName() + " truth count " + str(histContents["ZdTruthFlavor_2l2mu"]  + histContents["ZdTruthFlavor_2l2e"]) + " eventsProcessed: " +  str(histContents["eventsProcessed"])

        #outputString = hist.GetName() + " truth count " + str(histContents["ZdTruthFlavor_2l2mu"]  + histContents["ZdTruthFlavor_2l2e"])

        mass = re.search("\d+",hist.GetName()).group()

        

        if histContents["ZdTruthFlavor_2l2e"] == 0: acceptances["2l2e"][int(mass)] = 0
        else:  acceptances["2l2e"][int(mass)]   = (histContents["4e"]  + histContents["2mu2e"])/histContents["ZdTruthFlavor_2l2e"]
        acceptances["2l2mu"][int(mass)]  = (histContents["4mu"] + histContents["2e2mu"])/histContents["ZdTruthFlavor_2l2mu"] 
        acceptances["all"][int(mass)]   = histContents["all"] /(histContents["ZdTruthFlavor_2l2e"] +histContents["ZdTruthFlavor_2l2mu"]  )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        outputString = hist.GetName() + ", #2l2mu = " + str(acceptances["2l2mu"][int(mass)]  ) + \
                ", #2l2e = " + str(acceptances["2l2e"][int(mass)]) + \
                ", #all = " + str( acceptances["all"][int(mass)]  ) 


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

    
    graphDict = { flavor: graphHelper.dictToTGraph(acceptances[flavor]) for flavor in acceptances.keys() }

    graphDict["all"].GetYaxis().SetRangeUser(0.2,max(allAcceptances)*1.2)
    graphDict["all"].GetYaxis().SetTitle("acceptance [unitless]")
    graphDict["all"].GetYaxis().SetTitleSize(0.05)
    graphDict["all"].GetYaxis().SetTitleOffset(0.8)
    #graphDict["all"].GetYaxis().CenterTitle()

    graphDict["all"].GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    graphDict["all"].GetXaxis().SetTitleSize(0.05)
    graphDict["all"].GetXaxis().SetTitleOffset(0.85)

    graphDict["all"].SetLineColor(ROOT.kBlack)
    graphDict["2l2e"].SetLineColor(ROOT.kBlue)
    graphDict["2l2mu"].SetLineColor(ROOT.kRed)



    legend = setupTLegend()

    legend.AddEntry(graphDict["all"]   , "4#mu, 2e2#mu, 2#mu2e, 4e final states"  , "l");
    legend.AddEntry(graphDict["2l2e"]  , "2#mu2e, 4e final states"  , "l");
    legend.AddEntry(graphDict["2l2mu"] , "4#mu, 2e2#mu final states"  , "l");

    for key in graphDict: graphDict[key].SetLineWidth(2)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    canvas = ROOT.TCanvas("AcceptanceOverview", "AcceptanceOverview",int(720*1.47), 720) #,1920/1, 1080)
    ROOT.gPad.SetTickx();ROOT.gPad.SetTicky(); # enable ticks on both side of the plots



    graphDict["all"].Draw("")
    graphDict["2l2e"].Draw("same")
    graphDict["2l2mu"].Draw("same")

    atlasBlurb = addATLASBlurp("") 

    legend.Draw()



    canvas.Update()


    for fileType in ["png","pdf","root"]: canvas.Print("acceptanceOverview."+fileType)

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    print("All Done")