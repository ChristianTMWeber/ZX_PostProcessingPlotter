
import ROOT
import numpy as np

import re

import math
import argparse # to parse command line options


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper
import functions.RootTools as RootTools
import functions.rootDictAndTDirTools as TDirTools

from functions.getArrayConfInterval import getArrayConfInterval

def getCanvasAndLegendFromList( inputList):

    if inputList is None: return None, None
    legend = None
    canvas = None

    for element in inputList:
        if isinstance(element,ROOT.TCanvas): canvas = element
        elif isinstance(element,ROOT.TLegend): legend = element

    return canvas , legend

def makeGraphOverview( extractedLimit,  expectedLimit1Sig, expectedLimit2Sig , colorScheme = ROOT.kRed, writeTo = False, YAxisLimits = None, keepInScopeList = [] ):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.6; yOffset = 0.7
        xWidth  = 0.3; ywidth = 0.2
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend


    reuseCanvas = False

    canv, legend = getCanvasAndLegendFromList( keepInScopeList )

    if legend is None: legend = setupTLegend()
    if canv   is None: canv = ROOT.TCanvas("GraphOverview", "GraphOverview",1920/2, 1080)
    else:  reuseCanvas = True
    canv.SetLeftMargin(0.15)
    canv.SetBottomMargin(0.1)

    

    if YAxisLimits is not None: expectedLimit2Sig.GetYaxis().SetRangeUser(YAxisLimits[0], YAxisLimits[1])
 

    expectedLimit2Sig.GetYaxis().SetTitle("Upper 95% CL on #sigma_{H #rightarrow ZZ_{d} #rightarrow 4l} [fb] ")
    expectedLimit2Sig.GetYaxis().SetTitleSize(0.06)
    expectedLimit2Sig.GetYaxis().SetTitleOffset(0.8)
    expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetXaxis().SetTitleOffset(0.85)
    #expectedLimit2Sig.GetXaxis().CenterTitle()

    expectedLimit2Sig.SetFillColorAlpha(colorScheme-10,0.6) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
    #expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
    #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    if reuseCanvas: expectedLimit2Sig.Draw("3 same") # use 'A' option only for first TGraph apparently
    else:           expectedLimit2Sig.Draw("A3 same") # use 'A' option only for first TGraph apparently

    expectedLimit1Sig.SetFillColorAlpha(colorScheme-9,0.6) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
    #expectedLimit1Sig.SetFillColor(colorScheme-9)
    #expectedLimit1Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit1Sig.Draw("3 same")

    expectedLimitMedian = graphHelper.getTGraphWithoutError( expectedLimit1Sig  , ySetpoint = "median")

    expectedLimitMedian.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    expectedLimitMedian.SetLineWidth(2)
    expectedLimitMedian.SetLineColor(colorScheme)
    expectedLimitMedian.Draw("same")

    if extractedLimit is not None:

        extractedLimit.SetLineStyle(1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
        extractedLimit.SetLineWidth(2)
        extractedLimit.SetLineColor(colorScheme)
        extractedLimit.Draw("same")


    if extractedLimit is not None: legend.AddEntry(extractedLimit , "observed Limit"  , "l");
    legend.AddEntry(expectedLimitMedian , "expected limit"  , "l");
    legend.AddEntry(expectedLimit1Sig , "#pm1#sigma expected limit"  , "f");
    legend.AddEntry(expectedLimit2Sig , "#pm2#sigma expected limit"  , "f");    

    legend.Draw()

    #canv.SetLogy()

    canv.Update() #"a3" also seems to work https://root.cern/doc/master/classTGraphPainter

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if writeTo: writeTo.cd(); canv.Write()

    keepInScopeList.extend( [canv, expectedLimit2Sig, expectedLimit1Sig, expectedLimitMedian, extractedLimit, legend] )

    return canv, keepInScopeList



def yieldBranchAndContent(TTree, cutAt = 10):


    for branch in TTree.GetListOfBranches():         
        
        varName =  branch.GetName() 
        cutString = varName + " < " + str(cutAt)

        arrayFromTTree = RootTools.GetValuesFromTree(TTree, varName, cutString)

        mass = int(re.search("\d{2}", varName).group())  # systematics

        yield mass, arrayFromTTree



def getMeanAndStdDictFromTTree(TTree, nSigma = 1, cutAt = 10):

    meanDict = {}
    lowLimitDict = {}
    upLimitDict = {}

    for mass, npArray in yieldBranchAndContent(TTree, cutAt = cutAt):

        meanDict[mass] =  np.mean( npArray )

        lowLimitDict[mass] = np.mean( npArray ) - ( np.std( npArray  ) * nSigma)
        upLimitDict[mass]  = np.mean( npArray ) + ( np.std( npArray  ) * nSigma)

    return meanDict, lowLimitDict, upLimitDict

def getconfInterval(TTree,  nSigma = 1. , cutAt = 10):

    meanDict = {}
    lowLimitDict = {}
    upLimitDict = {}

    confidenceSetpoint = math.erf( float(nSigma) / 2.**0.5)

    for mass, npArray in yieldBranchAndContent(TTree, cutAt = cutAt):

        arrayMean = np.mean( npArray )


        lowLimit , highLimit = getArrayConfInterval( npArray, confidenceValue = confidenceSetpoint,  intervalCenter = arrayMean)
        meanDict[mass]   =  arrayMean
        #errorLow[mass]   =  arrayMean - lowLimit
        #errorHigh[mass]  =  highLimit - arrayMean
        lowLimitDict[mass] = lowLimit
        upLimitDict[mass]  = highLimit

    return meanDict, lowLimitDict, upLimitDict



def getToyLimits( filename , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_1sigma" ,nSigma = 1, intervalType = "confInterval"):

    makeMixingParameters = False

    # mixing dict taken from "Illuminating dark photons with high-energy colliders", arXiv:1412.0018, Table 2
    mixingDict =  { 14 : 0.00252 , 15 : 0.00295 , 16 : 0.00338 , 17 : 0.003885 , 18 : 0.00439 , 19 : 0.00497 , 20 : 0.00555 , 21 : 0.00618 , 22 : 0.00681 , 23 : 0.007475 , 24 : 0.00814 , 25 : 0.00877 , 26 : 0.0094 , 27 : 0.0099 , 28 : 0.0104 , 29 : 0.0106 , 30 : 0.0108 , 31 : 0.010205 , 32 : 0.00961 , 33 : 0.0078 , 34 : 0.00599 , 35 : 0.004895 , 36 : 0.0038 , 37 : 0.00346 , 38 : 0.00312 , 39 : 0.00296 , 40 : 0.0028 , 41 : 0.002715 , 42 : 0.00263 , 43 : 0.00258 , 44 : 0.00253 , 45 : 0.0025 , 46 : 0.00247 , 47 : 0.002445 , 48 : 0.00242 , 49 : 0.0024 , 50 : 0.00238 , 51 : 0.002365 , 52 : 0.00235 , 53 : 0.002335 , 54 : 0.00232 , 55 : 0.002305 , 56 : 0.00229 }
    higgsXS = 4.858E+04 # femot barn


    testFile = ROOT.TFile(filename)

    upperLimitTree1Sig = testFile.Get(TTreeName)

    
    if intervalType == "confInterval":
        mean, lowLimit, highLimit = getconfInterval(upperLimitTree1Sig, nSigma = nSigma , cutAt = 10)
    elif intervalType == "standardDeviation":
        mean, lowLimit, highLimit = getMeanAndStdDictFromTTree(upperLimitTree1Sig, nSigma = nSigma, cutAt = 10)


    toyLimitTGrapah = graphHelper.createNamedTGraphAsymmErrors("toyLimit_1sigma")

    for mass in sorted(mean.keys()):

        pointNr = toyLimitTGrapah.GetN()



        meanVal = mean[mass]

        lowVal = lowLimit[mass]
        highVal = highLimit[mass] 

        if makeMixingParameters: 
            mixingFactor =  1./(higgsXS * mixingDict[mass])
            meanVal *= mixingFactor
            lowVal *= mixingFactor
            highVal *= mixingFactor

            meanVal = np.sqrt(meanVal)
            lowVal  = np.sqrt(lowVal)
            highVal = np.sqrt(highVal)
        



        errorLow = meanVal -lowVal
        errorHigh = highVal - meanVal


        toyLimitTGrapah.SetPoint( pointNr, mass, meanVal )
        toyLimitTGrapah.SetPointError( pointNr, 0,0, errorLow , errorHigh )

    return toyLimitTGrapah


def getAsymptoticTGraphs(filename):
    expectedLimitTFile = ROOT.TFile(filename, "OPEN")

    observedLimitGraph         = expectedLimitTFile.Get("observedLimitGraph")
    expectedLimitsGraph_1Sigma = expectedLimitTFile.Get("expectedLimits_1Sigma")
    expectedLimitsGraph_2Sigma = expectedLimitTFile.Get("expectedLimits_2Sigma")

    return 


if __name__ == '__main__':



    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="name or path to the input files")
    parser.add_argument( "--limitType", type=str, help = "type of the limit we are plotting ", choices=["asymptotic","toyBased"] )
    parser.add_argument( "--outputName", type=str, help = "filename for the output", default= None )
    parser.add_argument( "--YAxis", type=float, nargs=2, help = "lower and upper limit for the plot Y axis, --YAxis 0 2.5", default= None )

    args = parser.parse_args()

    if args.outputName is None:  outputFileName = re.sub( ".root", "_XSPlot.root"  , args.input)
    else:                        outputFileName = args.outputName

    if not outputFileName.endswith(".root"): outputFileName += ".root"


    if args.limitType == "asymptotic":

        ###################### get limits (from asymptotics)

        #asympFileName = "toyResults_MC16adeV2.root"
        #asympFileName = "asymptotiveLimitV3_AsimovData.root"
        asympFileName = args.input
        #                                                                    TTreeName = "upperLimits2Sig_observed"
        #observedLimitTGraph =  getToyLimits( asympFileName , TTreeName = "bestEstimates_asymptotic", graphName = "observedLimits_upperLimit" ,nSigma = 1, intervalType = "standardDeviation")
        #observedLimitTGraph =  getToyLimits( "asymptotiveLimitV3_AsimovData.root" , TTreeName = "upperLimits2Sig_observed", graphName = "observedLimits_upperLimit" ,nSigma = 1, intervalType = "standardDeviation")

        #observedLimitTGraphNoErrors = graphHelper.getTGraphWithoutError( observedLimitTGraph )

        #########  plotExpectedLimitsFromTGraph   ### specifically just asymptotic case
        expectedLimitTFile = ROOT.TFile(asympFileName, "OPEN")

        observedLimitTGraph = None

        observedLimitGraph         = expectedLimitTFile.Get("observedLimitGraph")
        expectedLimitsGraph_1Sigma = expectedLimitTFile.Get("expectedLimits_1Sigma")
        expectedLimitsGraph_2Sigma = expectedLimitTFile.Get("expectedLimits_2Sigma")

        

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



        outputTFile = ROOT.TFile("XSLimitPlot.root", "RECREATE")
        #makeGraphOverview( observedLimitTGraphNoErrors , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = outputTFile)
        canv, keepInScopeList = makeGraphOverview(  observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = outputTFile, YAxisLimits = args.YAxis)
        outputTFile.Close()


        canv.Print( re.sub( ".root", ".pdf"  , outputFileName) )
        canv.Print( re.sub( ".root", ".png"  , outputFileName) )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    elif args.limitType == "toyBased":

        ################# plot expected limits from TTree    

        #testFile = ROOT.TFile("../allCombinedMC16a_1895.root")
        #upperLimitTree1Sig = testFile.Get("upperLimits1Sig_toys")

        #filename = "all_ToysV2_5109.root"
        asympFileName = args.input

        #filename = "allcombV1_all_mc16ade_5203Entries.root"



        toyLimitTGrapah1Sigma = getToyLimits( filename , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_1sigma", nSigma = 1, intervalType = "confInterval")
        toyLimitTGrapah2Sigma = getToyLimits( filename , TTreeName = "upperLimits1Sig_toys", graphName = "toyLimit_2sigma", nSigma = 2, intervalType = "confInterval")


        expectedLimit = graphHelper.getTGraphWithoutError( toyLimitTGrapah1Sigma )

        observedLimitTGraph =  getToyLimits( "unblindedObservedLimits.root" , TTreeName = "upperLimits2Sig_observed", graphName = "observedLimits_upperLimit" ,nSigma = 1, intervalType = "standardDeviation")
        observedLimitTGraphNoErrors = graphHelper.getTGraphWithoutError( observedLimitTGraph )
        


        outputTFile = ROOT.TFile("XSLimitPlot.root", "RECREATE")

        canv, keepInScopeList = makeGraphOverview( observedLimitTGraphNoErrors,  toyLimitTGrapah1Sigma, toyLimitTGrapah2Sigma , colorScheme = ROOT.kRed, writeTo = outputTFile)

        outputTFile.Close()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



                                   
