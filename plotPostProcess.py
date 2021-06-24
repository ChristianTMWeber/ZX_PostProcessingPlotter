#############################
#   
# python programm to make plotsout of the post processing outputs   
#
# run as:       python plotPostProcess.py exampleZdZdPostProcessOutput.root --mcCampaign mc16ade
#
# to run debugger: python -m pdb
#
#############################



import ROOT # to do all the ROOT stuff
#import numpy as np # good ol' numpy
import warnings # to warn about things that might not have gone right
import itertools # to cycle over lists in a nice automated way
import re # to do regular expression matching
import copy # for making deep copies
import argparse # to parse command line options
#import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
#import functions.RootTools as RootTools# root tool that I have taken from a program by Turra
import numpy as np # good ol' numpy
import os
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
import time # for measuring execution time

import functions.histNumpyTools as histNumpyTools # to convert ROOT.TH1 histograms to numpy arrays
from functions.TFileCache import TFileCache

import makeReducibleShapes.makeReducibleShapes as makeReducibleShapes

from functions.varibleSizeRebinHelper import varibleSizeRebinHelper # to help me make variable sized bins
import functions.rootDictAndTDirTools as rootDictAndTDirTools

class DSIDHelper:

    # define a groupings of DSIDS, e.g. if we wanna group DSIDs by 'physicsProcess', then one of those groups is called "H->ZZ*->4l" and contains the DSIDs 341964, 341947, etc...
    physicsProcess={"H->ZZ*->4l" : [341964, 341947, 345060, 341488, 345046, 345047, 345048, 345066, 344973, 344974],
                      "ZZ*->4l" :    [364250, 364251, 364252, 361603, 342556, 343232, 343212, 343213, 345708, 345709],
                      "Reducible (Z+Jets, WZ, ttbar)"  : [364114, 364115, 364116, 364117, 364118, 364119, 364120, 364121, 364122, 
                                                          364123, 364124, 364125, 364126, 364127, 364100, 364101, 364102, 364103, 
                                                          364104, 364105, 364106, 364107, 364108, 364109, 364110, 364111, 364112, 
                                                          364113, 364128, 364129, 364130, 364131, 364132, 364133, 364134, 364135, 
                                                          364136, 364137, 364138, 364139, 364140, 364141, 361601, 410472],
                       #"VVV/VBS" : [364248, 364247, 364245, 364243, 364364],
                       #"Z+(ttbar/J/Psi/Upsilon)" : [410142],
                       "VVV, tt+Z": [364248, 364247, 364245, 364243, 364364,
                                     410142]
                    }

    physicsProcessSignal = {"ZZd, m_{Zd} = 15GeV" : [343234],
                            "ZZd, m_{Zd} = 20GeV" : [343235],
                            "ZZd, m_{Zd} = 25GeV" : [343236],
                            "ZZd, m_{Zd} = 30GeV" : [343237],
                            "ZZd, m_{Zd} = 35GeV" : [343238],
                            "ZZd, m_{Zd} = 40GeV" : [343239],
                            "ZZd, m_{Zd} = 45GeV" : [343240],
                            "ZZd, m_{Zd} = 50GeV" : [343241],
                            "ZZd, m_{Zd} = 55GeV" : [343242],
                            "ZdZd, m_{Zd} =0.5GeV" : [302073],
                            "ZdZd, m_{Zd} =  1GeV" : [302074],
                            "ZdZd, m_{Zd} =  2GeV" : [302075],
                            "ZdZd, m_{Zd} =  5GeV" : [302076],
                            "ZdZd, m_{Zd} = 10GeV" : [302077],
                            "ZdZd, m_{Zd} = 15GeV" : [302078],
                            "ZdZd, m_{Zd} = 20GeV" : [302079],
                            "ZdZd, m_{Zd} = 25GeV" : [302080],
                            "ZdZd, m_{Zd} = 30GeV" : [302081],
                            "ZdZd, m_{Zd} = 35GeV" : [302082],
                            "ZdZd, m_{Zd} = 40GeV" : [302083],
                            "ZdZd, m_{Zd} = 45GeV" : [302084],
                            "ZdZd, m_{Zd} = 50GeV" : [302085],
                            "ZdZd, m_{Zd} = 55GeV" : [302086],
                            "ZdZd, m_{Zd} = 60GeV" : [302087],
                            "Za, m_{a} =  1GeV" : [451324],
                            "Za, m_{a} =  2GeV" : [451325],
                            "Za, m_{a} =2.5GeV" : [451326],
                            "Za, m_{a} =  4GeV" : [451327],
                            "Za, m_{a} =  6GeV" : [451328],
                            "Za, m_{a} =  8GeV" : [451329],
                            "Za, m_{a} = 10GeV" : [451330],
                            "Za, m_{a} = 15GeV" : [451331, 451332],
                            "Za, m_{a} = 20GeV" : [451333, 451334],
                            "Za, m_{a} = 25GeV" : [451335, 451336],
                            "Za, m_{a} = 30GeV" : [451337, 451338]}


    colorMap = {"H->ZZ*->4l" : ROOT.kRed  , "ZZ*->4l" :   ROOT.kAzure+1 ,
                      "Reducible (Z+Jets, WZ, ttbar)"  : ROOT.kYellow , "VVV/VBS" : ROOT.kCyan,
                       "Z+(ttbar/J/Psi/Upsilon)" : ROOT.kGreen, "VVV, tt+Z" : ROOT.kGreen , 
                       "H4l"  : ROOT.kRed  , "ZZ" :   ROOT.kAzure+1,   "const" : ROOT.kYellow} # colors for the analysisMapping

    physicsSubProcess = {"ggH" : [345060], "VBFH":[341488], "WH" : [341964], "ZH" : [341947],
                     "ggZH" : [345066], "ttH125" : [345046, 345047, 345048], "bbH" : [344973, 344974],
                     "qq->ZZ*->4l" : [364250, 364251, 364252], "gg->ZZ*->4l" : [345708, 345709],
                     "ZZZ" : [364248, 364247], "WZZ" : [364245], "WWZ" : [364243], 
                     "lllljj" : [364364], "ttll" : [410142], "WZ" : [361601], "ttbar" : [410472],
                     "Z+Jets (Z->ee, CVetoBVeto)"      : [364114, 364117, 364120, 364123] ,
                     "Z+Jets (Z->mumu, CVetoBVeto)"    : [364100, 364103, 364106, 364109] ,
                     "Z+Jets (Z->tautau, CVetoBVeto)"  : [364128, 364131, 364134, 364137] ,
                     "Z+Jets (Z->ee, CFilterBVeto)"    : [364115, 364118, 364121, 364124] ,
                     "Z+Jets (Z->mumu, CFilterBVeto)"  : [364101, 364104, 364107, 364110] ,
                     "Z+Jets (Z->tautau, CFilterBVeto)": [364129, 364132, 364135, 364138] ,
                     "Z+Jets (Z->ee, BFilter)"         : [364116, 364119, 364122, 364125] ,
                     "Z+Jets (Z->mumu, BFilter)"       : [364102, 364105, 364108, 364111] ,
                     "Z+Jets (Z->tautau, BFilter)"     : [364130, 364133, 364136, 364139] ,
                     "Z+Jets (Z->ee, hight pT, no filters)"       : [364126, 364127] ,
                     "Z+Jets (Z->mumu, hight pT, no filters)"     : [364112, 364113] ,
                     "Z+Jets (Z->tautau, hight pT, no filters)"   : [364140, 364141] 
                     }

    analysisMapping =   {   "H4l"    : [341964, 341947, 345060, 341488, 345046, 345047, 345048, 345066, 344973, 344974],
                            "ZZ"     : [364250, 364251, 364252, 361603, 342556, 343232, 343212, 343213, 345708, 345709],
                            "Reducible"  : [364114, 364115, 364116, 364117, 364118, 364119, 364120, 364121, 364122, 
                                            364123, 364124, 364125, 364126, 364127, 364100, 364101, 364102, 364103, 
                                            364104, 364105, 364106, 364107, 364108, 364109, 364110, 364111, 364112, 
                                            364113, 364128, 364129, 364130, 364131, 364132, 364133, 364134, 364135, 
                                            364136, 364137, 364138, 364139, 364140, 364141, 361601, 410472],
                            "VVV_Z+ll" : [364248, 364247, 364245, 364243, 364364,
                                           410142],
                }

    ######################################################
    # Define some default or hardcoded values
    ######################################################


    # campaigns integrated luminosity,  complete + partial
    lumiMap = { "mc16a" : 36.21496, "mc16d" : 44.3074, "mc16e": 59.9372, "mc16ade": 139., "units" : "fb-1"}
    #taken by Justin from: https://twiki.cern.ch/twiki/bin/view/Atlas/LuminosityForPhysics#2018_13_TeV_proton_proton_placeh
    #2015: 3.21956 fb^-1 +- 2.1% (final uncertainty) (3.9 fb^-1 recorded)
    #2016: 32.9954 fb^-1 +- 2.2% (final uncertainty) (35.6 fb^-1 recorded)
    #2017: 44.3074 fb^-1 +- 2.4% (preliminary uncertainty) (46.9 fb^-1 recorded)
    #2018: 59.9372 fb^-1 +- 5% (uncertainty TBD, use this as a placeholder) (62.2 fb^-1 recorded)
    #Total: 140.46 fb^-1


    sumOfEventWeightsDict = {}

    mappingOfChoice = None
    mappingOfChoiceInverse = None

    def __init__(self):

        # make background and Signal mappings before we add in the signals to the more specified lists
        self.BackgroundAndSignal = {"Background" : [] , "Signal" : [] } 
        for DISDList in self.physicsProcess.values()       : self.BackgroundAndSignal["Background"].extend( DISDList )
        for DISDList in self.physicsProcessSignal.values() : self.BackgroundAndSignal["Signal"].extend( DISDList )
        self.BackgroundAndSignalByDSID    = self.makeReverseDict( self.BackgroundAndSignal);

        self.ZJetDSIDs = []
        for subProcess in self.physicsSubProcess:
            if "Z+Jets" in subProcess: self.ZJetDSIDs.extend( self.physicsSubProcess[subProcess] )
        
        # add the signal into the physics(Sub)Process
        self.physicsProcess.update( self.physicsProcessSignal )
        self.physicsSubProcess.update( self.physicsProcessSignal )
        self.analysisMapping.update( self.physicsProcessSignal )

        # make the reverse dicts so that we can look up things by DSID
        self.physicsProcessByDSID    = self.makeReverseDict( self.physicsProcess);
        self.physicsSubProcessByDSID = self.makeReverseDict( self.physicsSubProcess);
        self.analysisMappingByDSID = self.makeReverseDict( self.analysisMapping)
        self.physicsProcessSignalByDSID = self.makeReverseDict( self.physicsProcessSignal)
        self.DSIDtoDSIDMapping =  { DSID : str(DSID) for DSID in self.physicsProcessByDSID }

    def setMappingOfChoice(self, mapping ):


        if   mapping == "physicsProcess" :    self.mappingOfChoice = self.physicsProcessByDSID    ; self.mappingOfChoiceInverse = self.physicsProcess
        elif mapping == "physicsSubProcess" : self.mappingOfChoice = self.physicsSubProcessByDSID ; self.mappingOfChoiceInverse = self.physicsSubProcess
        elif mapping == "analysisMapping" :   self.mappingOfChoice = self.analysisMappingByDSID   ; self.mappingOfChoiceInverse = self.analysisMapping
        #elif mapping == "DSIDtoDSIDMapping" : self.mappingOfChoice = self.DSIDtoDSIDMapping       ; self.mappingOfChoiceInverse = self.DSIDtoDSIDMapping
        else:  warnings.warn("Key not supported, no mapping defined")     # self.mappingOfChoice = mapping

        return None

    def isSignalSample(self , KeyOrDSID ):

        if isinstance(KeyOrDSID,str) and re.match("\d{6}", KeyOrDSID ): KeyOrDSID = int(KeyOrDSID)

        if KeyOrDSID in self.physicsProcessSignalByDSID: return True
        elif KeyOrDSID in self.physicsProcessSignal: return True
        
        return False

    def colorizeHistsInDict(self, mergedSamplesDICT, fillStyleSetting = None, 
        fillColors = itertools.cycle([ ROOT.kViolet,   ROOT.kYellow,   ROOT.kCyan,   ROOT.kBlue,   ROOT.kRed,   ROOT.kMagenta,   ROOT.kPink,   ROOT.kOrange,   ROOT.kSpring,   ROOT.kGreen,   ROOT.kTeal,   ROOT.kAzure,
                                       ROOT.kViolet-6, ROOT.kYellow-6, ROOT.kCyan-6, ROOT.kBlue-6, ROOT.kRed-6, ROOT.kMagenta-6, ROOT.kPink-6, ROOT.kOrange-6, ROOT.kSpring-6, ROOT.kGreen-6, ROOT.kTeal-6, ROOT.kAzure-6,
                                       ROOT.kViolet-2, ROOT.kYellow-2, ROOT.kCyan-2, ROOT.kBlue-2, ROOT.kRed-2, ROOT.kMagenta-2, ROOT.kPink-2, ROOT.kOrange-2, ROOT.kSpring-2, ROOT.kGreen-2, ROOT.kTeal-2, ROOT.kAzure-2,]) 
        ):

        #if not isinstance(mergedSamplesDICT, dict ): erroe

        for process in mergedSamplesDICT.keys(): 

            color = self.colorMap.get(process) # get( X ) returns 'None' if X is not among the keys of the dict

            if color is None: # if 'process' was not among the keys of the colorMap, pick a color and add it to the dict
                color = fillColors.next()
                self.colorMap[process] = color
            

            if fillStyleSetting is None : 
                if self.isSignalSample( process ): fillStyle = 3345 # make signal shaded 
                else:                                      fillStyle = 1001 # 1001 - Solid Fill: https://root.cern.ch/doc/v608/classTAttFill.html

            else: fillStyle = fillStyleSetting

            mergedSamplesDICT[process].SetFillStyle( fillStyle )  
            mergedSamplesDICT[process].SetFillColor( color )

        #elif isinstance(mergedSamplesDICT, list ): # if we happen to color a list of hists, we will just iterate over our colors
        #    for hist in mergedSamplesDICT.keys():    hist.SetFillColor(fillColors.next())

        return None


    def fillSumOfEventWeightsDict(self, TDir):

        if isinstance(TDir, str): # if we got a filename, instead of a ROOT.TFile, open it here, call fillSumOfEventWeightsDict and close it again
            tempTFile = ROOT.TFile(TDir,"READ")
            self.fillSumOfEventWeightsDict(tempTFile)
            tempTFile.Close()
            return None

        TDirKeys = TDir.GetListOfKeys() # output is a TList

        for TKey in TDirKeys: 
            weightHistCandidate =  TDir.Get(TKey.GetName()) # this is how I access the element that belongs to the current TKey

            if isinstance(weightHistCandidate, ROOT.TDirectoryFile ): continue

            if isinstance(weightHistCandidate, ROOT.TH1 ) and "sumOfWeights" in TKey.GetName():

                DSID = re.search("\d{6}", TKey.GetName() ).group() # if we found a regular expression
                DSID = int(DSID)

                sumAODWeights = weightHistCandidate.GetBinContent(weightHistCandidate.GetXaxis().FindBin("sumOfEventWeights_xAOD"))

                if DSID in self.sumOfEventWeightsDict.keys(): self.sumOfEventWeightsDict[DSID] += sumAODWeights
                else:                                         self.sumOfEventWeightsDict[DSID] =  sumAODWeights
                
        return None

    def getMCScale(self, DSID, mcTag = None):

        assert( self.sumOfEventWeightsDict), "sumOfEventWeightsDict is empty, please fill it with the method 'fillSumOfEventWeightsDict' "

        if mcTag is None: mcTag = self.mcTag

        DSID = int(DSID)

        if DSID == 0 : return 1. # zero indicates data, and will not be scaled

        prod = self.metaDataDict[DSID]["crossSection"] * self.metaDataDict[DSID]["kFactor"] * self.metaDataDict[DSID]["genFiltEff"]

        # remember: the metadata stores the cross section in nano barn, and the luminosity if in 1/fb. Th 1E6 factor scales the cross section from nb to fb.
        scale = self.lumiMap[mcTag] * 1000000. * prod / self.sumOfEventWeightsDict[int(DSID)] 

        # posthoc hack to display the plots with the postfit background expectation, to the H4lNorm nuisacne parameter in the fit-
        #if  int(DSID) in self.analysisMapping["H4l"]: scale = scale * h4lScaling 

        return scale
    
    def makeReverseDict(self, inputDict):
        # Lets say we have a dict that goes like:
        # dict = { "key1" : [1, 2, 3], "key2" : [4,5], "key3" : 7}
        # this function makes a 'reverse dict' that goes like
        # reverseDict = {1 : "key1", 2 : "key1", 3 : "key1", 4 : "key2", 5 : "key2", 7 : "key3"}

        reverseDict = {}

        for key in inputDict.keys():
        # distinguish between lists / ntuples and things that are not that easily iterable
            if isinstance(inputDict[key], (list, tuple)):
                 for element in inputDict[key]:
                    if element in reverseDict: warnings.warn("Non unique reverse mapping in dict[key] -> key")
                    reverseDict[element] = key
            else: 
                if element in reverseDict: warnings.warn("Non unique reverse mapping in dict[key] -> key")
                reverseDict[inputDict[key]] = key
        return reverseDict


    def importMetaData(self,metadataFileLocation, mcTag = None):
        # parse the metada data from a metadata text file that we furnish
        # we expect the metadata file to have the stucture:
        # <DSID> <crossSection> <kFactor> <genFiltEff>   <...>
        # There the different values are seperate by whitespace
        # We ignore lines that do not start with a DSID (i.e. a 6 digit number)

        metaDataDict = {}
        physicsShort = {}

        DSIDPattern = re.compile("\d{6}") # DSIDs are numbers 6 digits long

        metadataFile = open(metadataFileLocation,'r')

        for line in metadataFile:
            if re.match(DSIDPattern, line): #if the line starts with out pattern
                splittedLine = line.split() # split at whitespace
                DSID = int(splittedLine[0])
                tempDict = { "crossSection" : float(splittedLine[1]),  
                             "kFactor"      : float(splittedLine[2]),
                             "genFiltEff"   : float(splittedLine[3])}

                metaDataDict[DSID] = tempDict
                physicsShort[DSID] = splittedLine[4]

        self.metaDataDict=metaDataDict
        self.physicsShort=physicsShort

        if mcTag is not None: self.mcTag = mcTag
        return metaDataDict, physicsShort

    def defineSequenceOfSortedSamples(self, sortedSamples ):
        # define a sequence of the sorted sampleSamples keys,
        # such that the background ones go first and the signal ones do second
        # among the background and signal ones each, have them sorted alphabetically

        backgroundKeys = [];         signalKeys = []

        for key in sortedSamples.keys():

            if self.isSignalSample( key ): signalKeys.append(key)
            else :  backgroundKeys.append(key)

        backgroundKeys.sort(); signalKeys.sort()

        # put the background and signal keys in lists, the background ones first
        completeKeyList = backgroundKeys
        completeKeyList.extend(signalKeys)

        return completeKeyList

    def idDSID(self, path):
        ## look for the following patter:  after a / , look for 6 digits preceeded by any number of character that are not /
        ## return the non / strings and the 6 digits
        #DSIDRegExpression = re.search("(?<=/)[^/]*\d{6}", path)
        DSIDRegExpression = re.search("/\d{6}/", path)

        # if we found such a pattern, select the six digits, or return 0
        if DSIDRegExpression: DSID = re.search("\d{6}", DSIDRegExpression.group() ).group() # if we found a regular expression
        else:                 DSID ="0" 

        return DSID

