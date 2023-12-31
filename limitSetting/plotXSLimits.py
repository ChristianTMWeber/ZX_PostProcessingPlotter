
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

def addATLASBlurp(filename, boundaries = (0.5,0.57,0.9,0.67)):

    activateATLASPlotStyle()
    statsTexts = []

    statsTexts.append( "#font[72]{ATLAS}")
    #statsTexts.append( "#font[72]{ATLAS} Internal")
    #statsTexts.append( "#font[72]{ATLAS} Preliminary")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.0f fb^{-1}" %( 139. ) ) 
    #statsTexts.append( "ZX channel") # https://root.cern/doc/master/classTAttText.html#T1

    #if "2l2e" in filename:                         statsTexts.append( "2#mu2e, 4e final states" )
    #elif "2l2mu" in filename:                      statsTexts.append( "4#mu, 2e2#mu final states" )
    #elif "all" in filename or "All" in filename:   statsTexts.append( "4#mu, 2e2#mu, 2#mu2e, 4e final states" )

    statsTPave=ROOT.TPaveText(boundaries[0],boundaries[1],boundaries[2],boundaries[3],"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);
    statsTPave.SetTextAlign(12)
    statsTPave.Draw();

    return statsTPave


def makeGraphOverview( extractedLimit,  expectedLimit1Sig, expectedLimit2Sig , colorScheme = None, writeTo = False, YAxisLimits = None, 
                       keepInScopeList = [], smoothPlot = False , yAxisTitle = "Upper 95% CL on #sigma_{H #rightarrow ZZ_{d} #rightarrow 4l} [fb] ", xAxisTitle = "m_{Z_{d}} [GeV]",
                       makeYAxisLogarithmic = False , legendSuffix = "", yAxisTitleSize = 0.045, legendBoundaries = None ,YAxisSetMaxDigits = None):

    def setupTLegend( boundaries = None):

        if boundaries is None : boundaries = (0.58, 0.68, 0.58+0.3 ,0.68+0.2)
        # set up a TLegend, still need to add the different entries

        TLegend = ROOT.TLegend(boundaries[0],boundaries[1],boundaries[2],boundaries[3])

        #TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend


    reuseCanvas = False

    canv, legend = getCanvasAndLegendFromList( keepInScopeList )

    if legend is None: legend = setupTLegend(boundaries = legendBoundaries)
    if canv   is None: canv = ROOT.TCanvas("GraphOverview", "GraphOverview",int(720*1.47), 720) #,1920/1, 1080)
    else:  reuseCanvas = True
    canv.SetLeftMargin(0.2)
    canv.SetBottomMargin(0.1)
    if makeYAxisLogarithmic: canv.SetLogy()
    #canv.SetLogx()

    if YAxisLimits is not None: expectedLimit2Sig.GetYaxis().SetRangeUser(YAxisLimits[0], YAxisLimits[1])

    if smoothPlot:  
        errorBarDrawOption = "3 "
        regularTGraphDrawOption = "C "
    else:
        errorBarDrawOption = "3 "
        regularTGraphDrawOption = ""
 
    ROOT.gPad.SetTickx();ROOT.gPad.SetTicky(); # enable ticks on both side of the plots

    expectedLimit2Sig.GetYaxis().SetTitle(yAxisTitle)
    expectedLimit2Sig.GetYaxis().SetTitleSize( yAxisTitleSize )
    expectedLimit2Sig.GetYaxis().SetTitleOffset(1.05)
    #expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle(xAxisTitle)
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.045)
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
        alphaValue = 0.6
        if reuseCanvas: alphaValue -= 0.1
        expectedLimit2Sig.SetFillColorAlpha(colorScheme-10, alphaValue) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
        expectedLimit1Sig.SetFillColorAlpha(colorScheme-9,  alphaValue) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
        expectedLimitMedian.SetLineColor(colorScheme)
        ###expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
        #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
        #expectedLimit1Sig.SetFillColorAlpha(ROOT.kGreen,1) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now


    if YAxisSetMaxDigits is not None: expectedLimit2Sig.GetYaxis().SetMaxDigits(YAxisSetMaxDigits)

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


    if extractedLimit is not None: legend.AddEntry(extractedLimit , "Observed" +legendSuffix  , "l");
    legend.AddEntry(expectedLimitMedian , "Expected" +legendSuffix , "l");
    legend.AddEntry(expectedLimit1Sig , "Expected #pm1 #sigma" +legendSuffix , "f");
    legend.AddEntry(expectedLimit2Sig , "Expected #pm2 #sigma" +legendSuffix , "f");    

    legend.Draw()

    canv.Update() #"a3" also seems to work https://root.cern/doc/master/classTGraphPainter

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if writeTo: writeTo.cd(); canv.Write()

    keepInScopeList.extend( [canv, expectedLimit2Sig, expectedLimit1Sig, expectedLimitMedian, extractedLimit, legend] )

    ROOT.gPad.RedrawAxis("G") # to make sure that the Axis ticks are above the histograms

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
        higgsXS = 4.858E+04 # femto barn
        ZdToLLBranchingRatioDict = { 14 : 0.288  ,  15 : 0.288  ,  16 : 0.288  ,  17 : 0.2875 ,  18 : 0.287  ,  19 : 0.2865 ,  20 : 0.286  ,  21 : 0.2855 ,  22 : 0.285  ,  23 : 0.2845 ,  24 : 0.284  ,  25 : 0.2835 ,  26 : 0.283  ,  27 : 0.282  ,  28 : 0.281  ,  29 : 0.2805 ,  30 : 0.28   ,  31 : 0.279  ,  32 : 0.278  ,  33 : 0.2765 ,  34 : 0.275  ,  35 : 0.274  ,  36 : 0.273  ,  37 : 0.2715 ,  38 : 0.27   ,  39 : 0.2685 ,  40 : 0.267  ,  41 : 0.265  ,  42 : 0.263  ,  43 : 0.261  ,  44 : 0.259  ,  45 : 0.2565 ,  46 : 0.254  ,  47 : 0.2515 ,  48 : 0.249  ,  49 : 0.2465 ,  50 : 0.244  ,  51 : 0.241  ,  52 : 0.238  ,  53 : 0.2345 ,  54 : 0.231  ,  55 : 0.227  }
        ZToLLBranchingRatio = 0.0673 

        ZdBranchingRatioList = []
        XSLimitDict = {}

        for x in xrange( len(massPointList) ):  XSLimitDict[ int(massPointList[x]) ]  =  XSLimitList[x] 

        #for x in XSLimitDict.keys():
        #    mixingParameterSquaredList.append(  mixingDict[int()]   )

        for massPoint in sorted(XSLimitDict.keys()):  ZdBranchingRatioList.append(  XSLimitDict[massPoint] / higgsXS /ZToLLBranchingRatio /ZdToLLBranchingRatioDict[massPoint] )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        return ZdBranchingRatioList


    def XSLimitToFiducialXSLimit( massPointList, XSLimitList, flavor = "all"):

        xList = [15, 20, 25, 30, 35, 40, 45, 50, 55]

        acceptances = {}
        acceptances["all"] = [0.357654054054, 0.388194117647, 0.438163157895, 0.484426315789, 0.516921052632, 0.535021052632, 0.546821052632, 0.5512, 0.556578947368]
        acceptances["2l2e"] = [0.306456689495, 0.332439836573, 0.384631627848, 0.446484724194, 0.489524432442, 0.51137647419, 0.526228800623, 0.532394604066, 0.541807499131]
        acceptances["2l2mu"] = [0.408451159235, 0.443537989076, 0.49137333921, 0.522435863667, 0.544197966557, 0.558523198338, 0.56740940332, 0.569901954609, 0.57134138]

        fiducialXSLimits = []

        for x in xrange( len(massPointList) ): 
            acceptance = interpolator1D( xList, acceptances[flavor], massPointList[x] ) 
            fiducialXSLimits.append( XSLimitList[x] * acceptance) 

        return fiducialXSLimits

    def XSLimitToZaLimit( massPointList, XSLimitList, XSLimitToFiducialXSLimit, flavor = "all"):

        fiducialLimits = XSLimitToFiducialXSLimit(massPointList, XSLimitList, flavor = flavor)

        xList = [15, 20, 25, 30]

        acceptances = {}
        acceptances["all"] = [0.233762711864, 0.239411428571, 0.289577970223, 0.332806179775]
        acceptances["2l2e"] = [0,             0.199346590909, 0.251766666667, 0.308861111111]
        acceptances["2l2mu"] =[0.233757062147, 0.279936781609, 0.32961370361, 0.357295454545]

        fiducialXSLimits = []

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        for x in xrange( len(massPointList) ): 
            if massPointList[x] > 30: break # don't have signal samples for ma > 30 GeV
            acceptance = interpolator1D( xList, acceptances[flavor], massPointList[x] ) 
            fiducialXSLimits.append( fiducialLimits[x] / acceptance) 

        return fiducialXSLimits

    def XSLimitToMassMixingLimit(massPointList, XSLimitList, XSLimitToBRLimit):

        #XSLimitToBRLimit( massPointList , XSLimitList             )

        branchingRatioList_H_ZZd_4l = XSLimitToBRLimit(massPointList, XSLimitList)

        gammaHiggs = 4.07E-3 # (GeV) SM Higgs decay width

        HVaccumExpectation = 246. # (GeV) # Higgs vaccum expectation value

        mHiggs = 125. # (GeV) Higgs mass
        mZBoson = 91.188 # (GeV) Z boson mass
        XSHiggs = 43.92 # standard model higgs cross section

        Zto2lBranchingRatio = 0.068 # l is here muon or electron

        higgsXS = 4.858E+04 # femto barn

        fFunction = 1./math.pi * (mHiggs**2 - mZBoson**2)**3 / (HVaccumExpectation**2 * mHiggs**3) # f function from eq 7 in PHYSICAL REVIEW D 92, 092001 (2015)

        massMixingLimitList = []

        for x in xrange( len(massPointList) ):  
            if massPointList[x] > 35: break
            # following equations from run1 version of ZX analysis: PHYSICAL REVIEW D 92, 092001 (2015)
            #                                                       https://journals.aps.org/prd/abstract/10.1103/PhysRevD.92.092001
            branchingRatioList_H_ZZd_4l = XSLimitList[x]/higgsXS
            massMixingLimit =  branchingRatioList_H_ZZd_4l/ Zto2lBranchingRatio * gammaHiggs / fFunction # technically limits on \delta**2 * BR(Zd -> 2l), delta is mass mixing parameter
            massMixingLimitList.append(massMixingLimit)

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        return massMixingLimitList

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
        observedLimits_mixingParameter              = XSLimitToFiducialXSLimit( massPoints , observedLimits             , flavor = flavor)
        expectedLimits_mixingParameter              = XSLimitToFiducialXSLimit( massPoints , expectedLimits             , flavor = flavor)
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToFiducialXSLimit( massPoints , expectedLimits_1Sigma_Low  , flavor = flavor)
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToFiducialXSLimit( massPoints , expectedLimits_1Sigma_High , flavor = flavor)
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToFiducialXSLimit( massPoints , expectedLimits_2Sigma_Low  , flavor = flavor)
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToFiducialXSLimit( massPoints , expectedLimits_2Sigma_High , flavor = flavor)

    elif limitType == "massMixingLimit" :
        observedLimits_mixingParameter              = XSLimitToMassMixingLimit( massPoints , observedLimits             ,XSLimitToBRLimit)
        expectedLimits_mixingParameter              = XSLimitToMassMixingLimit( massPoints , expectedLimits             ,XSLimitToBRLimit)
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToMassMixingLimit( massPoints , expectedLimits_1Sigma_Low  ,XSLimitToBRLimit)
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToMassMixingLimit( massPoints , expectedLimits_1Sigma_High ,XSLimitToBRLimit)
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToMassMixingLimit( massPoints , expectedLimits_2Sigma_Low  ,XSLimitToBRLimit)
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToMassMixingLimit( massPoints , expectedLimits_2Sigma_High ,XSLimitToBRLimit)

    elif limitType == "ZaXSLimit" :
        observedLimits_mixingParameter              = XSLimitToZaLimit( massPoints , observedLimits             , XSLimitToFiducialXSLimit, flavor = flavor)
        expectedLimits_mixingParameter              = XSLimitToZaLimit( massPoints , expectedLimits             , XSLimitToFiducialXSLimit, flavor = flavor)
        expectedLimits_mixingParameter_1Sigma_Low   = XSLimitToZaLimit( massPoints , expectedLimits_1Sigma_Low  , XSLimitToFiducialXSLimit, flavor = flavor)
        expectedLimits_mixingParameter_1Sigma_High  = XSLimitToZaLimit( massPoints , expectedLimits_1Sigma_High , XSLimitToFiducialXSLimit, flavor = flavor)
        expectedLimits_mixingParameter_2Sigma_Low   = XSLimitToZaLimit( massPoints , expectedLimits_2Sigma_Low  , XSLimitToFiducialXSLimit, flavor = flavor)
        expectedLimits_mixingParameter_2Sigma_High  = XSLimitToZaLimit( massPoints , expectedLimits_2Sigma_High , XSLimitToFiducialXSLimit, flavor = flavor)


    observedLimitGraph         = graphHelper.listToTGraph( massPoints, observedLimits_mixingParameter , name = observedLimitGraph.GetName() )
    expectedLimitsGraph_1Sigma = graphHelper.listToTGraph( massPoints, expectedLimits_mixingParameter , yLowList = expectedLimits_mixingParameter_1Sigma_Low, yHighList = expectedLimits_mixingParameter_1Sigma_High , name = expectedLimitsGraph_1Sigma.GetName())
    expectedLimitsGraph_2Sigma = graphHelper.listToTGraph( massPoints, expectedLimits_mixingParameter , yLowList = expectedLimits_mixingParameter_2Sigma_Low, yHighList = expectedLimits_mixingParameter_2Sigma_High , name = expectedLimitsGraph_2Sigma.GetName())

    return observedLimitGraph, expectedLimitsGraph_1Sigma , expectedLimitsGraph_2Sigma


