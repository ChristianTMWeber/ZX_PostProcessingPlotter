
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

from  limitFunctions.RooIntegralMorphWrapper import getNewSetNorm as interpolator1D # to interpolate 1d thinds

def getCanvasAndLegendFromList( inputList):

    if inputList is None: return None, None
    legend = None
    canvas = None

    for element in inputList:
        if isinstance(element,ROOT.TCanvas): canvas = element
        elif isinstance(element,ROOT.TLegend): legend = element

    return canvas , legend

def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None

def addATLASBlurp(filename):

    activateATLASPlotStyle()
    statsTexts = []

    statsTexts.append( "#font[72]{ATLAS} internal")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.0f fb^{-1}" %( 139. ) ) 

    if "2l2e" in filename:                         statsTexts.append( "2#mu2e, 4e final states" )
    elif "2l2mu" in filename:                      statsTexts.append( "4#mu, 2e2#mu final states" )
    elif "all" in filename or "All" in filename:   statsTexts.append( "4#mu, 2e2#mu, 2#mu2e, 4e final states" )

    statsTPave=ROOT.TPaveText(0.5,0.57,0.9,0.67,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);
    statsTPave.Draw();

    return statsTPave


def makeGraphOverview( extractedLimit,  expectedLimit1Sig, expectedLimit2Sig , colorScheme = None, writeTo = False, YAxisLimits = None, 
                       keepInScopeList = [], smoothPlot = False , yAxisTitle = "Upper 95% CL on #sigma_{H #rightarrow ZZ_{d} #rightarrow 4l} [fb] ",
                       makeYAxisLogarithmic = False , legendSuffix = ""):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.58; yOffset = 0.68
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
    if canv   is None: canv = ROOT.TCanvas("GraphOverview", "GraphOverview",int(720*1.47), 720) #,1920/1, 1080)
    else:  reuseCanvas = True
    canv.SetLeftMargin(0.2)
    canv.SetBottomMargin(0.1)
    if makeYAxisLogarithmic: canv.SetLogy()
    #canv.SetLogx()

    if YAxisLimits is not None: expectedLimit2Sig.GetYaxis().SetRangeUser(YAxisLimits[0], YAxisLimits[1])

    if smoothPlot:  
        errorBarDrawOption = "4 "
        regularTGraphDrawOption = "C "
    else:
        errorBarDrawOption = "3 "
        regularTGraphDrawOption = ""
 
    ROOT.gPad.SetTickx();ROOT.gPad.SetTicky(); # enable ticks on both side of the plots

    expectedLimit2Sig.GetYaxis().SetTitle(yAxisTitle)
    expectedLimit2Sig.GetYaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetYaxis().SetTitleOffset(1.0)
    expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetXaxis().SetTitleOffset(0.85)
    #expectedLimit2Sig.GetXaxis().CenterTitle()

    expectedLimitMedian = graphHelper.getTGraphWithoutError( expectedLimit1Sig  , ySetpoint = "median")

    expectedLimitMedian.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    expectedLimitMedian.SetLineWidth(2)

    #colorScheme = ROOT.kRed

    if colorScheme is None:
        #### ATLAS green yellow color scheme
        expectedLimit2Sig.SetFillColor(ROOT.kYellow)
        expectedLimit1Sig.SetFillColor(ROOT.kGreen)
        expectedLimitMedian.SetLineColor(ROOT.kBlack)

    else: # Custon Color Scheme
        expectedLimit2Sig.SetFillColorAlpha(colorScheme-10,0.6) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
        expectedLimit1Sig.SetFillColorAlpha(colorScheme-9,0.6) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
        expectedLimitMedian.SetLineColor(colorScheme)
        ###expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
        #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
        #expectedLimit1Sig.SetFillColorAlpha(ROOT.kGreen,1) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now


    if reuseCanvas: expectedLimit2Sig.Draw(errorBarDrawOption + " same") # use 'A' option only for first TGraph apparently
    else:           expectedLimit2Sig.Draw(errorBarDrawOption + " A same") # use 'A' option only for first TGraph apparently



    #expectedLimit1Sig.SetFillColor(colorScheme-9)
    #expectedLimit1Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit1Sig.Draw(errorBarDrawOption + " same")

    expectedLimitMedian.Draw(regularTGraphDrawOption + "same")

    if extractedLimit is not None:

        extractedLimit.SetLineStyle(1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
        extractedLimit.SetLineWidth(2)
        #extractedLimit.SetLineColor(colorScheme)
        if colorScheme is None: extractedLimit.SetLineColor(ROOT.kBlack)
        else:                   extractedLimit.SetLineColor(colorScheme)
        extractedLimit.Draw(regularTGraphDrawOption + "same")


    if extractedLimit is not None: legend.AddEntry(extractedLimit , "observed Limit" +legendSuffix  , "l");
    legend.AddEntry(expectedLimitMedian , "expected limit" +legendSuffix , "l");
    legend.AddEntry(expectedLimit1Sig , "#pm1#sigma expected limit" +legendSuffix , "f");
    legend.AddEntry(expectedLimit2Sig , "#pm2#sigma expected limit" +legendSuffix , "f");    

    legend.Draw()

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


def convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , 
    limitType = "mixingParameterLimit", flavor = None):

    flavor = flavor.lower() # ensure that all characters are lower case, also throws error if flavor is not a string, which is good for now

    def XSLimitToKineticMixingParameter( massPointList, XSLimitList):

        # mixing dict taken from "Illuminating dark photons with high-energy colliders", arXiv:1412.0018, Table 2
        mixingDict =  { 14 : 0.00252 , 15 : 0.00295 , 16 : 0.00338 , 17 : 0.003885 , 18 : 0.00439 , 19 : 0.00497 , 20 : 0.00555 , 21 : 0.00618 , 22 : 0.00681 , 23 : 0.007475 , 24 : 0.00814 , 25 : 0.00877 , 26 : 0.0094 , 27 : 0.0099 , 28 : 0.0104 , 29 : 0.0106 , 30 : 0.0108 , 31 : 0.010205 , 32 : 0.00961 , 33 : 0.0078 , 34 : 0.00599 , 35 : 0.004895 , 36 : 0.0038 , 37 : 0.00346 , 38 : 0.00312 , 39 : 0.00296 , 40 : 0.0028 , 41 : 0.002715 , 42 : 0.00263 , 43 : 0.00258 , 44 : 0.00253 , 45 : 0.0025 , 46 : 0.00247 , 47 : 0.002445 , 48 : 0.00242 , 49 : 0.0024 , 50 : 0.00238 , 51 : 0.002365 , 52 : 0.00235 , 53 : 0.002335 , 54 : 0.00232 , 55 : 0.002305 , 56 : 0.00229 }
        higgsXS = 4.858E+04 # femot barn
        # kinetic mixing parameter **2 =  (sigma_{H->ZZd->4l} / sigma_H) / mixingDict[massPoint]  

        mixingParameterList = []
        XSLimitDict = {}

        for x in xrange( len(massPointList) ):  XSLimitDict[ int(massPointList[x]) ]  =  XSLimitList[x] 

        #for x in XSLimitDict.keys():
        #    mixingParameterSquaredList.append(  mixingDict[int()]   )

        for massPoint in sorted(XSLimitDict.keys()):  mixingParameterList.append(  ( XSLimitDict[massPoint] / higgsXS /mixingDict[massPoint] )**0.5)

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        return mixingParameterList


    def XSLimitToBRLimit( massPointList, XSLimitList):

        # ZdToLLBranchingRatioDict  taken from "Illuminating dark photons with high-energy colliders", arXiv:1412.0018, Table 2
        higgsXS = 4.858E+04 # femot barn
        ZdToLLBranchingRatioDict = { 14 : 0.288  ,  15 : 0.288  ,  16 : 0.288  ,  17 : 0.2875 ,  18 : 0.287  ,  19 : 0.2865 ,  20 : 0.286  ,  21 : 0.2855 ,  22 : 0.285  ,  23 : 0.2845 ,  24 : 0.284  ,  25 : 0.2835 ,  26 : 0.283  ,  27 : 0.282  ,  28 : 0.281  ,  29 : 0.2805 ,  30 : 0.28   ,  31 : 0.279  ,  32 : 0.278  ,  33 : 0.2765 ,  34 : 0.275  ,  35 : 0.274  ,  36 : 0.273  ,  37 : 0.2715 ,  38 : 0.27   ,  39 : 0.2685 ,  40 : 0.267  ,  41 : 0.265  ,  42 : 0.263  ,  43 : 0.261  ,  44 : 0.259  ,  45 : 0.2565 ,  46 : 0.254  ,  47 : 0.2515 ,  48 : 0.249  ,  49 : 0.2465 ,  50 : 0.244  ,  51 : 0.241  ,  52 : 0.238  ,  53 : 0.2345 ,  54 : 0.231  ,  55 : 0.227  }
        ZToLLBranchingRatio = 0.00673 

        ZdBranchingRatioList = []
        XSLimitDict = {}

        for x in xrange( len(massPointList) ):  XSLimitDict[ int(massPointList[x]) ]  =  XSLimitList[x] 

        #for x in XSLimitDict.keys():
        #    mixingParameterSquaredList.append(  mixingDict[int()]   )

        for massPoint in sorted(XSLimitDict.keys()):  ZdBranchingRatioList.append(  XSLimitDict[massPoint] / higgsXS /ZToLLBranchingRatio /ZdToLLBranchingRatioDict[massPoint] )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        return ZdBranchingRatioList


    def XSLimitToFixucialXSLimit( massPointList, XSLimitList):

        xList = [15, 20, 25, 30, 35, 40, 45, 50, 55]

        acceptances = {}
        acceptances["all"] = [0.2344810810810811, 0.2650647058823529, 0.29614736842105266, 0.32632105263157896, 0.34549473684210524, 0.3544684210526316, 0.3597421052631579, 0.36243157894736844, 0.3676421052631579]
        acceptances["2l2e"] = [0.15540987876748755, 0.18345417188201119, 0.20836412779525731, 0.24438134300888678, 0.26468478352603597, 0.26789353098307517, 0.27110989462159574, 0.27222445059004835, 0.28951995872424213]
        acceptances["2l2mu"] = [0.31293410723323606, 0.3460745012541904, 0.3834036479650736, 0.4084075225201496, 0.42595160070582305, 0.4405217920597773, 0.44835752402403983, 0.4521425122294304, 0.44571657073104]

        fiducialXSLimits = []

        for x in xrange( len(massPointList) ): 
            acceptance = interpolator1D( xList, acceptances[flavor], massPointList[x] ) 
            fiducialXSLimits.append( XSLimitList[x] * acceptance) 

        return fiducialXSLimits

    massPoints , observedLimits = graphHelper.tGraphToList(observedLimitGraph , ySetpoint = "median")
    _ , expectedLimits = graphHelper.tGraphToList(expectedLimitsGraph_1Sigma , ySetpoint = "median")
    _ , expectedLimits_1Sigma_Low  = graphHelper.tGraphToList(expectedLimitsGraph_1Sigma , ySetpoint = "yLow")
    _ , expectedLimits_1Sigma_High = graphHelper.tGraphToList(expectedLimitsGraph_1Sigma , ySetpoint = "yHigh")
    _ , expectedLimits_2Sigma_Low  = graphHelper.tGraphToList(expectedLimitsGraph_2Sigma , ySetpoint = "yLow")
    _ , expectedLimits_2Sigma_High = graphHelper.tGraphToList(expectedLimitsGraph_2Sigma , ySetpoint = "yHigh")


    if limitType == "mixingParameterLimit" :
        observedLimits_mixingParameter              = XSLimitToKineticMixingParameter( massPoints , observedLimits             )
        expectedLimits_mixingParameter              = XSLimitToKineticMixingParameter( massPoints , expectedLimits             )
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToKineticMixingParameter( massPoints , expectedLimits_1Sigma_Low  )
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToKineticMixingParameter( massPoints , expectedLimits_1Sigma_High )
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToKineticMixingParameter( massPoints , expectedLimits_2Sigma_Low  )
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToKineticMixingParameter( massPoints , expectedLimits_2Sigma_High )

    elif limitType == "brachingRatioLimit" :
        observedLimits_mixingParameter              = XSLimitToBRLimit( massPoints , observedLimits             )
        expectedLimits_mixingParameter              = XSLimitToBRLimit( massPoints , expectedLimits             )
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToBRLimit( massPoints , expectedLimits_1Sigma_Low  )
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToBRLimit( massPoints , expectedLimits_1Sigma_High )
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToBRLimit( massPoints , expectedLimits_2Sigma_Low  )
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToBRLimit( massPoints , expectedLimits_2Sigma_High )

    elif limitType == "fiducialXSLimit" :
        observedLimits_mixingParameter              = XSLimitToFixucialXSLimit( massPoints , observedLimits             )
        expectedLimits_mixingParameter              = XSLimitToFixucialXSLimit( massPoints , expectedLimits             )
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToFixucialXSLimit( massPoints , expectedLimits_1Sigma_Low  )
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToFixucialXSLimit( massPoints , expectedLimits_1Sigma_High )
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToFixucialXSLimit( massPoints , expectedLimits_2Sigma_Low  )
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToFixucialXSLimit( massPoints , expectedLimits_2Sigma_High )


    observedLimitGraph = graphHelper.listToTGraph( massPoints, observedLimits_mixingParameter  )
    expectedLimitsGraph_1Sigma = graphHelper.listToTGraph( massPoints, expectedLimits_mixingParameter , yLowList = expectedLimits_mixingParameter_1Sigma_Low, yHighList = expectedLimits_mixingParameter_1Sigma_High )
    expectedLimitsGraph_2Sigma = graphHelper.listToTGraph( massPoints, expectedLimits_mixingParameter , yLowList = expectedLimits_mixingParameter_2Sigma_Low, yHighList = expectedLimits_mixingParameter_2Sigma_High )

    return observedLimitGraph, expectedLimitsGraph_1Sigma , expectedLimitsGraph_2Sigma