# end  class DSIDHelper



def idPlotTitle(path, DSIDHelper , DSID=None ):

    if DSID is None: DSID = DSIDHelper.idDSID(path)

    pathDSIDCleaned = path.replace("_"+DSID+"_","_")

    plotTitle = pathDSIDCleaned.split("/h_")[-1]

    return plotTitle

def irrelevantTObject(path, baseHist, requiredRootType = ROOT.TH1):

    #if "Nominal" not in path: return True
    if "Cutflow" in path: return True
    elif "cutflow" in path: return True
    elif "h_raw_" in path: return True
    elif "hraw_" in path: return True
    elif "pileupWeight" in path: return True
    elif isinstance( baseHist, ROOT.TH2 ): return True
    elif not isinstance( baseHist, requiredRootType ): return True
    elif "sumOfWeights" in path: return True

    return False


def mergeHistsByMapping(backgroundSamples, mappingDict) :
    # backgroundSamples - a list of tuples [(DSID, TH1),...]
    # mappingDict - a dictionary like { DSID1 : descriptor1, DSID2 : descriptor2, ...}
    # mergeHistsByMapping - combines TH1s with the common descriptors (as defined in the mapping dict) into a single TH1
    # e.g. let's say we have the samples [ (001, TH1a), (002, TH1b), (003, TH1c)] and the mapping { 001 : 'ggH', 002 : 'ggH', 003 : 'tt' }
    # output will be a dict structure { 'ggH' : TH1a+b, 'tt' : TH1c} , where TH1a+b is the sum of TH1a and TH1b

    mergedSamplesDICT = {} # store the merged samples here

    for aTuple in backgroundSamples: # loop over all the tuples

        DSID, histogram = aTuple

        DSIDTarget = mappingDict[int(DSID)]

        if not isinstance(histogram,ROOT.TH1): continue

        if DSIDTarget in mergedSamplesDICT.keys():  mergedSamplesDICT[DSIDTarget].Add(histogram)
        else:                                       mergedSamplesDICT[DSIDTarget]=histogram.Clone();

    return mergedSamplesDICT


