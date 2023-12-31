import ROOT

import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import numpy as np # good ol' numpy
import copy # for making deep copies
import re # for redular expressions
import os

import sys 
sys.path.append( os.path.dirname( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.histNumpyTools as histNumpyTools
#from plotPostProcess import preselectTDirsForProcessing
import plotPostProcess

def makeMinAndMaxHistograms(listOfTh1s):

    histMatrix = histNumpyTools.listOfTH1ToNumpyMatrix(listOfTh1s)

    refHist = listOfTh1s[0]

    maxHist = refHist.Clone( refHist.GetName() + "_MaxHist")
    maxHist.Reset()
    minHist = maxHist.Clone( refHist.GetName() + "_MinHist")


    minimumBins = histMatrix.min(axis=0)
    maximumBins = histMatrix.max(axis=0)

    for binNr in xrange(0, len(minimumBins)): minHist.SetBinContent( binNr+1 ,minimumBins[binNr] )
    for binNr in xrange(0, len(maximumBins)): maxHist.SetBinContent( binNr+1 ,maximumBins[binNr] )

    return maxHist, minHist

def makeEnvelopeHistograms(listOfTh1s , upperEnvelopeFunction = lambda x : x.max(axis=0), lowerEnvelopeFunction = lambda x : x.min(axis=0)):

    histMatrix = histNumpyTools.listOfTH1ToNumpyMatrix(listOfTh1s) #histMatrix[ histNumber , binNr]

    refHist = listOfTh1s[0]

    maxHist = listOfTh1s[0].Clone( refHist.GetName() + "_UpperEnvelope") # pick an arbitrary histogram as reference histogram
    maxHist.Reset()
    minHist = maxHist.Clone( refHist.GetName() + "_LowerEnvelop")

    maximumBins = upperEnvelopeFunction(histMatrix)
    minimumBins = lowerEnvelopeFunction(histMatrix)

    for binNr in xrange(0, len(maximumBins)): maxHist.SetBinContent( binNr+1 ,maximumBins[binNr] )
    for binNr in xrange(0, len(minimumBins)): minHist.SetBinContent( binNr+1 ,minimumBins[binNr] )   

    return maxHist, minHist


def visualizeEnvelopeHistogram( upperHist, lowerHist, listHist, outputDir, nominalHist , title = "weight_variation_overview"):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.5; yOffset = 0.4
        xWidth  = 0.4; ywidth = 0.3
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    initialBatchStatus = ROOT.gROOT.IsBatch() # query batch status, so that we can toggle back to it
    ROOT.gROOT.SetBatch(True)

    tCanvas = ROOT.TCanvas( title,title, 1280,720)

    histPadYStart = 3.5/13
    histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
    ROOT.SetOwnership(histPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042

    histPad.Draw();              # Draw the upper pad: pad1
    histPad.cd();                # pad1 becomes the current pad

    for minMaxHist in [upperHist, lowerHist]:
        minMaxHist.SetLineStyle(ROOT.kDashed )
        minMaxHist.SetLineWidth( 2 )

    upperHist.SetLineColor(ROOT.kRed )
    lowerHist.SetLineColor(ROOT.kMagenta )

    histMaximumValues = []

    listHist[0].SetTitle(title)

    for hist in listHist: 
        hist.SetStats( False) # remove stats box
        hist.GetYaxis().SetTitle("#Events")
        hist.Draw("SAME HIST")
        hist.SetTitle(title)
        histMaximumValues.append( hist.GetMaximum())

    upperHist.Draw("SAMEHIST")
    lowerHist.Draw("SAMEHIST")

    legend = setupTLegend()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    legend.AddEntry(upperHist , upperHist.GetName().split("_")[2] + " variation Up, yield: %.2f"  %upperHist.Integral(), "l");
    legend.AddEntry(listHist[0] , title.split("_")[-2] + " variations", "l");
    legend.AddEntry(lowerHist , lowerHist.GetName().split("_")[2] + " variation Down, yield: %.2f"  %lowerHist.Integral(), "l");

    legend.Draw()

    listHist[0].GetYaxis().SetRangeUser(0, max(histMaximumValues) * 1.1)


    tCanvas.cd()

    ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);
    ROOT.SetOwnership(ratioPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042

    ratioPad.SetTopMargin(0.)
    ratioPad.SetBottomMargin(0.3)
    ratioPad.Draw();              # Draw the upper pad: pad1
    ratioPad.cd();                # pad1 becomes the current pad

    upperRatioHist  = upperHist.Clone( "RatioUp")
    lowerRatioHist  = lowerHist.Clone( "RatioDown")

    #upperRatioHist.Divide(nominalHist)
    #lowerRatioHist.Divide(nominalHist)

    for hist in [upperRatioHist, lowerRatioHist]:
        hist.SetStats( False) # remove stats box
        hist.SetTitle("")
        #hist.GetYaxis().SetTitle(" % change to nominal")
        hist.GetYaxis().SetTitle("variation - nominal")
        hist.GetXaxis().SetLabelSize(0.06)
        hist.GetXaxis().SetTitleSize(0.1)
        hist.GetXaxis().SetTitleOffset(0.7)

        hist.GetYaxis().SetLabelSize(0.065)
        hist.GetYaxis().SetTitleSize(0.1)
        hist.GetYaxis().SetTitleOffset(0.3)
        hist.GetYaxis().SetLabelSize(0.1)

        for binNr in xrange(1,hist.GetNbinsX()+1): 
            hist.SetBinError(binNr,0)
            #if hist.GetBinContent(binNr) > 0 : hist.SetBinContent(binNr, (hist.GetBinContent(binNr) -1)*100 )
            if hist.GetBinContent(binNr) > 0 : hist.SetBinContent(binNr, (hist.GetBinContent(binNr) - nominalHist.GetBinContent(binNr)))



    upperRatioHist.GetYaxis().SetRangeUser( min(histNumpyTools.histToNPArray( lowerRatioHist)) *1.1, max(histNumpyTools.histToNPArray( upperRatioHist)) *1.1)



    upperRatioHist.Draw()
    lowerRatioHist.Draw("same")


    tCanvas.Update()
    
    if not os.path.exists( outputDir): os.mkdir(outputDir)

    canvasPrintPath = os.path.join(outputDir,title)
    tCanvas.Print(canvasPrintPath+".pdf")
    tCanvas.Print(canvasPrintPath+".png")
    tCanvas.Print(canvasPrintPath+".root")

    ROOT.gROOT.SetBatch(initialBatchStatus)

    return tCanvas, legend



def makeHistVariationDict(dsidTheorySysDict, DSIDList , PMGWeightVariationsDict , nominalList, flavor="All", prefix="", normalizeToNominal = True):
    # We have a set of TH1 histogram variations for a number of DSIDs
    # The histogram variations are one TH1 for PMG weight
    # Different DSIDs might have differently named PMG weight names, that we consider to be the same weight variations
    # e.g. we consider 'muR=2.0,muF=1.0' and 'MUR2_MUF1_PDF261000' to be the same vairations
    # the PMGWeightVariationsDict defines how these different PMG weight names are matched to each other
    #
    #   PMGWeightVariationsDict[nameOfTheoryWeightVariation]  = [ list of weight variation names for different samples that match to nameOfTheoryWeightVariation]
    #   e.g. 'muR=2.0,muF=1.0': ['muR=2.0,muF=1.0', 'MUR2_MUF1_PDF261000', ...]
    #
    #   The DSIDList defines the set of DSIDs that we consider here
    #   All of the TH1 associated with a DSID in the DSIDList and one common variation name (i.e. one particular element from PMGWeightVariationsDict.keys() )
    #   Are added to one output TH1
    #   
    #   The output here is a dict with
    #   theoryVarHistDict[ PMGVariationName] = TH1


    def selectMatchingHistogram( histDictDict, keysToCheck ):
        for aKeyToCheck in keysToCheck:
            if prefix+aKeyToCheck in histDictDict.keys():

                if histDictDict[prefix+aKeyToCheck][flavor].Integral() == 0: continue # import the debugger and instruct it to stop here
                return histDictDict[prefix+aKeyToCheck][flavor]
        return None 

    theoryVarHistDict = {}

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    for DSID in DSIDList:

        if str(DSID) not in dsidTheorySysDict.keys(): continue

        for weightVariation in PMGWeightVariationsDict.keys():

            # find the matching theory variation histogram
            theoryHist = selectMatchingHistogram( dsidTheorySysDict[str(DSID)], PMGWeightVariationsDict[weightVariation] )
            #if theoryHist is None: theoryHist = selectMatchingHistogram( dsidTheorySysDict[str(DSID)], nominalList )
            if theoryHist is None: theoryHist = dsidTheorySysDict[str(DSID)]['Nominal'][flavor]

            if normalizeToNominal : 
                tempHist = theoryHist.Clone("tempHist")
                tempHist.Scale(dsidTheorySysDict[str(DSID)]['Nominal'][flavor].Integral() /tempHist.Integral() )
            else: tempHist = theoryHist


            if weightVariation not in theoryVarHistDict: theoryVarHistDict[weightVariation] = tempHist.Clone(weightVariation)
            else:                                  theoryVarHistDict[weightVariation].Add(tempHist)

    #upperHist, lowerHist  = makeEnvelopeHistograms( weightVariationHistDict.values())

    return theoryVarHistDict


def getWeightVariationNames():

    #weightVariationDict = {    "Nominal" : ['MUR1_MUF1_PDF261000', 'muR=0.10000E+01muF=0.10000E+01', 'nominal'] , 
    #"interPDF" : ['MUR1_MUF1_PDF13000', 'MUR1_MUF1_PDF25300', 'MUR1_MUF1_PDF269000', 'MUR1_MUF1_PDF270000', 'PDFset=11000', 'PDFset=11068', 'PDFset=13100', 'PDFset=13165', 'PDFset=25200', 'PDFset=25300', 'PDFset=90400', 'PDFset=91400'],
    #"QCDScales" : ['MUR0.5_MUF0.5_PDF261000', 'MUR0.5_MUF1_PDF261000', 'MUR1_MUF0.5_PDF261000', 'MUR1_MUF2_PDF261000', 'MUR2_MUF1_PDF261000', 'MUR2_MUF2_PDF261000', 'muR=0.10000E+01muF=0.20000E+01', 'muR=0.10000E+01muF=0.50000E+00', 'muR=0.20000E+01muF=0.10000E+01', 'muR=0.20000E+01muF=0.20000E+01', 'muR=0.5,muF=0.5', 'muR=0.5,muF=1.0', 'muR=0.50000E+00muF=0.10000E+01', 'muR=0.50000E+00muF=0.50000E+00', 'muR=1.0,muF=0.5', 'muR=1.0,muF=2.0', 'muR=2.0,muF=1.0', 'muR=2.0,muF=2.0'],
    #"intraPDF" : ['MUR1_MUF1_PDF261001', 'MUR1_MUF1_PDF261002', 'MUR1_MUF1_PDF261003', 'MUR1_MUF1_PDF261004', 'MUR1_MUF1_PDF261005', 'MUR1_MUF1_PDF261006', 'MUR1_MUF1_PDF261007', 'MUR1_MUF1_PDF261008', 'MUR1_MUF1_PDF261009', 'MUR1_MUF1_PDF261010', 'MUR1_MUF1_PDF261011', 'MUR1_MUF1_PDF261012', 'MUR1_MUF1_PDF261013', 'MUR1_MUF1_PDF261014', 'MUR1_MUF1_PDF261015', 'MUR1_MUF1_PDF261016', 'MUR1_MUF1_PDF261017', 'MUR1_MUF1_PDF261018', 'MUR1_MUF1_PDF261019', 'MUR1_MUF1_PDF261020', 'MUR1_MUF1_PDF261021', 'MUR1_MUF1_PDF261022', 'MUR1_MUF1_PDF261023', 'MUR1_MUF1_PDF261024', 'MUR1_MUF1_PDF261025', 'MUR1_MUF1_PDF261026', 'MUR1_MUF1_PDF261027', 'MUR1_MUF1_PDF261028', 'MUR1_MUF1_PDF261029', 'MUR1_MUF1_PDF261030', 'MUR1_MUF1_PDF261031', 'MUR1_MUF1_PDF261032', 'MUR1_MUF1_PDF261033', 'MUR1_MUF1_PDF261034', 'MUR1_MUF1_PDF261035', 'MUR1_MUF1_PDF261036', 'MUR1_MUF1_PDF261037', 'MUR1_MUF1_PDF261038', 'MUR1_MUF1_PDF261039', 'MUR1_MUF1_PDF261040', 'MUR1_MUF1_PDF261041', 'MUR1_MUF1_PDF261042', 'MUR1_MUF1_PDF261043', 'MUR1_MUF1_PDF261044', 'MUR1_MUF1_PDF261045', 'MUR1_MUF1_PDF261046', 'MUR1_MUF1_PDF261047', 'MUR1_MUF1_PDF261048', 'MUR1_MUF1_PDF261049', 'MUR1_MUF1_PDF261050', 'MUR1_MUF1_PDF261051', 'MUR1_MUF1_PDF261052', 'MUR1_MUF1_PDF261053', 'MUR1_MUF1_PDF261054', 'MUR1_MUF1_PDF261055', 'MUR1_MUF1_PDF261056', 'MUR1_MUF1_PDF261057', 'MUR1_MUF1_PDF261058', 'MUR1_MUF1_PDF261059', 'MUR1_MUF1_PDF261060', 'MUR1_MUF1_PDF261061','MUR1_MUF1_PDF261062', 'MUR1_MUF1_PDF261063', 'MUR1_MUF1_PDF261064', 'MUR1_MUF1_PDF261065', 'MUR1_MUF1_PDF261066', 'MUR1_MUF1_PDF261067', 'MUR1_MUF1_PDF261068', 'MUR1_MUF1_PDF261069', 'MUR1_MUF1_PDF261070', 'MUR1_MUF1_PDF261071', 'MUR1_MUF1_PDF261072', 'MUR1_MUF1_PDF261073', 'MUR1_MUF1_PDF261074', 'MUR1_MUF1_PDF261075', 'MUR1_MUF1_PDF261076', 'MUR1_MUF1_PDF261077', 'MUR1_MUF1_PDF261078', 'MUR1_MUF1_PDF261079', 'MUR1_MUF1_PDF261080', 'MUR1_MUF1_PDF261081', 'MUR1_MUF1_PDF261082', 'MUR1_MUF1_PDF261083', 'MUR1_MUF1_PDF261084', 'MUR1_MUF1_PDF261085', 'MUR1_MUF1_PDF261086', 'MUR1_MUF1_PDF261087', 'MUR1_MUF1_PDF261088', 'MUR1_MUF1_PDF261089', 'MUR1_MUF1_PDF261090', 'MUR1_MUF1_PDF261091', 'MUR1_MUF1_PDF261092', 'MUR1_MUF1_PDF261093', 'MUR1_MUF1_PDF261094', 'MUR1_MUF1_PDF261095', 'MUR1_MUF1_PDF261096', 'MUR1_MUF1_PDF261097', 'MUR1_MUF1_PDF261098', 'MUR1_MUF1_PDF261099', 'MUR1_MUF1_PDF261100', 'PDFset=260000', 'PDFset=260001', 'PDFset=260002', 'PDFset=260003', 'PDFset=260004', 'PDFset=260005', 'PDFset=260006', 'PDFset=260007', 'PDFset=260008', 'PDFset=260009', 'PDFset=260010', 'PDFset=260011', 'PDFset=260012', 'PDFset=260013', 'PDFset=260014', 'PDFset=260015', 'PDFset=260016', 'PDFset=260017', 'PDFset=260018', 'PDFset=260019', 'PDFset=260020', 'PDFset=260021', 'PDFset=260022', 'PDFset=260023', 'PDFset=260024', 'PDFset=260025', 'PDFset=260026', 'PDFset=260027', 'PDFset=260028', 'PDFset=260029', 'PDFset=260030', 'PDFset=260031', 'PDFset=260032', 'PDFset=260033', 'PDFset=260034', 'PDFset=260035', 'PDFset=260036', 'PDFset=260037', 'PDFset=260038', 'PDFset=260039', 'PDFset=260040', 'PDFset=260041', 'PDFset=260042', 'PDFset=260043', 'PDFset=260044', 'PDFset=260045', 'PDFset=260046', 'PDFset=260047', 'PDFset=260048', 'PDFset=260049', 'PDFset=260050', 'PDFset=260051', 'PDFset=260052', 'PDFset=260053', 'PDFset=260054', 'PDFset=260055', 'PDFset=260056', 'PDFset=260057', 'PDFset=260058', 'PDFset=260059', 'PDFset=260060', 'PDFset=260061', 'PDFset=260062', 'PDFset=260063', 'PDFset=260064', 'PDFset=260065', 'PDFset=260066', 'PDFset=260067', 'PDFset=260068', 'PDFset=260069', 'PDFset=260070', 'PDFset=260071', 'PDFset=260072', 'PDFset=260073', 'PDFset=260074', 'PDFset=260075', 'PDFset=260076', 'PDFset=260077', 'PDFset=260078', 'PDFset=260079', 'PDFset=260080', 'PDFset=260081', 'PDFset=260082', 'PDFset=260083', 'PDFset=260084', 'PDFset=260085', 'PDFset=260086', 'PDFset=260087', 'PDFset=260088', 'PDFset=260089', 'PDFset=260090', 'PDFset=260091', 'PDFset=260092', 'PDFset=260093', 'PDFset=260094', 'PDFset=260095', 'PDFset=260096', 'PDFset=260097', 'PDFset=260098', 'PDFset=260099', 'PDFset=260100']}

    QCDScaleDict = {'muR=0.5,muF=0.5' : ['muR=0.5,muF=0.5', 'MUR0.5_MUF0.5_PDF261000', 'muR=0.50000E+00muF=0.50000E+00' ],
                    'muR=0.5,muF=1.0' : ['muR=0.5,muF=1.0', 'MUR0.5_MUF1_PDF261000',   'muR=0.50000E+00muF=0.10000E+01'  ],
                    'muR=1.0,muF=0.5' : ['muR=1.0,muF=0.5', 'MUR1_MUF0.5_PDF261000',   'muR=0.10000E+01muF=0.50000E+00' ],
                    'muR=1.0,muF=2.0' : ['muR=1.0,muF=2.0', 'MUR1_MUF2_PDF261000',     'muR=0.10000E+01muF=0.20000E+01' ],
                    'muR=2.0,muF=1.0' : ['muR=2.0,muF=1.0', 'MUR2_MUF1_PDF261000',     'muR=0.20000E+01muF=0.10000E+01' ],
                    'muR=2.0,muF=2.0' : ['muR=2.0,muF=2.0', 'MUR2_MUF2_PDF261000',     'muR=0.20000E+01muF=0.20000E+01' ] }

    PDFDict =       {'MUR1_MUF1_PDF13000'  : ['MUR1_MUF1_PDF13000'],
                     'MUR1_MUF1_PDF25300'  : ['MUR1_MUF1_PDF25300'],
                     'MUR1_MUF1_PDF269000' : ['MUR1_MUF1_PDF269000'],
                     'MUR1_MUF1_PDF270000' : ['MUR1_MUF1_PDF270000'],
                     'PDFset=11000'        : ['PDFset=11000'],
                     'PDFset=11068'        : ['PDFset=11068'],
                     'PDFset=13100'        : ['PDFset=13100'],
                     'PDFset=13165'        : ['PDFset=13165'],
                     'PDFset=25200'        : ['PDFset=25200'],
                     'PDFset=25300'        : ['PDFset=25300'],
                     'PDFset=90400'        : ['PDFset=90400'],
                     'PDFset=91400'        : ['PDFset=91400'] }

    #intraPDFDict = {}
    for aNumber in xrange(0,101):   PDFDict[ "PDFset=%04d" % aNumber ] = [ "MUR1_MUF1_PDF261%03d" % aNumber, "PDFset=260%03d" % aNumber]

    weightVariationDict = {"QCD_Shape" : QCDScaleDict, 
                           #"interPDF" : interPDFDict, 
                           "PDF_Shape" : PDFDict }

    nominalList = ['MUR1_MUF1_PDF261000', 'muR=0.10000E+01muF=0.10000E+01']


    return weightVariationDict, nominalList


def addTheoryVariationsToMasterHistDict( pmgWeightDict, masterHistDict,  analysisMapping, region = "ZXSR", backgroundtypes = ["H4l", "ZZ"], prefix="PMG_", outputEnvelopeDir = None):
    # pmgWeightDict and masterHistDict are both tree like dicts, but with slightly different keys
    # masterHistDict[ signal or validation region][ event type like 'H4l', 'ZZ', etc][ systematic variation like, 'nominal', 'MUONS_ID1up', etc][ flavor like 'All', '4mu', etc] = ROOT.TH1
    # pmgWeightDict[  signal or validation region][ DSID, e.g. '345060'             ][ PMG weight like 'muR=0.5,muF=0.5', or 'PDFset=260012'   ][ flavor like 'All', '4mu', etc] = ROOT.TH1
    #   
    # analysisMapping describes the mapping from 'DSID' to the event type as used in masterHistDict
    # e.g. analysisMapping['345060'] = 'H4l'
    #
    # so what we do here is combine to combine the different DSIDs according to the mapping, while also using the PMG weight to calculate '1up' and '1down' variations for the theory systematics
    # 
    # the function getWeightVariationNames yields a dict 'weightVariationDict' that defines the types of theory systematics that we consider, and how they relate to the PMG weights
    # weightVariationDict[theorySystematic][ PMG weight type] = [list of names we associate with this PMG weight type]
    # we use the mapping {PMG weight type : [list of names we associate with this PMG weight type] } 
    # because the same pmg weight variation has different names in the PMGTruthWeightTool: https://gitlab.cern.ch/jrobinso/athena/-/tree/21.2/PhysicsAnalysis/AnalysisCommon/PMGTools/PMGTools
    #  
    # For example we consider : 'muR=0.5,muF=0.5', 'MUR0.5_MUF0.5_PDF261000', 'muR=0.50000E+00muF=0.50000E+00'  as the same QCD scale varaition and refer to it as the 'muR=0.5,muF=0.5' variation
    #                            and 'MUR1_MUF1_PDF261005', 'PDFset=260005' as the same variation of the 260000 PDF set weight and refer to it as the 'PDFset=260005' variation
    #
    # Additional getWeightVariationNames provides also a list of 'nominal' variatons. i.e. the weight variation include a 'nominal' weight point, but that one is not necessary named 'nominal'
    #  
    #
    # The function 'makeHistVariationDict' does the combining, it takes the  pmgWeightDict[region] sub-dicts as input, 
    # together the { PMG weight type = [list of names we associate with this PMG weight type]} PMG weight name mappings and hte list of nominal variations
    #
    # The 1up and 1down shape variations are given as the upper and lower envelopes of the set of variations of kinematic distributions
    # We could select the envelopes of each DSID, but I deem it to be more appropariate to of set of variations of the ZZ and H4l backgrounds each, and then take the envelope of those
    # One obstacle in that is that the the same vriation for different DSIDs might have different names
    # Here the 'makeHistVariationDict' together with the output from 'getWeightVariationNames' makes sure that that these are properly combined,
    # So that we have a set of variations for ZZ and H4l
    #
    #
    # the current function 'addTheoryVariationsToMasterHistDict' takes care to loop over all of the relevant theprySystematics, quadruplet flavors, and background types
    # it also builds the theory variation hists from the envelope of the output from 'makeHistVariationDict' and sorts them properly into the masterHistDict 


    weightVariationDict, nominalList = getWeightVariationNames()

    flavors = masterHistDict[region].values()[0].values()[0].keys()   

    for background in backgroundtypes:

        DSIDList = analysisMapping[background]

        for systematicType in weightVariationDict.keys(): # weightVariationDict, QCDScaleDict, or interPDFDict

            for flavor in flavors: # all, 4e, 2e2mu, 2mu2e, 4mu

                histVariationDict = makeHistVariationDict(pmgWeightDict[region], DSIDList , weightVariationDict[systematicType] , nominalList, flavor=flavor, prefix=prefix, normalizeToNominal = True)

                #if "intra" in systematicType:   # envelope function is slightly different for intraPdf estimate
                #    upperEnvelopeHist , lowerEnvelopeHist = makeEnvelopeHistograms(histVariationDict.values() , upperEnvelopeFunction = lambda x : np.percentile(x,84.14,axis=0), lowerEnvelopeFunction = lambda x : np.percentile(x,15.87,axis=0) )

                upperEnvelopeHist , lowerEnvelopeHist = makeEnvelopeHistograms(histVariationDict.values() , upperEnvelopeFunction = lambda x : x.max(axis=0), lowerEnvelopeFunction = lambda x : x.min(axis=0))

                upperHistName = "_".join([region, background , systematicType+"1up", flavor ])
                upperEnvelopeHist.SetName( upperHistName )#; upperEnvelopeHist.SetTitle( upperHistName )

                lowerHistName = "_".join([region, background , systematicType+"1down", flavor ])
                lowerEnvelopeHist.SetName( lowerHistName )#; lowerEnvelopeHist.SetTitle( lowerHistName )

                masterHistDict[region][background][systematicType+"1up"][flavor] = upperEnvelopeHist
                masterHistDict[region][background][systematicType+"1down"][flavor] = lowerEnvelopeHist

                if outputEnvelopeDir is not None: 
                    canvasTitle = "_".join(["TheorySyst", region, background , systematicType, flavor ])
                    nominalHist = masterHistDict[region][background]["Nominal"][flavor]
                    visualizeEnvelopeHistogram( upperEnvelopeHist, lowerEnvelopeHist, histVariationDict.values(), outputEnvelopeDir, nominalHist, title = canvasTitle)

    return None

def addTheoryVariationsToMasterHistDict2( pmgWeightDict, masterHistDict,  analysisMapping, region = "ZXSR", backgroundtypes = ["H4l", "ZZ"], prefix="PMG_", outputEnvelopeDir = None):

    weightVariationDict, nominalList = getWeightVariationNames()

    flavors = masterHistDict[region].values()[0].values()[0].keys()   

    for background in backgroundtypes:

        DSIDList = analysisMapping[background]

        for systematicType in weightVariationDict.keys(): # weightVariationDict, QCDScaleDict, or interPDFDict

            for flavor in flavors: # all, 4e, 2e2mu, 2mu2e, 4mu

                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
                nominalHist = masterHistDict[region][background]["Nominal"][flavor]

                aggregateUpperEnvelopeHist = nominalHist.Clone(re.sub("Nominal", systematicType +"1Up" , nominalHist.GetName()))
                aggregateLowerEnvelopeHist = nominalHist.Clone(re.sub("Nominal", systematicType +"1Down" , nominalHist.GetName()))

                aggregateUpperEnvelopeHist.Reset()
                aggregateLowerEnvelopeHist.Reset()

                for DSID in DSIDList: 

                    if str(DSID) not in pmgWeightDict[region].keys(): continue

                    histVariationDict = makeHistVariationDict(pmgWeightDict[region], [DSID] , weightVariationDict[systematicType] , nominalList, flavor=flavor, prefix=prefix, normalizeToNominal = True)

                    #if "intra" in systematicType:   # envelope function is slightly different for intraPdf estimate
                    #    upperEnvelopeHist , lowerEnvelopeHist = makeEnvelopeHistograms(histVariationDict.values() , upperEnvelopeFunction = lambda x : np.percentile(x,84.14,axis=0), lowerEnvelopeFunction = lambda x : np.percentile(x,15.87,axis=0) )
                    #else: 
                    #    upperEnvelopeHist , lowerEnvelopeHist = makeEnvelopeHistograms(histVariationDict.values() , upperEnvelopeFunction = lambda x : x.max(axis=0), lowerEnvelopeFunction = lambda x : x.min(axis=0))

                    upperEnvelopeHist , lowerEnvelopeHist = makeEnvelopeHistograms(histVariationDict.values() , upperEnvelopeFunction = lambda x : x.max(axis=0), lowerEnvelopeFunction = lambda x : x.min(axis=0))

                    aggregateUpperEnvelopeHist.Add(upperEnvelopeHist)
                    aggregateLowerEnvelopeHist.Add(lowerEnvelopeHist)

                    #upperHistName = "_".join([region, background , systematicType+"1up", flavor ])
                    #upperEnvelopeHist.SetName( upperHistName )#; upperEnvelopeHist.SetTitle( upperHistName )

                    #lowerHistName = "_".join([region, background , systematicType+"1down", flavor ])
                    #lowerEnvelopeHist.SetName( lowerHistName )#; lowerEnvelopeHist.SetTitle( lowerHistName )

                masterHistDict[region][background][systematicType+"1up"][flavor]   = aggregateUpperEnvelopeHist
                masterHistDict[region][background][systematicType+"1down"][flavor] = aggregateLowerEnvelopeHist

                if outputEnvelopeDir is not None: 
                    canvasTitle = "_".join(["TheorySyst", region, background , systematicType, flavor ])
                    nominalHist = masterHistDict[region][background]["Nominal"][flavor]
                    visualizeEnvelopeHistogram( aggregateUpperEnvelopeHist, aggregateLowerEnvelopeHist, histVariationDict.values(), outputEnvelopeDir, nominalHist, title = canvasTitle)
    return None



if __name__ == '__main__':

    import plotPostProcess as postProcess

    import makeHistDict as makeHistDict # things to fill what I call later the masterHistDict

    import functions.rootDictAndTDirTools as rootDictAndTDirTools

    myDSIDHelper = postProcess.DSIDHelper()
    myDSIDHelper.importMetaData( "../../metadata/md_bkg_datasets_mc16e_All.txt"  ) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    #myDSIDHelper.setMappingOfChoice( "DSIDtoDSIDMapping" )
    myDSIDHelper.setMappingOfChoice( "analysisMapping" )

    #inputDataFile = "../../post_20200915_171012_mc16ade_ZX_Run2_SignalBackgroundDataFeb2020Unblinded.root"
    #inputDataFile = "../../post_20200809_203927__ZX_Run2_MainBackground_PMGWeights.root"
    #inputDataFile = "ZX_PostProcess_PMGWeightExampleInput.root"
    #inputDataFile = "../../post_20201230_204837__ZX_Run2_Jul2020_ZZ_364251_Sys_PMGWeights.root"

    inputDataFile = "../../post_20200915_171012_mc16ade_ZX_Run2_SignalBackgroundDataFeb2020UnblindedPMGFixed.root"


    postProcessedData = ROOT.TFile(inputDataFile,"READ"); # open the file with te data from the ZdZdPostProcessing

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)

    DSIDsToConsider = []; backgroundTypes = []
    #DSIDsToConsider.extend( myDSIDHelper.analysisMapping["H4l"]) ; backgroundTypes.append("H4l")
    DSIDsToConsider.extend( myDSIDHelper.analysisMapping["ZZ"]) ; backgroundTypes.append("ZZ")
    DSIDsToConsider.remove(364251)

    DSIDsToConsider = [364251]

    channelMapping = { "ZXSR" : "ZXSR"}

    mcCampaign = "mc16ade"

    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
    pmgWeightDict  = copy.deepcopy(masterHistDict)  

    nRelevantHistsProcessed = 0

    import time # for measuring execution time
    import reportMemUsage as reportMemUsage
    startTime = time.time()


    for path, myTObject in plotPostProcess.preselectTDirsForProcessing(postProcessedData, permittedDSIDs = DSIDsToConsider, systematicsTags = ["PMG_","Nominal"], systematicsVetoes = None, newOwnership = None):
    #for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if makeHistDict.skipTObject(path, myTObject, selectChannels = channelMapping.keys() ): continue # skip non-relevant histograms
        if "EG_RESOLUTION" in path: continue
        if "EG_SCALE" in path: continue
        if "EL_EFF" in path: continue
        if "MUONS_" in path: continue
        if "MUON_" in path: continue
        if "PileupWeight" in path: continue

        if myTObject.Integral() == 0: continue


        if   "PMG_"    in path: pmgWeightDict = makeHistDict.fillHistDict(path, myTObject , mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = pmgWeightDict, customMapping=myDSIDHelper.DSIDtoDSIDMapping) 
        elif "Nominal" in path: 
            pmgWeightDict = makeHistDict.fillHistDict(path, myTObject , mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = pmgWeightDict, customMapping=myDSIDHelper.DSIDtoDSIDMapping) 
            masterHistDict= makeHistDict.fillHistDict(path, myTObject , mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = masterHistDict) 
        else: continue
        
        nRelevantHistsProcessed += 1

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)

    
    reportMemUsage.reportMemUsage(startTime = startTime)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    addTheoryVariationsToMasterHistDict( pmgWeightDict, masterHistDict,  myDSIDHelper.analysisMapping, region = "ZXSR", backgroundtypes = backgroundTypes, prefix="PMG_", outputEnvelopeDir = "theorySystOverview")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