if __name__ == '__main__':



    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="name or path to the input files")
    parser.add_argument( "--observedLimitFile", type=str, help="option to provide alternative file take the observed limit from", )
    parser.add_argument( "--limitType", type=str, help = "type of the limit we are plotting ", choices=["asymptotic","toyBased"] , default= "asymptotic")
    parser.add_argument( "--outputName", type=str, help = "filename for the output", default= None )
    parser.add_argument( "--YAxis", type=float, nargs=2, help = "lower and upper limit for the plot Y axis, --YAxis 0 2.5", default= None )
    parser.add_argument( "--smooth",  default=False, action='store_true', help = "If selected, will smooth the plotted figures")
    parser.add_argument( "--makeMixingParameterPlot" , default=False, action='store_true', help = "Plot mixing prameter instead of cross section limit.")
    parser.add_argument( "--makeBranchingRatioPlot" , default=False, action='store_true', help = "Plot BranchingRatio prameter instead of cross section limit.")
    parser.add_argument( "--makeFiducialXSPlot" , default=False, action='store_true', help = "Plot fiducial cross section instead of measured cross section limit.")
    parser.add_argument( "--logarithmixYAxis" , default=False, action='store_true', help = "make YAxis logarithmic")

    parser.add_argument( "--AddATLASBlurp" , default=False, choices=["all", "All", "2l2e", "2l2mu", False], help = "Add ATLAS blurp to the figure, include ")

    colorScheme = None

    args = parser.parse_args()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if args.outputName is None:  outputFileName = re.sub( ".root", "_XSPlot.root"  , args.input)
    else:                        outputFileName = args.outputName

    if not outputFileName.endswith(".root"): outputFileName += ".root"


    if args.limitType == "asymptotic":

        ###################### get limits (from asymptotics)

        #asympFileName = "toyResults_MC16adeV2.root"
        #asympFileName = "asymptotiveLimitV3_AsimovData.root"
        #                                                                    TTreeName = "upperLimits2Sig_observed"
        #observedLimitTGraph =  getToyLimits( asympFileName , TTreeName = "bestEstimates_asymptotic", graphName = "observedLimits_upperLimit" ,nSigma = 1, intervalType = "standardDeviation")
        #observedLimitTGraph =  getToyLimits( "asymptotiveLimitV3_AsimovData.root" , TTreeName = "upperLimits2Sig_observed", graphName = "observedLimits_upperLimit" ,nSigma = 1, intervalType = "standardDeviation")

        #observedLimitTGraphNoErrors = graphHelper.getTGraphWithoutError( observedLimitTGraph )

        #########  plotExpectedLimitsFromTGraph   ### specifically just asymptotic case
        expectedLimitTFile = ROOT.TFile(args.input, "OPEN")
        expectedLimitsGraph_1Sigma = expectedLimitTFile.Get("expectedLimits_1Sigma")
        expectedLimitsGraph_2Sigma = expectedLimitTFile.Get("expectedLimits_2Sigma")



        if args.observedLimitFile is not None:  observedLimitTFile = ROOT.TFile(args.observedLimitFile , "OPEN")
        else :                                  observedLimitTFile = expectedLimitTFile


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        if "observedLimitGraph" in [tObject.GetName() for tObject in TDirTools.TDirToList(observedLimitTFile)]:
            observedLimitGraph         = observedLimitTFile.Get("observedLimitGraph")
            if isinstance(observedLimitGraph, ROOT.TGraphAsymmErrors): # for some limit setting schemes the upperlimit is given by the upper error of the TGraph. 
                observedLimitGraph = graphHelper.getTGraphWithoutError( observedLimitGraph , ySetpoint = "yHigh")

        yAxisTitle = "Upper 95% CL on #sigma_{H #rightarrow ZZ_{d} #rightarrow 4l} [fb] "

        #observedLimitGraph = None

        if args.makeMixingParameterPlot: 
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "mixingParameterLimit" , flavor = args.AddATLASBlurp)
            yAxisTitle = "Upper 95% CL onkinetic mixing parameter #varepsilon"
        elif args.makeBranchingRatioPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "brachingRatioLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = "Upper 95% CL on #frac{#sigma_{H}}{#sigma_{H}^{SM}}B(H #rightarrow ZZd)"  
        elif args.makeFiducialXSPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "fiducialXSLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = "Upper 95% CL on #sigma_{H #rightarrow ZZ_{d} #rightarrow 4l}^{fid} [fb] "



        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        
        #makeGraphOverview( observedLimitTGraphNoErrors , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = outputTFile)
        canv, keepInScopeList = makeGraphOverview(  observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = colorScheme , 
                                                    YAxisLimits = args.YAxis, keepInScopeList = [], smoothPlot = args.smooth ,
                                                    yAxisTitle = yAxisTitle, makeYAxisLogarithmic = args.logarithmixYAxis)


        if args.AddATLASBlurp: atlasBlurb = addATLASBlurp(args.AddATLASBlurp) 

        canv.Update()
        ### use this if I wanna plot a second set of limits on top of the first set ###
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        #expectedLimitTFile = ROOT.TFile( "mc16adeToyResultsV7.38.root", "OPEN")
        #observedLimitGraphB = expectedLimitTFile.Get("observedLimitGraph")
        #expectedLimitsGraph_1SigmaB = expectedLimitTFile.Get("expectedLimits_1Sigma")
        #expectedLimitsGraph_2SigmaB = expectedLimitTFile.Get("expectedLimits_2Sigma")
        #canv, keepInScopeList = makeGraphOverview(  observedLimitGraphB  , expectedLimitsGraph_1SigmaB, expectedLimitsGraph_2SigmaB , colorScheme = ROOT.kBlue , YAxisLimits = args.YAxis, keepInScopeList = keepInScopeList, smoothPlot = args.smooth, legendSuffix = ", 2l2e")
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


        outputTFile = ROOT.TFile(outputFileName, "RECREATE")

        canv.Write()

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

    else: print("Comand line potion '--limitType' not choosen! Nothing has been plotted :(")



                                   