def getHistIntegralWithUnertainty(hist, lowerLimit = 0, upperLimit = None ):

    #TH1::Integral returns the integral of bins in the bin range (default(1,Nbins).
    #If you want to include the Under/Overflow, use h.Integral(0,Nbins+1)
    
    if upperLimit is None: upperLimit = hist.GetNbinsX() +1
    integralUncertainty = ROOT.Double()

    integral = hist.IntegralAndError( lowerLimit , upperLimit, integralUncertainty)
    return integral, integralUncertainty


def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.15,0.70,0.55,0.95)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(2);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend


def printRootCanvasPDF(myRootCanvas, isLastCanvas, fileName, tableOfContents = None):
    if fileName is None:  fileName = myRootCanvas.GetTitle() + ".pdf"

    # it is not the last histogram in the TFile
    if not isLastCanvas: fileName += "("
    # close the pdf if it is the last histogram
    else:                fileName += ")"
    # see for alternatives to these brackets here: https://root.cern.ch/doc/master/classTPad.html#abae9540f673ff88149c238e8bb2a6da6


    if tableOfContents is None: myRootCanvas.Print(fileName)
    else: myRootCanvas.Print(fileName, "Title:" + tableOfContents)

    return None


def getBinContentsPlusError(myTH1):  
    return [ myTH1.GetBinContent(n)+myTH1.GetBinError(n) for n in range(1, myTH1.GetNbinsX() +1) ]






#To get the y value corresponding to bin k, h->GetBinContent(k);
#To get the bin number k corresponding to an x value, do
#  int k = h->GetXaxis()->FindBin(x);



def fillMasterHistDict2( currentTH1, systematicChannel, histEnding, mcTag, DSID, aDSIDHelper, masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):
    # split the histograms in inputFileDict by HistEnding, systematicChannel, and DSID 
    # and put them into a collections.defaultdict to indext them by HistEnding, systematicChannel, and DSID
    #
    # remember that python instantiates functions only once, 
    # so unless we provice a masterHistDict, we will aggregate results 
    # in the default one over multiple function calls
    #
    # masterHistDict[systematicChannel][ HistEnding ][ DSID ][ ROOT.TH1 ] 

    if int(DSID) != 0: # Signal & Background have DSID > 0
        scale = aDSIDHelper.getMCScale(DSID, mcTag)
        currentTH1.Scale(scale) # scale the histogram

    masterHistDict[systematicChannel][histEnding][DSID]=currentTH1.Clone()

    return masterHistDict


def findTypeInTList(TList, desiredType, doRecursive = True):
    # let's find all of the instances of <desiredType> in the TList 
    # do it recursively if possibly by checking of any element of the given TList can yield a TList itself
    # return a list of the found instances of <desiredType>

    instancesOfDesiredType = [] # save all the found instances of <desiredType> here

    for element in TList:
        if doRecursive:
            try: # let's try to see if the current element can produce a TList itself
                subTList = element.GetListOfPrimitives()
                instancesOfDesiredType.extend( findTypeInTList(subTList, desiredType) ) # 
            except:  pass # if it can't, do nothing
        if isinstance(element,desiredType):  instancesOfDesiredType.append(element)

    return instancesOfDesiredType



def printSubsetOfHists(histList, searchStrings=["M12","M34","M4l"], outputDir = "supportnoteFigs"):
    # we'll iterate over all of the lists in the histList, 
    # check each of the hists names against a list of searchStrings using regular expressions
    # and if the histogram name mates one of the search strings, we will print it to one of their own PDFs 
    # and a common .root file

    # let's make a search string for the regular expression
    # if we anna check if 'str1', 'str2' or 'str3' is in a given word we can do this with regular expressions
    # by executing re.search( "(str1)|(str2)|(str3)", "givenWord" )
    # here we build that search string
    searchString =  "(" +  ")|(".join(searchStrings) + ")" 

    if not os.path.exists(outputDir): os.makedirs(outputDir) 

    outoutROOTFile = ROOT.TFile(outputDir +"/figures.root","RECREATE")

    for currentCanvas in histList:

        reMatchObject = re.search(searchString, currentCanvas.GetName() ) # do the matching of the histogram name against any of the search strings

        if reMatchObject is not None: 

            # change the displayed title of the plot ( it is the title in the THStack )
            THStacklist = findTypeInTList(currentCanvas.GetListOfPrimitives() ,ROOT.THStack) 



            tempTitle = THStacklist[0].GetTitle()
            THStacklist[0].SetTitle(" ")
            
            
            printRootCanvasPDF(currentCanvas, True, "supportnoteFigs"+"/"+currentCanvas.GetName()+".pdf", tableOfContents = None)
            currentCanvas.Write() # write to the .ROOT file

            THStacklist[0].SetTitle(tempTitle)

    outoutROOTFile.Close()

    return None

def addRegionAndChannelToStatsText(shortName):

    outList = ""

    # fill in region
    if "ZXSR" in shortName:    outList += "Signal Region"
    elif "ZXCRC" in shortName: outList += "VR1"
    elif "ZXCRD" in shortName: outList += "VR2"
    else: outList += shortName

    outList += ", "

    if "4m"      in shortName:  outList += "4#mu"
    elif "2e2m"  in shortName:  outList += "2e2#mu"
    elif "2e2mu" in shortName:  outList += "2e2#mu"
    elif "2m2e"  in shortName:  outList += "2#mu2e"
    elif "2mu2e" in shortName:  outList += "2#mu2e"
    elif "4e"    in shortName:  outList += "4e"
    elif "2l2e"  in shortName:  outList += "llee"
    elif "2l2mu"in shortName:  outList += "ll#mu#mu"
    else:                       outList += "4#mu, 2e2#mu, 2#mu2e, 4e"

    return outList