def outputHEPDataRootFile(outputName, graphList):

    HEPDataTFile = ROOT.TFile("HEPData_"+outputName, "RECREATE")
    for graph in graphList: graph.Write()
    HEPDataTFile.Close()

    return None

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
    parser.add_argument( "--makeMassMixingPlot" , default=False, action='store_true', help = "Plot mass-mixingParam^2 times branching ratio of Zd->2l instead of measured cross section limit.")
    parser.add_argument( "--makeZaLimitPlot" , default=False, action='store_true', help = "Plot Za limit.")
    parser.add_argument( "--logarithmixYAxis" , default=False, action='store_true', help = "make YAxis logarithmic")

    parser.add_argument( "--AddATLASBlurp" , default=False, choices=["all", "All", "2l2e", "2l2mu", "blank", False], help = "Add ATLAS blurp to the figure, include ")

    parser.add_argument("--secondInput", type=str, default=False, help="second input files for plots where we show 2l2e and 2l2mu for example")



    args = parser.parse_args()

    ROOT.gROOT.SetBatch(True)


    if args.secondInput: colorScheme = ROOT.kBlue
    else:                colorScheme = None

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

            import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            if isinstance(observedLimitGraph, ROOT.TGraphAsymmErrors): # for some limit setting schemes the upperlimit is given by the upper error of the TGraph. 
                observedLimitGraph = graphHelper.getTGraphWithoutError( observedLimitGraph , ySetpoint = "yHigh")

        yAxisTitlePrefix = "95 % CL upper limit on "
        yAxisTitle = yAxisTitlePrefix + "#sigma(gg #rightarrow H #rightarrow ZZ_{d} #rightarrow 4l) [fb] "
        xAxisTitle = "m_{Z_{d}} [GeV]"

        #observedLimitGraph = None

        yAxisTitleSize = 0.039
        delta = 0.06

        blurbDx = .3; blurbDy = .1
        legendDx = .3 ; legendDy = 0

        blurbBoundaries = (0.58, .78  ,0.58 + blurbDx, .78 +blurbDy )
        legendBoundaries = (0.58, 0.58 , 0.58+legendDx , .78 )

        if args.secondInput: legendBoundaries = (0.58, 0.46 , 0.58+legendDx , .78 )



        #legendBoundaries = (0.58, 0.68 + delta, 0.95 ,0.88)
        #blurbBoundaries = (0.58,0.51 + delta,0.9,0.67 + delta)


        limitType = None
        YAxisSetMaxDigits = None

        if args.makeMixingParameterPlot: 
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "mixingParameterLimit" , flavor = args.AddATLASBlurp)
            yAxisTitle = yAxisTitlePrefix + "kinetic mixing parameter #varepsilon"
            #yAxisTitleSize = 0.045
            #blurbBoundaries = (0.3,0.76,0.62,0.86)
            #legendBoundaries = (0.3, .78 +blurbDy - .18 , 0.3+legendDx , .78 +blurbDy )
            limitType = "mixingParameterLimit"
        elif args.makeBranchingRatioPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "brachingRatioLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = yAxisTitlePrefix + "#frac{#sigma_{H}}{#sigma_{H}^{SM}}B(H #rightarrow ZZd)"  
            limitType = "brachingRatioLimit"
            YAxisSetMaxDigits = 2
        elif args.makeFiducialXSPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "fiducialXSLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = yAxisTitlePrefix + "#sigma_{fid}(gg #rightarrow H #rightarrow ZX #rightarrow 4l) [fb] "
            xAxisTitle = "m_{X} [GeV]"
            limitType = "fiducialXSLimit"
        elif args.makeMassMixingPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "massMixingLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = yAxisTitlePrefix + "#delta^{2} #times BR(Z_{d} #rightarrow 2l)"
            #yAxisTitleSize = 0.045
            #blurbBoundaries = (0.7,0.76,0.93,0.86)
            #legendBoundaries = (0.25, 0.69, 0.25+0.3 ,0.69+0.2)
            legendBoundaries = (0.25, .78 +blurbDy - .18 , 0.3+legendDx , .78 +blurbDy )
            limitType = "massMixingLimit"
        elif args.makeZaLimitPlot:
            observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma = convertXSLimitsToMixingParameterLimits(observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , limitType = "ZaXSLimit", flavor = args.AddATLASBlurp)
            yAxisTitle = yAxisTitlePrefix + "#sigma(gg #rightarrow H #rightarrow Za #rightarrow 2l2#mu) [fb] "
            xAxisTitle = "m_{a} [GeV]"
            #blurbBoundaries = (0.24,0.76,0.62,0.86)
            limitType = "ZaXSLimit"


        outputHEPDataRootFile(outputFileName, [observedLimitGraph, expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma] )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        if args.secondInput: legendSuffix = ", 2l2e"
        else:                legendSuffix = ""

        
        #makeGraphOverview( observedLimitTGraphNoErrors , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = outputTFile)
        canv, keepInScopeList = makeGraphOverview(  observedLimitGraph   , expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = colorScheme , 
                                                    YAxisLimits = args.YAxis, keepInScopeList = [], smoothPlot = args.smooth ,
                                                    yAxisTitle = yAxisTitle, makeYAxisLogarithmic = args.logarithmixYAxis, xAxisTitle = xAxisTitle, yAxisTitleSize = yAxisTitleSize, legendBoundaries = legendBoundaries , legendSuffix = legendSuffix, YAxisSetMaxDigits = YAxisSetMaxDigits) 



        atlasBlurb = addATLASBlurp(args.AddATLASBlurp, boundaries = blurbBoundaries)
        #atlasBlurb = addATLASBlurp("") 


        canv.Update()
        #### use this if I wanna plot a second set of limits on top of the first set ###

        if args.secondInput: 
            expectedLimitTFile = ROOT.TFile( args.secondInput, "OPEN") # 2l2e
            observedLimitGraphB = expectedLimitTFile.Get("observedLimitGraph")
            expectedLimitsGraph_1SigmaB = expectedLimitTFile.Get("expectedLimits_1Sigma")
            expectedLimitsGraph_2SigmaB = expectedLimitTFile.Get("expectedLimits_2Sigma")
            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            if limitType:
                observedLimitGraphB   , expectedLimitsGraph_1SigmaB, expectedLimitsGraph_2SigmaB = convertXSLimitsToMixingParameterLimits(observedLimitGraphB   , 
                                        expectedLimitsGraph_1SigmaB, expectedLimitsGraph_2SigmaB , limitType = limitType, flavor = "2l2mu")
            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            canv, keepInScopeList = makeGraphOverview(  observedLimitGraphB  , expectedLimitsGraph_1SigmaB, expectedLimitsGraph_2SigmaB , colorScheme = ROOT.kRed ,
                                                         YAxisLimits = args.YAxis, keepInScopeList = keepInScopeList, smoothPlot = args.smooth, 
                                                         yAxisTitle = yAxisTitle, xAxisTitle = xAxisTitle, legendSuffix = ", 2l2#mu")
            atlasBlurb = addATLASBlurp("",boundaries = blurbBoundaries) 

            outputHEPDataRootFile(re.sub( ".root", "__2l2mu.root"  , outputFileName), [observedLimitGraphB, expectedLimitsGraph_1SigmaB, expectedLimitsGraph_2SigmaB] )
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        #expectedLimitTFile = ROOT.TFile( "mc16adeToyResultsV7.37.root", "OPEN") # 2l2mu
        #observedLimitGraphC = expectedLimitTFile.Get("observedLimitGraph")
        #expectedLimitsGraph_1SigmaC = expectedLimitTFile.Get("expectedLimits_1Sigma")
        #expectedLimitsGraph_2SigmaC = expectedLimitTFile.Get("expectedLimits_2Sigma")
        #observedLimitGraphC   , expectedLimitsGraph_1SigmaC, expectedLimitsGraph_2SigmaC = convertXSLimitsToMixingParameterLimits(observedLimitGraphC   , 
        #                        expectedLimitsGraph_1SigmaC, expectedLimitsGraph_2SigmaC , limitType = "fiducialXSLimit", flavor = "2l2mu")
        #
        #canv, keepInScopeList = makeGraphOverview(  observedLimitGraphC  , expectedLimitsGraph_1SigmaC, expectedLimitsGraph_2SigmaC , colorScheme = ROOT.kRed , 
        #                                            YAxisLimits = args.YAxis, keepInScopeList = keepInScopeList, smoothPlot = args.smooth, 
        #                                            yAxisTitle = yAxisTitle, xAxisTitle = xAxisTitle, legendSuffix = ", 2l2#mu")
        #atlasBlurb = addATLASBlurp("", boundaries = (0.55,0.57,0.95,0.67)) 
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



                                   
