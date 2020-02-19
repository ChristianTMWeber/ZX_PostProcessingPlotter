import ROOT # to do all the ROOT stuff
import re # regular expressions

# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

from functions.rootDictAndTDirTools import buildDictTreeFromTDir
import functions.histHelper as histHelper # to help me fill some histograms
import functions.rootDictAndTDirTools as rootDictAndTDirTools


def prepareSignalSampleOverviewTH2(masterHistDict, channel = None):
    if channel is None: channel = masterHistDict.keys()[0]

    masspoints = getMasspointDict(masterHistDict , channel = channel )

    hist = masterHistDict[channel][masspoints.values()[0]]['Nominal']['All']
    nBinsX = hist.GetNbinsX()
    lowLimitX  = hist.GetBinLowEdge(1)
    highLimitX = hist.GetBinLowEdge(nBinsX+1)

    lowLimitY = min(masspoints.keys())
    highLimitY = max(masspoints.keys())+1
    nBinsY = highLimitY - lowLimitY

    signalOverviewTH2 = ROOT.TH2D("signalOverviewTH2", "signalOverviewTH2", nBinsX, lowLimitX, highLimitX, nBinsY , lowLimitY, highLimitY )

    return signalOverviewTH2


def getMasspointDict(masterHistDict , channel = None ):
    # returns a dict of the available masspoints: masspointDict[ int ] = <name of event type with that mass>
    # e.g.: masspointDict[20] = 'ZZd, m_{Zd} = 20GeV'
    #if channel is None: channel = masterHistDict.keys()[0]
    
    masspointDict = {}
    for channel in masterHistDict.keys(): 
        for eventType in masterHistDict[channel].keys(): 
            reObject = re.search("\d{2}", eventType)
            if reObject: # True if we found something
                # do some checks that the 'All' and 'Nominal' are in the dict, and that the TH1 in the dict is actually in there
                # these are mostly settings for development
                #if masterHistDict[channel][eventType]['Nominal']['All'] is not None:
                #    print(masterHistDict[channel][eventType]['Nominal']['All'])
                    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
                masspointDict[ int(reObject.group()) ] = eventType
    return masspointDict



def make3dOverview(masterHistDict, masspointsBeforeInterpolation = [] ):

    masspoints = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples
    

    signalOverviewTH2 = prepareSignalSampleOverviewTH2(masterHistDict, channel = "ZXSR")
    signalOverviewTH2Interpolated = signalOverviewTH2.Clone( signalOverviewTH2.GetName()+"Interpolated" )


    # sort things into the two overviewTH2s
    for mass in masspoints:
        hist = masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All']
        if mass in masspointsBeforeInterpolation: histHelper.fillTH2SliceWithTH1(signalOverviewTH2,             hist, mass )
        else:                                     histHelper.fillTH2SliceWithTH1(signalOverviewTH2Interpolated, hist, mass )

    signalOverviewTH2.SetLineColor(ROOT.kBlack)
    signalOverviewTH2.SetFillColor(ROOT.kBlue)
    signalOverviewTH2Interpolated.SetLineColor(ROOT.kBlack)
    signalOverviewTH2Interpolated.SetFillColor(ROOT.kRed)

    signalSampleStack = ROOT.THStack("signalSamples","signalSamples")
    signalSampleStack.Add(signalOverviewTH2)
    signalSampleStack.Add(signalOverviewTH2Interpolated)
    canvasSignalOverview3 = ROOT.TCanvas( "signalOverview3", "signalOverview3" ,1300/2,1300/2)
    signalSampleStack.Draw("LEGO1")
    # the following works only after calling signalSampleStack.Draw() once
    signalSampleStack.GetXaxis().SetRange(signalOverviewTH2.GetXaxis().FindBin(10),signalOverviewTH2.GetXaxis().FindBin(61))

    signalSampleStack.GetXaxis().SetTitle("m_{34} , " + str(signalSampleStack.GetXaxis().GetBinWidth(1) )+" GeV bin-width" )
    #signalSampleStack.GetXaxis().SetTitleSize(0.05)
    signalSampleStack.GetXaxis().SetTitleOffset(2.)
    signalSampleStack.GetXaxis().CenterTitle()

    signalSampleStack.GetYaxis().SetTitle("signal sample masspoint [GeV]" )
    signalSampleStack.GetYaxis().SetTitleOffset(2.)
    signalSampleStack.GetYaxis().CenterTitle()

    signalSampleStack.Draw("LEGO1")
    canvasSignalOverview3.Update()

    return signalSampleStack , canvasSignalOverview3






if __name__ == '__main__':

    fileName = "../preppedHistsV2_mc16ade_1GeVBins.root"

    aTFile = ROOT.TFile(fileName, "OPEN")

    tFileDict = buildDictTreeFromTDir(aTFile)

    masterHistDict = tFileDict.values()[0]

    masterHistDict["ZXSR"].keys()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    ###############################################################################
    ## write the histograms in the masterHistDict to file for the limit setting
    ###############################################################################
    #rootDictAndTDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = "test.root" )


    signalSampleStack, canvasSignalOverview3 = make3dOverview(masterHistDict, masspointsBeforeInterpolation = range(15,56,5) )


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    masspoints = getMasspointDict(masterHistDict , channel = "ZXSR" ) # This will be used later in plotting the signal samples

    massesSorted = masspoints.keys();   massesSorted.sort()

    signalTH1List = []
    for mass in massesSorted: signalTH1List.append(masterHistDict["ZXSR"][ masspoints[mass] ]['Nominal']['All'])

    signalOverviewFile = ROOT.TFile("signalOverview.root","RECREATE")
    #signalOverviewTH2.Write()
    #signalOverviewTH2Interpolated.Write()
    signalSampleStack.Write()
    canvasSignalOverview3.Write()
    for hist in signalTH1List: hist.Write()
    signalOverviewFile.Close()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