def getDataDrivenReducibleShape(canvasName, sortedSampleKey, rebin):

    # this is super crude :(
    # but should work for now

    if "ZXSR_All_HWindow_m34" in canvasName  :
    #for key in sortedSamples.keys(): # add merged samples to the backgroundTHStack
        if "Reducible" in sortedSampleKey: 
            reducibleFile = ROOT.TFile("limitSetting/preppedHistsV2_mc16ade_1GeVBins_unblinded.root" , "OPEN")
            mergedHist = reducibleFile.Get("ZXSR").Get("reducibleDataDriven").Get("Nominal").Get("All").Get("h_m34_All")

            return copy.deepcopy(mergedHist) # return a deep copy to protec the hist from getting garbage collected after the TFile here goes out of scope


    if "ZXVR1_All_LowMassSidebands_m4l" in canvasName  : 
        if "Reducible" in sortedSampleKey: 
            reducibleFile = ROOT.TFile("limitSetting/dataDrivenBackgroundsFromH4l/dataDrivenReducible_ZZ_VR_m4l.root" , "OPEN")
            mergedHist = reducibleFile.Get("ZZVR_all_m4l")
            mergedHist.Rebin( rebin )

            return copy.deepcopy(mergedHist) # return a deep copy to protec the hist from getting garbage collected after the TFile here goes out of scope

    return False


def getDataDrivenReducibleShape2(canvasName, sortedSampleKey, referenceHist , meomizeDict = {} ):

    # this is super crude :(
    # but should work for now

    #makeReducibleShapes.getReducibleTH1s(TH1Template = None , convertXAxisFromMeVToGeV = False)

    # use the fact that the meomizeDict is only initialized once - at the launch of the programm  and not at function call 
    # to meomize the output getReducibleTH1s thus we only need to call getReducibleTH1s once 
    # and me might safe some time after when calling getDataDrivenReducibleShape2 repeatedly
    if len(meomizeDict) == 0:  
        reducibleShapeDict = makeReducibleShapes.getReducibleTH1s(TH1Template = referenceHist , convertXAxisFromMeVToGeV = True)
        for flavor in reducibleShapeDict: meomizeDict[flavor] = reducibleShapeDict[flavor]


    #if  "ZXSR_2mu2e_HWindow_m34" in canvasName: import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if re.search( "ZXSR_\w+_HWindow_m34", canvasName) :
    #for key in sortedSamples.keys(): # add merged samples to the backgroundTHStack
        if "Reducible" in sortedSampleKey: 


            inferredFlavor  = re.search("(All)|(2e2mu)|(4mu)|(4e)|(2mu2e)|(2l2e)|(2l2mu)", canvasName).group()

            #th1Dict = makeReducibleShapes.getReducibleTH1s(TH1Template = referenceHist , convertXAxisFromMeVToGeV = True)
            mergedHist = meomizeDict[inferredFlavor]
 
            mergedHist.Scale(   myDSIDHelper.lumiMap[args.mcCampaign] / myDSIDHelper.lumiMap["mc16ade"])
            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


            #reducibleFile = ROOT.TFile("limitSetting/preppedHistsV2_mc16ade_1GeVBins_unblinded.root" , "OPEN")
            #mergedHist = reducibleFile.Get("ZXSR").Get("reducibleDataDriven").Get("Nominal").Get("All").Get("h_m34_All")

            return copy.deepcopy(mergedHist) # return a deep copy to protec the hist from getting garbage collected after the TFile here goes out of scope


    #if "ZXVR1_All_LowMassSidebands_m4l" in canvasName  : 
    #    if "Reducible" in sortedSampleKey: 
    #        reducibleFile = ROOT.TFile("limitSetting/dataDrivenBackgroundsFromH4l/dataDrivenReducible_ZZ_VR_m4l.root" , "OPEN")
    #        mergedHist = reducibleFile.Get("ZZVR_all_m4l")
    #        mergedHist.Rebin( rebin )
    #
    #        return copy.deepcopy(mergedHist) # return a deep copy to protec the hist from getting garbage collected after the TFile here goes out of scope

    return False

def makelleeAndllmumuPlots(dictTree):


    for systematicChannel in dictTree.keys():

        for histEnding in dictTree[systematicChannel].keys():

            checkForMixedFlavor = re.search("(_2e2mu_)|(_2mu2e_)", histEnding )

            if not checkForMixedFlavor: continue

            referenceFlavor = checkForMixedFlavor.group()

            if referenceFlavor == "_2e2mu_" : 
                complimentingHistEnding = re.sub("_2e2mu_", "_4mu_", histEnding) 

                combdinedFlavor = "_2l2mu_"
                combinedHistEnding = re.sub("_2e2mu_", "_2l2mu_", histEnding) 
            else:                                  
                complimentingHistEnding = re.sub("_2mu2e_", "_4e_", histEnding) 
                combdinedFlavor = "_2l2e_"
                combinedHistEnding = re.sub("_2mu2e_", "_2l2e_", histEnding) 

            for DSID in dictTree[systematicChannel][histEnding].keys():

                histA = dictTree[systematicChannel][histEnding][DSID]
                histB = dictTree[systematicChannel][complimentingHistEnding][DSID]

                newName = re.sub("_2e2mu_", combdinedFlavor, histEnding) 

                combinedHist = histA.Clone(newName)
                combinedHist.Add(histB)

                dictTree[systematicChannel][combinedHistEnding][DSID] = combinedHist

                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


def addStatUncertVariationHists(BackgroundVariationDict, flavor = "All", nominalHist = None):

    if nominalHist is None: nominalHist =  BackgroundVariationDict["Nominal"][flavor]

    variationNameTuples = [("STAT_UNCERT_1up" , +1.), ("STAT_UNCERT_1down" , -1.)]

    for variationName , signFactor in variationNameTuples:

        BackgroundVariationDict[variationName][flavor] = nominalHist.Clone( re.sub( "Nominal", variationName, nominalHist.GetName()) )

        for binNr in xrange(1,nominalHist.GetNbinsX()+1):  
            BackgroundVariationDict[variationName][flavor].SetBinContent(binNr, nominalHist.GetBinContent(binNr) + signFactor*nominalHist.GetBinError(binNr) )

    return None


def make1UpAnd1DownSystVariationHistogram( BackgroundVariationDict , flavor = "All" , nominalBackgroundHist = None):
    #make1UpAnd1DownSystVariationHistogram( altMasterHistDict["ZXSR"]["Background"] )

    def makeVariationHist( upOrDown = "1up" , inlcudeStatUncertainty = False, nominalBackgroundHist = None):

        sysVarHists = [BackgroundVariationDict[sysName+upOrDown][flavor] for sysName in systematicNames]
        sysYieldMatrix =  histNumpyTools.listOfTH1ToNumpyMatrix(sysVarHists)  # numpy matrix, entries are event counts, axis = 0 indexes the systeamatic variations, axis = 1 indexes the bins

        nominalHist = BackgroundVariationDict["Nominal"][flavor]
        nominalVector= histNumpyTools.histToNPArray(nominalHist) # 1-d numpy matrix that contains the nominal bin counts
        nominalMatrix = np.tile(nominalVector, (sysYieldMatrix.shape[0],1) ) # 2-d numpy matrix, axis = 1 indexes the bins, same shape as the sysYieldMatrix


        relativeYieldDifference = (sysYieldMatrix - nominalMatrix)/nominalMatrix
        relativeYieldDifference = np.nan_to_num(relativeYieldDifference) # replace the NaN with zeros

        relativeYieldDifference = relativeYieldDifference * ( abs(relativeYieldDifference) <2 )

        relativeYieldUncertainty = np.sqrt( np.sum( np.square( relativeYieldDifference) , axis=0) ) # add the same bin over different systematics in quadrature

        if inlcudeStatUncertainty:
            relStatError = histNumpyTools.histErrorToNPArray(nominalHist)/nominalVector
            relStatError = np.nan_to_num(relStatError)

            relativeYieldUncertainty = np.sqrt(relativeYieldUncertainty**2 + relStatError**2)

        if upOrDown == "1up": yieldVariation = (+relativeYieldUncertainty) *nominalVector
        else:                 yieldVariation = (-relativeYieldUncertainty) *nominalVector

        if nominalBackgroundHist is None: nominalBackgroundHist = BackgroundVariationDict["Nominal"][flavor]

        sysHist = nominalBackgroundHist.Clone( nominalBackgroundHist.GetName() + "_systVar_"+upOrDown)
        #sysHist.Reset()

        for binNr in xrange(0, len(yieldVariation)):
            oldBinContent = sysHist.GetBinContent(binNr+1 )
            sysHist.SetBinContent( binNr+1 , oldBinContent  +  yieldVariation[binNr] )
            sysHist.SetBinError(binNr+1 , 0)

        return sysHist

    
    #for sysVariation in BackgroundVariationDict :     systematicNameSet.add( re.sub('(1down)|(1up)', '', sysVariation) )
    systematicNameList = [ re.sub('(1down)|(1up)', '', sysVariation) for sysVariation in BackgroundVariationDict if not sysVariation.startswith("PMG_") ] 

    systematicNameSet = set(systematicNameList)
    systematicNameSet.discard("Nominal") # remove the Nominal variation from list

    removeList = [x for x in systematicNameSet if re.search("(UncorrUncertaintyNP)|(CorrUncertaintyNP)", x) ]

    for x in removeList: systematicNameSet.discard(x)
    systematicNames = sorted(list(systematicNameSet))

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    upSysHist   = makeVariationHist( upOrDown = "1up"   , inlcudeStatUncertainty = False , nominalBackgroundHist = nominalBackgroundHist  )
    downSysHist = makeVariationHist( upOrDown = "1down" , inlcudeStatUncertainty = False , nominalBackgroundHist = nominalBackgroundHist  )

    return upSysHist, downSysHist

def make1UpAnd1DownSystVariationYields( BackgroundVariationDict , flavor = "All" , nominalHist = None):

    def makeVariationYield( upOrDown = "1up" , nominalHist = None):
        signFactorDict = {"1up" : +1. , "1down" : -1.}
        signFactor = signFactorDict[upOrDown]

        if nominalHist is None: nominalHist = BackgroundVariationDict["Nominal"][flavor]

        sysVarYieldList = np.array([BackgroundVariationDict[sysName+upOrDown][flavor].Integral() for sysName in systematicNames if "STAT_UNCERT" not in sysName])
        # tread stat error differently, as they are uncorrelated between bins
        nominalYield , statError = getHistIntegralWithUnertainty(nominalHist) 
        np.append(sysVarYieldList , signFactor*statError+nominalYield )

        relativeYieldDifference = (sysVarYieldList - nominalYield)/nominalYield
        relativeYieldDifference = np.nan_to_num(relativeYieldDifference) # replace the NaN with zeros

        relativeYieldUncertainty = np.sqrt( np.sum( np.square( relativeYieldDifference) , axis=0) ) # add the same bin over different systematics in quadrature

        yieldVariation = (signFactor*relativeYieldUncertainty) *nominalYield

        return yieldVariation

    #for sysVariation in BackgroundVariationDict :     systematicNameSet.add( re.sub('(1down)|(1up)', '', sysVariation) )
    systematicNameList = [ re.sub('(1down)|(1up)', '', sysVariation) for sysVariation in BackgroundVariationDict if not sysVariation.startswith("PMG_") ] 

    systematicNameSet = set(systematicNameList)
    systematicNameSet.discard("Nominal") # remove the Nominal variation from list

    removeList = [x for x in systematicNameSet if re.search("(UncorrUncertaintyNP)|(CorrUncertaintyNP)", x) ]

    for x in removeList: systematicNameSet.discard(x)

    systematicNames = sorted(list(systematicNameSet))

    upSysYieldChange   = makeVariationYield( upOrDown = "1up"   , nominalHist = nominalHist)
    downSysYieldChange = makeVariationYield( upOrDown = "1down" , nominalHist = nominalHist)

    return upSysYieldChange, downSysYieldChange

def preselectTDirsForProcessing(postProcessedData , permittedDSIDs = None, systematicsTags = None, systematicsVetoes = None , newOwnership = None):

    if permittedDSIDs is None:
        reSearchString = ""
    else:
        reSearchOptions = [ "(/%i)" %DSID for DSID in permittedDSIDs]

        reSearchStringDSID = "|".join(reSearchOptions)

    # preselect by systematic
    if systematicsTags is None:                    reSearchStringSystematics = ""
    elif isinstance(systematicsTags, list):        reSearchStringSystematics = "|".join(systematicsTags)
    else:                                          reSearchStringSystematics = systematicsTags

    if systematicsVetoes is None:                    reSearchStringSysVeto = False
    elif isinstance(systematicsVetoes, list):        reSearchStringSysVeto = "|".join(systematicsVetoes)
    else:                                            reSearchStringSysVeto = systematicsVetoes


    for path_DSIDLevel, baseHist_DSIDLevel  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive( postProcessedData , newOwnership = newOwnership, maxRecursionDepth = 0) :        

        if not isinstance(baseHist_DSIDLevel,ROOT.TDirectoryFile): continue
        DSID = path_DSIDLevel.split("/")[-1]
        if not re.search( reSearchStringDSID, path_DSIDLevel): continue

        preselectedTDirs = []
        for path_sysLevel, baseHist_sysLevel  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive( baseHist_DSIDLevel , baseString = path_DSIDLevel, newOwnership = newOwnership, maxRecursionDepth = 0) :

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            systematic = path_sysLevel.split("/")[-1]
            if reSearchStringSysVeto and re.search( reSearchStringSysVeto, systematic): continue
            if not re.search( reSearchStringSystematics, systematic): continue

            for path, baseHist in rootDictAndTDirTools.generateTDirPathAndContentsRecursive( baseHist_sysLevel , baseString = path_sysLevel, newOwnership = newOwnership):
                yield path, baseHist

def makeSignificancePlots(referenceHist, dataHist, backgroundHist):


    # complimentary cumulative distribution function 
    # ROOT.Math.poisson_cdf_c( n, b ) gives the cumulative poisson distribution from n+1 to infinity. So that is equivalent to the probability of getting a value more extreme than n
    # We want the probability of getting n or more, so we need to add in the valye for b
    def makeP0Value(nObserved,nExpected):   return ROOT.Math.poisson_cdf_c( int(nObserved) , nExpected) + ROOT.Math.poisson_pdf( int(nObserved) , nExpected)# complimentary cumulative distribution function 
    # ROOT.Math.poisson_pdf( int(0) , 5)
    def getGaussSignificance(p0Value):      return ROOT.Math.normal_quantile(1-p0Value,1) # ROOT.Math.normal_quantile( Z , sigma)

    # ROOT.Math.poisson_cdf_c( x , expectation value)   

    dataArray          = histNumpyTools.histToNPArray(dataHist)
    expectedYieldArray = histNumpyTools.histToNPArray(backgroundHist)

    significanceListForHist = []
    significanceListForPlotLimits = []

    #for index in xrange(0,len(dataArray)):  int(dataArray[index]), expectedYieldArray[index], makeP0Value(  int(dataArray[index]), expectedYieldArray[index] ), getGaussSignificance( makeP0Value(  int(dataArray[index]), expectedYieldArray[index] ) )
    for index in xrange(0,len(dataArray)):  
        if dataArray[index] == 0 :  signifiance = -10 # I don't know how to exclde plotting 0-bin content bins outside of the "bar" option, but this might work
        else:
            signifiance = getGaussSignificance( makeP0Value(  int(dataArray[index]), expectedYieldArray[index] ) ) 
            significanceListForPlotLimits.append(signifiance)

        if np.isinf(signifiance ) : signifiance = -10
        significanceListForHist.append( signifiance )

    significanceHist = referenceHist.Clone( referenceHist.GetName() + "_signifiance" )
    significanceHist.Reset()

    histNumpyTools.fillHistWithNPArray( significanceHist, significanceListForHist)

    significanceHist.SetMarkerColor(ROOT.kRed )
    significanceHist.SetMarkerStyle( 3 ) # https://root.cern.ch/doc/master/classTAttMarker.html#M2

    #significanceHist.SetMarkerStyle( 105 ) # https://root.cern.ch/doc/master/classTAttMarker.html#M2

    significanceHist.GetYaxis().SetRangeUser(min(significanceListForPlotLimits)*1.1, max(significanceListForPlotLimits)*1.1)
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return significanceHist, min(significanceListForPlotLimits)*1.1, max(significanceListForPlotLimits)*1.1

if __name__ == '__main__':

    from functions.compareVersions import compareVersions # to compare root versions
    import functions.histHelper as histHelper # to help me with histograms
    import limitSetting.limitFunctions.makeHistDict as makeHistDict # alternative option to fill the  masterHistDict
    import limitSetting.limitFunctions.reportMemUsage as reportMemUsage


    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("-c", "--mcCampaign", type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], default="mc16ade",
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="metadata/md_bkg_datasets_mc16e_All.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument( "--DSID_Binning", type=str, help = "set how the different DSIDS are combined, ",
        choices=["physicsProcess","physicsSubProcess","DSID","analysisMapping"] , default="physicsProcess" )

    parser.add_argument( "--holdAtPlot", default=False , action='store_true',
        help = "Debugging option. If True sets a debugger tracer and \
        activates the debugger at the point where the plot has has been fully assembled." ) 

    parser.add_argument( "--outputName", type=str, default=None , 
        help = "Pick the name of the output files. \
        We'll produce three of them: a root file output (.root), pdfs of the histograms (.pdf) and a .txt indexing the histogram names.\
        If no outputName is choosen, we will default to <inputFileName>_<mcCampaign>_outHistograms." ) 

    parser.add_argument( "--rebin", type=int, default=1 , 
    help = "We can rebin the bins. Choose rebin > 1 to rebin #<rebin> bins into 1." ) 

    parser.add_argument( "--batch", default=False, action='store_true' , 
    help = "If run with '--batch' we will activate root batch mode and suppress all creation of graphics." ) 

    parser.add_argument( "--skipRatioHist", default=False, action='store_true' , 
    help = "If run with '--skipRatioHist' we will skip drawing of the ratio hist." ) 

    parser.add_argument( "--makeSystematicsPlots", default=False, action='store_true' , 
    help = "If run with '--makeSystematicsPlots' we will not only plot the 'Nominal' distributions, but also teh systematics variations too." ) 

    parser.add_argument( "--kinematicsToPlot", nargs='*', default=[], 
    help = "If we only want to list a subset of the kninematic variables, list them here.\
            Use like --kinematicsToPlot m4l m34. If none are specified, or argument is not used, we plot all kinematic variables" ) 

    parser.add_argument( "--flavorsToPlot", nargs='*', default=["2e2mu", "2mu2e", "4e", "4mu", "All"], 
    help = "If we only want to list a subset of the kninematic variables, list them here.\
            Use like --kinematicsToPlot m4l m34. If none are specified, or argument is not used, we plot all kinematic variables" ) 

    parser.add_argument( "--skipReducible", default=False, action='store_true' , 
    help = "If run with '--skipReducible' we will not include any 'reducible' MC in the plots " ) 

    parser.add_argument( "--cacheForDockerOnWSL", default=False, action='store_true' , 
    help = "Use when opening larger files, while operating in a docker container, on a Windows machine" ) 

    parser.add_argument( "--h4lScale", type=float, default= 1. , 
    help = "Scale the cross section of the h4l background by this factor. Usefull for setting the H4l background to a postfit value" ) 


    startTime = time.time() 

    args = parser.parse_args()

    skipZX = True
    skipZdZd = True
    skipZjets = False
    skipReducible = args.skipReducible

    if skipReducible: skipZjets = True

    replaceWithDataDriven = True

    addSystematicUncertaintyToNominal = args.makeSystematicsPlots and (len(args.kinematicsToPlot)==1)

    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    # check root version
    currentROOTVersion = ROOT.gROOT.GetVersion()

    if compareVersions( currentROOTVersion, "6.04/16") > 0:
        warnings.warn("Running on ROOT version > 6.04/16. Current version is  "
                       + currentROOTVersion + ". Adjusting ROOT object ownership, which might affect memory consumption.")
        # the underlying issue for the extra memory consumption is the root memory managment. 
        # For the version 6.04/16 our method of given root ownership of the parsed opjects to delete them works and memory utilization is lower
        # for the newer versions this way of affecting the ownership results in a crash. So we don't deal with it and accept higher memory utilization
        ownershipSetpoint = None
    else: ownershipSetpoint = True


    if args.batch : ROOT.gROOT.SetBatch(True)

    activateATLASPlotStyle()

    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = DSIDHelper()
    myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati

    # scale H4l cross sections to value set in command line. Default is 1. and leaves the cross sections unchanged
    for DSID in myDSIDHelper.analysisMapping["H4l"]: myDSIDHelper.metaDataDict[DSID]["crossSection"] *= args.h4lScale

    # assemble the input files, mc-campaign tags and metadata file locations into dict
    # well structered dict is sorted by mc-campign tag and has 

    #######################
    # Test generator access to ROOT TH1s 

    #postProcessedData = inputFileDict.values()[0]["TFile"]

    mainBackgrounds = []

    mainBackgrounds.extend( myDSIDHelper.analysisMapping["H4l"])
    mainBackgrounds.extend( myDSIDHelper.analysisMapping["ZZ"])

    if args.cacheForDockerOnWSL : postProcessedData = TFileCache(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing
    else:                         postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)

    altMasterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) # alternative master hist dict, store here all backgrounds in one histogram, for calculations of systematic uncertainties

    histCounter = 0 # count how many relevant hists we have
    nonRelevantHistCounter = 0


    DSIDsToConsider = []
    DSIDsToConsider.append( 0) # data!
    DSIDsToConsider.extend( myDSIDHelper.analysisMapping["H4l"])
    DSIDsToConsider.extend( myDSIDHelper.analysisMapping["ZZ"])
    DSIDsToConsider.extend( myDSIDHelper.analysisMapping["VVV_Z+ll"])
    if not skipReducible: DSIDsToConsider.extend( myDSIDHelper.analysisMapping["Reducible"])
    if skipZjets: # we remove the Z+Jet DSIDs after the fact, due to the way the analysisMappings are defined
        for ZJetDISD in  myDSIDHelper.ZJetDSIDs:
            if ZJetDISD in DSIDsToConsider:   DSIDsToConsider.remove(ZJetDISD)

    # ZZd samples                   m_Zd    15 GeV  20 GeV  25 GeV  30 GeV  35 GeV  40 GeV  45 GeV  50 GeV  55 GeV  
    #                                       343234, 343235, 343236, 343237, 343238, 343239, 343240, 343241, 343242
    if not skipZX : DSIDsToConsider.extend([343234, 343235, 343236, 343237, 343238, 343239, 343240, 343241, 343242])



    if args.makeSystematicsPlots  : systematicsTags = "" # this way we tag all the systematics
    else:                           systematicsTags =  "Nominal"


    # loop over all of the TObjects in the given ROOT file                         # newOwnership set to none for newer root versions, set to true for older ones
    #for path, baseHist  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = ownershipSetpoint): 
    for path, baseHist in preselectTDirsForProcessing(postProcessedData, permittedDSIDs = DSIDsToConsider, systematicsTags = systematicsTags, systematicsVetoes = ["UncorrUncertaintyNP" ,"CorrUncertaintyNP" ,"PMG_"], newOwnership = ownershipSetpoint):

        nonRelevantHistCounter += 1
        if nonRelevantHistCounter %1e5 == 0: print "%i irrelevant hists processed. \t Memory usage: %s (MB)" % (nonRelevantHistCounter, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000)


        if irrelevantTObject(path, baseHist): continue # skip non-relevant histograms

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        # discern DSID and plotTitle to use them when sorting into a tree structure
        DSID = myDSIDHelper.idDSID(path)

        plotTitle = idPlotTitle(path, myDSIDHelper, DSID=DSID)

        systematicChannel = path.split("/")[-2]

        # make cuts on kinematic variables
        if len(args.kinematicsToPlot) >0 :
            if not any([kinematic in path for kinematic in args.kinematicsToPlot]): continue

        # make cuts on flavors
        if len(args.flavorsToPlot) >0 :
            if not any([ "_"+flavor+"_" in path for flavor in args.flavorsToPlot]): continue

        #if not "ZXSR" in path: continue

        ROOT.SetOwnership(baseHist, False)  # if we pass irrelevantTObject the histogram is relevant, so we change the ownership here to False in the attempt to prevent deletion

        # build my tree structure here to house the relevant histograms, pre-sorted for plotting

        baseHist.Rebin(args.rebin)
        
        if "ZXVR2" in path:  baseHist = varibleSizeRebinHelper(baseHist, [(76,84)])

        if addSystematicUncertaintyToNominal and not  int(DSID) in myDSIDHelper.analysisMapping["Reducible"] :
            altMasterHistDict = makeHistDict.fillHistDict(path, baseHist , args.mcCampaign, myDSIDHelper, channelMap = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZXVR1" , "ZXVR2" : "ZXVR2", "ZXVR1a":"ZXVR1a" } , masterHistDict = altMasterHistDict, customMapping = myDSIDHelper.BackgroundAndSignalByDSID) 

        # store the histograms for binning and and plotting in the master HistDict
        masterHistDict = fillMasterHistDict2( baseHist, systematicChannel, plotTitle, args.mcCampaign, DSID, myDSIDHelper )
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        # output a running counter of processed hists and used memory
        histCounter += 1
        if histCounter %1000 == 0: print str(histCounter) + " relevant hists processed. \t Memory usage: %s (MB)" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000)


    reportMemUsage.reportMemUsage(startTime)

    ######################################################
    # Do the data processing from here on
    ######################################################

    if args.flavorsToPlot == parser.get_default("flavorsToPlot"): 
        makelleeAndllmumuPlots(masterHistDict)
        makeHistDict.add2l2eAnd2l2muHists(altMasterHistDict)

    combinedMCTagHistDict = masterHistDict

    canvasList = []

    for systematicChannel in combinedMCTagHistDict.keys():
        if re.search("(UncorrUncertaintyNP)|(CorrUncertaintyNP)|(PMG_)", systematicChannel): continue # skip generator weight variations when plottins systematics

        if "Nominal" != systematicChannel: continue

        for histEnding in combinedMCTagHistDict[systematicChannel].keys():

            backgroundSamples = [] # store the background samples as list of tuples [ (DSID, TH1) , ...] 
            canvasName = systematicChannel +"_"+ histEnding
            backgroundTHStack = ROOT.THStack(histEnding,histEnding)
            #backgroundTHStack.SetMaximum(25.)

            gotDataSample = False # change this to true later if we do have data samples

            for DSID in combinedMCTagHistDict["Nominal"][histEnding].keys():

                    if int(DSID) > 0: # Signal & Background have DSID > 0
                        currentTH1 = combinedMCTagHistDict[systematicChannel][histEnding][DSID]
                        backgroundSamples.append( ( int(DSID), currentTH1) )
                    else:   # data has DSID 0 for us  \

                        #continue

                        currentTH1 = copy.deepcopy(combinedMCTagHistDict["Nominal"][histEnding][DSID]) # do deppcopy here in case we rebin, otherwise we would rebin multiple times


                        gotDataSample = True
                        dataTH1 = currentTH1

#    ######### process the cutflow histograms #########


            if   args.DSID_Binning == "physicsProcess" :    DSIDMappingDict = myDSIDHelper.physicsProcessByDSID
            elif args.DSID_Binning == "physicsSubProcess" : DSIDMappingDict = myDSIDHelper.physicsSubProcessByDSID
            elif args.DSID_Binning == "analysisMapping" : DSIDMappingDict = myDSIDHelper.analysisMappingByDSID
            elif args.DSID_Binning == "DSID" : # if we choose to do the DSID_Binning by DSID, we build here a a mapping DSID -> str(DSID)
                DSIDMappingDict = {}
                for aTuple in backgroundSamples: DSIDMappingDict[aTuple[0]] = str( aTuple[0] )  #DSID, histogram = aTuple

            #print(backgroundSamples)
            #import pdb; pdb.set_trace() # import the debugger and instruct
            sortedSamples = mergeHistsByMapping(backgroundSamples, DSIDMappingDict)

            myDSIDHelper.colorizeHistsInDict(sortedSamples) # change the fill colors of the hists in a nice way
            statsTexts = []

            statsTexts.append( "#font[72]{ATLAS} internal")
            statsTexts.append( "#sqrt{s} = 13 TeV, %.1f fb^{-1}" %( myDSIDHelper.lumiMap[args.mcCampaign] ) ) 

            regionAndChannelString = addRegionAndChannelToStatsText( canvasName )
            if systematicChannel != "Nominal" : regionAndChannelString = systematicChannel +" "+ regionAndChannelString
            statsTexts.append( regionAndChannelString ) 

            statsTexts.append( "  " ) 

            # use these to report the total number of background and signal samples each later on
            backgroundTallyTH1 = sortedSamples.values()[0].Clone( "backgroundTally")
            backgroundTallyTH1.Scale(0)
            signalTallyTH1 = backgroundTallyTH1.Clone("signalTally")

            legend = setupTLegend()

            for key in myDSIDHelper.defineSequenceOfSortedSamples( sortedSamples  ): # add merged samples to the backgroundTHStack 


                if replaceWithDataDriven: # insert data driven reducible hist if so desided
                    #dataDrivenReducibleHist = getDataDrivenReducibleShape(canvas.GetName(), key, args.rebin)
                    dataDrivenReducibleHist = getDataDrivenReducibleShape2(canvasName, key, sortedSamples[key] )

                    if dataDrivenReducibleHist: # false if we didn't find a match
                        dataDrivenReducibleHist.SetFillStyle( 1001 )  
                        dataDrivenReducibleHist.SetFillColor( myDSIDHelper.colorMap[key] )
                        sortedSamples[key] = dataDrivenReducibleHist
                        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

                mergedHist = sortedSamples[key]

                

                keyProperArrow = re.sub('->', '#rightarrow ', key) # make sure the legend displays the proper kind of arrow
                legend.AddEntry(mergedHist , keyProperArrow , "f");
                #statsTexts.append( keyProperArrow + ": %.1f #pm %.1f" %( getHistIntegralWithUnertainty(mergedHist)) )
                statsTexts.append( keyProperArrow + ": %.1f" %( mergedHist.Integral() ) )

                if myDSIDHelper.isSignalSample( key ): signalTallyTH1.Add(sortedSamples[key])
                else:
                    backgroundTHStack.Add( mergedHist )                                  
                    backgroundTallyTH1.Add(sortedSamples[key])

            backgroundClones = []
            signalTHStacks = []
            for key in myDSIDHelper.defineSequenceOfSortedSamples( sortedSamples  ): # add merged samples to the backgroundTHStack 
                if myDSIDHelper.isSignalSample( key ): 
                    signalHist = sortedSamples[key]

                    signalTHStack = ROOT.THStack(key,key)
                    backgroundForSignalStack = backgroundTallyTH1.Clone( key +"_signalBackground" )
                    backgroundForSignalStack.SetFillStyle(0)
                    backgroundClones.append(backgroundForSignalStack)

                    signalTHStack.Add(backgroundForSignalStack)
                    signalTHStack.Add(signalHist)

                    signalTHStacks.append(signalTHStack)

            #import pdb; pdb.set_trace() # import the debugger and instruct


            
            canvas = ROOT.TCanvas(canvasName,canvasName,1300/2,1300/2);
            ROOT.SetOwnership(canvas, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042


            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            # create a pad for the CrystalBall fit + data
            if gotDataSample and not args.skipRatioHist: histPadYStart = 3.5/13
            else:  histPadYStart = 0
            histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
            ROOT.SetOwnership(histPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
            if gotDataSample and not args.skipRatioHist: histPad.SetBottomMargin(0.06); # Seperation between upper and lower plots
            else: histPad.SetBottomMargin(0.12)
            #histPad.SetGridx();          # Vertical grid
            histPad.Draw();              # Draw the upper pad: pad1
            histPad.cd();                # pad1 becomes the current pad

            backgroundTHStack.SetTitle("")

            backgroundTHStack.Draw("Hist")
            drawPrefix = "SAME " # after we draw out first histogram(stack) we need to add 'same' to the draw command 
            for signalStack in signalTHStacks:
                signalStack.Draw(drawPrefix + "HIST")
                drawPrefix = "SAME "


            backgroundTHStack.Draw(drawPrefix+"Hist")


            backgroundMergedTH1 = histHelper.mergeTHStackHists(backgroundTHStack) # get a merged background to draw uncertainty bars on the total backgroun

            backgroundSystAddendum = ""
            backgroundYieldText = "Background: %.1f #pm %.1f" %( getHistIntegralWithUnertainty(backgroundMergedTH1))

            backgroundMergedTH1ForRatioHist = backgroundMergedTH1.Clone( backgroundMergedTH1.GetName() + "_ratioHist")

            ################# add in systematic uncertainties #################
            if addSystematicUncertaintyToNominal  and systematicChannel == "Nominal" and "ZXVR1a" not in histEnding : # and "ZXSR" in histEnding

                inferredRegion = re.search( "(ZXSR)|(ZXVR1)|(ZXVR2)", histEnding).group()

                print(inferredRegion)

                inferredFlavor  = re.search("(All)|(2e2mu)|(4mu)|(4e)|(2mu2e)|(2l2e)|(2l2mu)", histEnding).group()

                addStatUncertVariationHists(altMasterHistDict[inferredRegion]["Background"], flavor = inferredFlavor , nominalHist = backgroundTallyTH1)

                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
                upSysHist, downSysHist = make1UpAnd1DownSystVariationHistogram( altMasterHistDict[inferredRegion]["Background"]  , flavor =  inferredFlavor , nominalBackgroundHist = backgroundMergedTH1ForRatioHist.Clone())
                upSysYield, downSysYield = make1UpAnd1DownSystVariationYields(  altMasterHistDict[inferredRegion]["Background"]  , flavor = inferredFlavor, nominalHist = None)
                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

                for sysHist in [upSysHist, downSysHist]: 
                    sysHist.SetLineColor(ROOT.kGray+2 )
                    sysHist.SetLineStyle(ROOT.kDashed )
                    sysHist.SetFillStyle(0)#(3001) # fill style: https://root.cern.ch/doc/v614/classTAttFill.html#F2

                    #sysHist.SetLineWidth( 2 )

                #upSysHist.Draw("same")
                #downSysHist.Draw("same")

                #legend.AddEntry(upSysHist, "MC sys unc.", "l")

                nominalYield = backgroundMergedTH1.Integral()



                backgroundSystAddendum += "_{stat} #pm %.1f_{sys}" %(   (upSysYield - downSysYield)/2)

                backgroundYieldText = "Background: %.1f #pm %.1f" %( nominalYield, (upSysYield - downSysYield)/2)

                # include the systematic error in the backgroundMergedTH1, so that it is reflected in the ratio hist
                for binNr in xrange(1,backgroundMergedTH1ForRatioHist.GetNbinsX()+1): 
                    newBinError = upSysHist.GetBinContent(binNr) - backgroundMergedTH1ForRatioHist.GetBinContent(binNr)
                    backgroundMergedTH1ForRatioHist.SetBinError(binNr, newBinError )
                    backgroundMergedTH1.SetBinError(binNr,  (upSysHist.GetBinContent(binNr)- downSysHist.GetBinContent(binNr))/2 )
            ################# add in systematic uncertainties #################

            


            backgroundMergedTH1.Draw("same E2 ")   # "E2" Draw error bars with rectangles:  https://root.cern.ch/doc/v608/classTHistPainter.html
            backgroundMergedTH1.SetMarkerStyle(0 ) # SetMarkerStyle(0 ) remove marker from combined backgroun
            backgroundMergedTH1.SetFillStyle(3244)#(3001) # fill style: https://root.cern.ch/doc/v614/classTAttFill.html#F2
            backgroundMergedTH1.SetFillColor(1)    # black: https://root.cern.ch/doc/v614/classTAttFill.html#F2
            #if "m34" in  backgroundTHStack.GetName() :  backgroundTHStack.GetXaxis().SetRangeUser(10, 70)

            legend.AddEntry(backgroundMergedTH1 , "Uncertainty" , "f");

            #if "eta"   in backgroundMergedTH1.getTitle: yAxisUnit = ""
            #elif "phi" in backgroundMergedTH1.getTitle: yAxisUnit = " radians"

            backgroundTHStack.GetYaxis().SetTitle("Events / " + str(backgroundMergedTH1.GetBinWidth(1) )+" GeV" )
            backgroundTHStack.GetYaxis().SetTitleSize(0.05)
            backgroundTHStack.GetYaxis().SetTitleOffset(1.1)
            backgroundTHStack.GetYaxis().CenterTitle()
            
            #backgroundTHStack.GetXaxis().SetTitleSize(0.12)
            backgroundTHStack.GetXaxis().SetTitleOffset(1.1)
            
                
            statsTexts.append( "  " )       
            statsTexts.append( backgroundYieldText )
            #statsTexts.append( "Background : %.1f #pm %.1f" %( getHistIntegralWithUnertainty(backgroundTallyTH1)) + backgroundSystAddendum )
            if signalTallyTH1.Integral() >0 : statsTexts.append( "Signal: %.1f #pm %.1f" %( getHistIntegralWithUnertainty(signalTallyTH1)) )


            # use the x-axis label from the original plot in the THStack, needs to be called after 'Draw()'
            #backgroundTHStack.GetXaxis().SetTitle( mergedHist.GetXaxis().GetTitle() )

            if gotDataSample: # add data samples
                dataTH1.Draw("same")
                #if "m34" in  backgroundTHStack.GetName() :  dataTH1.GetXaxis().SetRangeUser(10, 70)
                #if max(getBinContentsPlusError(dataTH1)) > backgroundTHStack.GetMaximum(): backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)) +1 ) # rescale Y axis limit
                #backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)*1.3) )

                legend.AddEntry(currentTH1, "data", "l")

                if dataTH1.Integral >0: statsTexts.append("Data: %.1f #pm %.1f" %( getHistIntegralWithUnertainty(dataTH1) ) )  

            # rescale Y-axis
            largestYValue = [max(getBinContentsPlusError(backgroundMergedTH1ForRatioHist) )]
            if gotDataSample:  largestYValue.append( max( getBinContentsPlusError(dataTH1) ) )
            backgroundTHStack.SetMaximum( max(largestYValue) * 1.3 )

            #rescale X-axis
            axRangeLow, axRangeHigh = histHelper.getFirstAndLastNonEmptyBinInHist(backgroundTHStack, offset = 1)
            backgroundTHStack.GetXaxis().SetRange(axRangeLow,axRangeHigh)

            #statsOffset = (0.6,0.55), statsWidths = (0.3,0.32)
            statsTPave=ROOT.TPaveText(0.4,0.40,0.9,0.87,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
            for stats in statsTexts:   statsTPave.AddText(stats);
            statsTPave.Draw();
            legend.Draw(); # do legend things
            
            ROOT.gPad.RedrawAxis("G") # to make sure that the Axis ticks are above the histograms
            ROOT.gPad.RedrawAxis()

            canvas.cd()





            if gotDataSample and not args.skipRatioHist: # fill the ratio pad with the ratio of the data bins to  mc bckground bins

                # define a TPad where we can add a histogram of the ratio of the data and MC bins
                ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);
                ROOT.SetOwnership(ratioPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
                ratioPad.SetTopMargin(0.)
                ratioPad.SetBottomMargin(0.3)
                ratioPad.SetGridy(); #ratioPad.SetGridx(); 
                ratioPad.Draw();              # Draw the upper pad: pad1
                ratioPad.cd();                # pad1 becomes the current pad

                ratioHist = dataTH1.Clone( dataTH1.GetName()+"_Clone" )
                ratioHist.Divide(backgroundMergedTH1ForRatioHist)
                ratioHist.GetXaxis().SetRange(axRangeLow, axRangeHigh)
                ratioHist.SetStats( False) # remove stats box
                
                ratioHist.SetTitle("")
                
                ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
                ratioHist.GetYaxis().SetLabelSize(0.1)

                ratioHist.GetYaxis().SetTitle("Data / MC")
                ratioHist.GetYaxis().SetTitleSize(0.11)
                ratioHist.GetYaxis().SetTitleOffset(0.4)
                ratioHist.GetYaxis().CenterTitle()

                # ratioHist.GetMaximum() , ratioHist.GetMinimum()
                if ratioHist.GetMaximum() > 5: ratioHist.GetYaxis().SetRangeUser(ratioHist.GetMinimum(), 5)
                maxRatioVal , _ = histHelper.getMaxBin(ratioHist , useError = True, skipZeroBins = True)
                minRatioVal , _ = histHelper.getMinBin(ratioHist , useError = True, skipZeroBins = True)

                #if minRatioVal is None: import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

                if maxRatioVal > 5.5: maxRatioVal = 5

                if maxRatioVal is not None and minRatioVal is not None:
                    ratioHist.GetYaxis().SetRangeUser(minRatioVal * 0.9, maxRatioVal * 1.1)



                ratioHist.GetXaxis().SetLabelSize(0.12)
                ratioHist.GetXaxis().SetTitleSize(0.13)
                ratioHist.GetXaxis().SetTitleOffset(1.0)
                

                ratioHist.Draw()

                if "ZXSR" in backgroundTHStack.GetName(): #== "ZXSR_All_HWindow_m34": 
                    significanceHist, minSignifiance, maxSignificance = makeSignificancePlots(ratioHist, dataTH1, backgroundMergedTH1ForRatioHist)

                    newLowerAxisLimit = min(ratioHist.GetMinimum(), minSignifiance)
                    newUpperAxisLimit = max(ratioHist.GetMaximum(), maxSignificance)

                    ratioHist.GetYaxis().SetRangeUser(newLowerAxisLimit, newUpperAxisLimit)

                    significanceHist.Draw("P same") 

                    lowerLegend = setupTLegend()
                    lowerLegend.AddEntry(ratioHist, "Data / MC", "p")
                    lowerLegend.AddEntry(significanceHist, "sign.", "p")
                    lowerLegend.Draw()

                    lowerLegend.SetX2(.3)

                    ratioHist.GetYaxis().SetTitle("#splitline{Data / MC,}{significance.}")
                    #ratioHist.GetYaxis().SetTitle("Data / MC, significance")
                    #ratioHist.GetYaxis().CenterTitle(True)
                    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


                #if "m34" in  ratioHist.GetName() :  ratioHist.GetXaxis().SetRangeUser(10, 70)
            else: backgroundTHStack.GetXaxis().SetTitle( sortedSamples.values()[0].GetXaxis().GetTitle()  )

            #if "m34" in  backgroundTHStack.GetName() :  backgroundTHStack.GetXaxis().SetRangeUser(10, 70)




            canvas.Update() # we need to update the canvas, so that changes to it (like the drawing of a legend get reflected in its status)
            canvasList.append( copy.deepcopy(canvas) ) # save a deep copy of the canvas for later use
            if args.holdAtPlot: import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    #for histogram in canvasList: 
    #    if "ZXSR" not in histogram.GetName():
    #        canvasList.remove(histogram)

    # sort canvasList by hist title, use this nice lambda construct        
    canvasList.sort( key = lambda x:x.GetTitle()) # i.e. we are sorting the list by the output of a function, where the function provides takes implicitly elements of the list, and in our case calls the .GetTitle() method of that element of the list and outputs it


    if isinstance(args.input,list):  postProcessedDataFileName = os.path.basename( args.input[0] ) # split off the file name from the path+fileName string if necessary
    else:                            postProcessedDataFileName = os.path.basename( args.input ) # split off the file name from the path+fileName string if necessary

    if args.outputName is None: outputName = postProcessedDataFileName.split(".")[0] +  "_"+args.mcCampaign+"_"
    else:                       outputName = args.outputName

    indexFile = open(outputName+".txt", "w") # w for (over) write
    # Write the Histograms to a ROOT File
    outoutROOTFile = ROOT.TFile(outputName+".root","RECREATE")
    counter = 0
    for histogram in canvasList: 
        
        counter +=1

        tempName = histogram.GetName()
        
        histogram.SetName( str(counter) + " - " + histogram.GetName() )
        histogram.Write() # write to the .ROOT file

        printRootCanvasPDF(histogram, isLastCanvas = histogram==canvasList[-1] , 
                           fileName = outputName+".pdf", tableOfContents = str(counter) + " - " + histogram.GetTitle() ) # write to .PDF
        indexFile.write(str(counter) + "\t" + histogram.GetName() + "\n"); 

        histogram.SetName(tempName)
    outoutROOTFile.Close()
    indexFile.close()

    printSubsetOfHists( canvasList, searchStrings=["M34","M4l"], outputDir = "supportnoteFigs")

    reportMemUsage.reportMemUsage(startTime)

    print("All plots processed!")
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

