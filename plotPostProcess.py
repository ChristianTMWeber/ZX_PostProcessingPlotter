#############################
#   
# python programm to make plotsout of the post processing outputs   
#
# run as:       python plotPostProcess.py ZZdPostProcessOutput.root --mcCampaign mc16a 
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
import os
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

from functions.compareVersions import compareVersions # to compare root versions
import functions.rootDictAndTDirTools as rootDictAndTDirTools
import functions.histHelper as histHelper # to help me with histograms

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
                            "ZdZd, m_{Zd} = 60GeV" : [302087]}

    colorMap = {"H->ZZ*->4l" : ROOT.kRed  , "ZZ*->4l" :   ROOT.kAzure+1 ,
                      "Reducible (Z+Jets, WZ, ttbar)"  : ROOT.kYellow , "VVV/VBS" : ROOT.kCyan,
                       "Z+(ttbar/J/Psi/Upsilon)" : ROOT.kGreen, "VVV, tt+Z" : ROOT.kGreen , 
                       "H4l"  : ROOT.kRed  , "ZZ" :   ROOT.kAzure+1,   "const" : ROOT.kYellow} # colors for the analysisMapping

    physicsSubProcess = {"ggH" : [345060], "VBFH":[341488], "WH" : [341964], "ZH" : [341947],
                     "ggZH" : [345066], "ttH125" : [345046, 345047, 345048], "bbH" : [344973, 344974],
                     "qq->ZZ*->4l" : [364250, 364251, 364252], "gg->ZZ*->4l" : [345708, 345709],
                     "ZZZ" : [364248, 364247], "WZZ" : [364245], "WWZ" : [364243], 
                     "lllljj" : [364364], "ttll" : [410142], "WZ" : [361601], "ttbar" : [410472],
                     "Z+Jets (Sherpa)" : [364114, 364115, 364116, 364117, 364118, 364119, 364120, 
                                          364121, 364122, 364123, 364124, 364125, 364126, 364127, 
                                          364100, 364101, 364102, 364103, 364104, 364105, 364106, 
                                          364107, 364108, 364109, 364110, 364111, 364112, 364113, 
                                          364128, 364129, 364130, 364131, 364132, 364133, 364134, 
                                          364135, 364136, 364137, 364138, 364139, 364140, 364141]
                     }

    analysisMapping =   {   "H4l"    : [341964, 341947, 345060, 341488, 345046, 345047, 345048, 345066, 344973, 344974],
                            "ZZ"     : [364250, 364251, 364252, 361603, 342556, 343232, 343212, 343213, 345708, 345709],
                            "Reducible"  : [364114, 364115, 364116, 364117, 364118, 364119, 364120, 364121, 364122, 
                                            364123, 364124, 364125, 364126, 364127, 364100, 364101, 364102, 364103, 
                                            364104, 364105, 364106, 364107, 364108, 364109, 364110, 364111, 364112, 
                                            364113, 364128, 364129, 364130, 364131, 364132, 364133, 364134, 364135, 
                                            364136, 364137, 364138, 364139, 364140, 364141, 361601, 410472],
                            "VVV_Z+ll" : [364248, 364247, 364245, 364243, 364364.,
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

    def __init__(self):

        
        # add the signal into the physics(Sub)Process
        self.physicsProcess.update( self.physicsProcessSignal )
        self.physicsSubProcess.update( self.physicsProcessSignal )
        self.analysisMapping.update( self.physicsProcessSignal )

        # make the reverse dicts so that we can look up things by DSID
        self.physicsProcessByDSID    = self.makeReverseDict( self.physicsProcess);
        self.physicsSubProcessByDSID = self.makeReverseDict( self.physicsSubProcess);
        self.analysisMappingByDSID = self.makeReverseDict( self.analysisMapping)
        self.physicsProcessSignalByDSID = self.makeReverseDict( self.physicsProcessSignal)

    def setMappingOfChoice(self, mapping ):


        if   mapping == "physicsProcess" :    self.mappingOfChoice = self.physicsProcessByDSID
        elif mapping == "physicsSubProcess" : self.mappingOfChoice = self.physicsSubProcessByDSID
        elif mapping == "analysisMapping" :   self.mappingOfChoice = self.analysisMappingByDSID
        else:                                 self.mappingOfChoice = mapping

        return None

    def isSignalSample(self , KeyOrDSID ):

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

    if "Nominal" not in path: return True
    elif "Cutflow" in path: return True
    elif "cutflow" in path: return True
    elif "h_raw_" in path: return True
    elif "hraw_" in path: return True
    elif "pileupWeight" in path: return True
    elif isinstance( baseHist, ROOT.TH2 ): return True
    elif not isinstance( baseHist, requiredRootType ): return True

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



def fillMasterHistDict2( currentTH1, histEnding, mcTag, DSID, aDSIDHelper, masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):
    # split the histograms in inputFileDict by HistEnding, mcCampaign, and DSID 
    # and put them into a collections.defaultdict to indext them by HistEnding, mcCampaign, and DSID
    #
    # remember that python instantiates functions only once, 
    # so unless we provice a masterHistDict, we will aggregate results 
    # in the default one over multiple function calls
    #
    # masterHistDict[ HistEnding ][ mcCampaign ][ DSID ][ ROOT.TH1 ] 

    if int(DSID) != 0: # Signal & Background have DSID > 0
        scale = aDSIDHelper.getMCScale(DSID, mcTag)
        currentTH1.Scale(scale) # scale the histogram

    masterHistDict[histEnding][mcTag][DSID]=currentTH1

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

    if "4m" in shortName:     outList += "4#mu"
    elif "2e2m" in shortName: outList += "2e2#mu"
    elif "2m2e" in shortName: outList += "2#mu2e"
    elif "4e" in shortName:   outList += "4e"
    else:     outList += "4#mu, 2e2#mu, 2#mu2e, 4e"

    return outList

if __name__ == '__main__':



    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("-c", "--mcCampaign", nargs='*', type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], required=True,
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

    args = parser.parse_args()


    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    assert 1 ==  len(args.mcCampaign), "We do not have exactly one mc-campaign tag per input file"
    #assert len(args.input) ==  len(args.mcCampaign)

    assert all( x==1   for x in collections.Counter( args.mcCampaign ).values() ), "\
    Some mc-campaign tags have been declared more than once. \
    For now we are only setup to support one file per MC-tag. Until we changed that, 'hadd' them in bash"

    # check root version
    currentROOTVersion = ROOT.gROOT.GetVersion()

    if compareVersions( currentROOTVersion, "6.04/16") > 0:
        warnings.warn("Running on newer than ideal root version. Designed for version 6.04/16, current version is  "
                       + currentROOTVersion + ". This should work but might consume much more memory then otherwise. ")
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

    # assemble the input files, mc-campaign tags and metadata file locations into dict
    # well structered dict is sorted by mc-campign tag and has 

    #######################
    # Test generator access to ROOT TH1s 

    #postProcessedData = inputFileDict.values()[0]["TFile"]


    postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)

    histCounter = 0 # count how many relevant hists we have

    # loop over all of the TObjects in the given ROOT file                         # newOwnership set to none for newer root versions, set to true for older ones
    for path, baseHist  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = ownershipSetpoint): 

        if irrelevantTObject(path, baseHist): continue # skip non-relevant histograms

        ROOT.SetOwnership(baseHist, False)  # if we pass irrelevantTObject the histogram is relevant, so we change the ownership here to False in the attempt to prevent deletion

        # discern DSID and plotTitle to use them when sorting into a tree structure
        DSID = myDSIDHelper.idDSID(path)

        # 15GeV , 20GeV , 25GeV , 30GeV , 35GeV , 40GeV , 45GeV , 50GeV , 55GeV
        # 343234, 343235, 343236, 343237, 343238, 343239, 343240, 343241, 343242

        #                                          343237, #
        if int(DSID) in [ 343234, 343235, 343236,         343238, 343239, 343240, 343241, 343242]: continue # skip ZZd samples, except the 30 GeV one
        if int(DSID) in [302073, 302074, 302075, 302076, 302077, 302078, 302079, 302080, 302081, 302082, 
                         302083, 302084, 302085, 302086, 302087, 302088, 302089, 302090, 309475, 309476, 
                         309477, 309478, 309479, 309480, 309481, 309482, 309483, 309484, 309485, 309709]: continue # non ZZd signal sample DSIDS, i.e. ZdZd signal sample DSIDs
        plotTitle = idPlotTitle(path, myDSIDHelper, DSID=DSID)

        # build my tree structure here to house the relevant histograms, pre-sorted for plotting
        masterHistDict = fillMasterHistDict2( baseHist, plotTitle, args.mcCampaign[0], DSID, myDSIDHelper )

        # output a running counter of processed hists and used memory
        histCounter += 1
        if histCounter %1000 == 0: print str(histCounter) + " relevant hists processed. \t Memory usage: %s (MB)" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000)



    ######################################################
    # Do the data processing from here on
    ######################################################


    combinedMCTagHistDict = masterHistDict

    canvasList = []

    for histEnding in combinedMCTagHistDict.keys():

        backgroundTHStack = ROOT.THStack(histEnding,histEnding)
        backgroundSamples = [] # store the background samples as list of tuples [ (DSID, TH1) , ...] 
        #backgroundTHStack.SetMaximum(25.)
        canvas = ROOT.TCanvas(histEnding,histEnding,1300/2,1300/2);
        ROOT.SetOwnership(canvas, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
        legend = setupTLegend()


        # define fill colors, use itertools to cycle through them, access via fillColors.next()
        fillColors = itertools.cycle([ROOT.kBlue,   ROOT.kViolet,   ROOT.kMagenta,   ROOT.kPink,   ROOT.kRed,   ROOT.kOrange,   ROOT.kYellow,   ROOT.kSpring,   ROOT.kGreen,   ROOT.kTeal,   ROOT.kCyan,   ROOT.kAzure,
                                      ROOT.kBlue-6, ROOT.kViolet-6, ROOT.kMagenta-6, ROOT.kPink-6, ROOT.kRed-6, ROOT.kOrange-6, ROOT.kYellow-6, ROOT.kSpring-6, ROOT.kGreen-6, ROOT.kTeal-6, ROOT.kCyan-6, ROOT.kAzure-6,
                                      ROOT.kBlue+2, ROOT.kViolet+2, ROOT.kMagenta+2, ROOT.kPink+2, ROOT.kRed+2, ROOT.kOrange+2, ROOT.kYellow+2, ROOT.kSpring+2, ROOT.kGreen+2, ROOT.kTeal+2, ROOT.kCyan+2, ROOT.kAzure+2]) 
        #ROOT.kBlue, ROOT.kViolet, ROOT.kMagenta, ROOT.kPink, ROOT.kRed, ROOT.kOrange, ROOT.kYellow, ROOT.kSpring, ROOT.kGreen, ROOT.kTeal, ROOT.kCyan, ROOT.kAzure
        #ROOT.kBlue-6, ROOT.kViolet-6, ROOT.kMagenta-6, ROOT.kPink-6, ROOT.kRed-6, ROOT.kOrange-6, ROOT.kYellow-6, ROOT.kSpring-6, ROOT.kGreen-6, ROOT.kTeal-6, ROOT.kCyan-6, ROOT.kAzure-6
        #ROOT.kBlue+2, ROOT.kViolet+2, ROOT.kMagenta+2, ROOT.kPink+2, ROOT.kRed+2, ROOT.kOrange+2, ROOT.kYellow+2, ROOT.kSpring+2, ROOT.kGreen+2, ROOT.kTeal+2, ROOT.kCyan+2, ROOT.kAzure+2



        gotDataSample = False # change this to true later if we do have data samples

        assert len( combinedMCTagHistDict[histEnding].keys() ) == 1, "We ended up with more than MC tag after the comining the masterHistDict. That shouldn't be the case"

        for mcTag in combinedMCTagHistDict[histEnding].keys():



            for DSID in combinedMCTagHistDict[histEnding][mcTag].keys():

                    currentTH1 = combinedMCTagHistDict[histEnding][mcTag][DSID]
                    currentTH1.Rebin(args.rebin)

                    if int(DSID) > 0: # Signal & Background have DSID > 0
                        backgroundSamples.append( ( int(DSID), currentTH1) )
                    else:   # data has DSID 0 for us  
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
            statsTexts.append( "#sqrt{s} = 13 TeV, %.1f fb^{-1}" %( myDSIDHelper.lumiMap[mcTag] ) ) 

            statsTexts.append( addRegionAndChannelToStatsText(canvas.GetName() ) ) 
            statsTexts.append( "  " ) 

            # use these to report the total number of background and signal samples each later on
            backgroundTallyTH1 = sortedSamples.values()[0].Clone( "backgroundTally")
            backgroundTallyTH1.Scale(0)
            signalTallyTH1 = backgroundTallyTH1.Clone("signalTally")

            for key in myDSIDHelper.defineSequenceOfSortedSamples( sortedSamples  ): # add merged samples to the backgroundTHStack 
                #for key in sortedSamples.keys(): # add merged samples to the backgroundTHStack
                mergedHist = sortedSamples[key]
                backgroundTHStack.Add( mergedHist )

                keyProperArrow = re.sub('->', '#rightarrow ', key) # make sure the legend displays the proper kind of arrow
                legend.AddEntry(mergedHist , keyProperArrow , "f");
                statsTexts.append( keyProperArrow + ": %.2f #pm %.2f" %( getHistIntegralWithUnertainty(mergedHist)) )

                if myDSIDHelper.isSignalSample( key ): signalTallyTH1.Add(sortedSamples[key])
                else:                                  backgroundTallyTH1.Add(sortedSamples[key])

            # create a pad for the CrystalBall fit + data
            if gotDataSample and not args.skipRatioHist: histPadYStart = 3./13
            else:  histPadYStart = 0
            histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
            ROOT.SetOwnership(histPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
            if gotDataSample and not args.skipRatioHist: histPad.SetBottomMargin(0.06); # Seperation between upper and lower plots
            else: histPad.SetBottomMargin(0.12)
            #histPad.SetGridx();          # Vertical grid
            histPad.Draw();              # Draw the upper pad: pad1
            histPad.cd();                # pad1 becomes the current pad

            backgroundTHStack.Draw("Hist")


            backgroundMergedTH1 = histHelper.mergeTHStackHists(backgroundTHStack) # get a merged background to draw uncertainty bars on the total backgroun

            backgroundMergedTH1.Draw("same E2 ")   # "E2" Draw error bars with rectangles:  https://root.cern.ch/doc/v608/classTHistPainter.html
            backgroundMergedTH1.SetMarkerStyle(0 ) # SetMarkerStyle(0 ) remove marker from combined backgroun
            backgroundMergedTH1.SetFillStyle(3244)#(3001) # fill style: https://root.cern.ch/doc/v614/classTAttFill.html#F2
            backgroundMergedTH1.SetFillColor(1)    # black: https://root.cern.ch/doc/v614/classTAttFill.html#F2

            legend.AddEntry(backgroundMergedTH1 , "MC stat. uncertainty" , "f");

            #if "eta"   in backgroundMergedTH1.getTitle: yAxisUnit = ""
            #elif "phi" in backgroundMergedTH1.getTitle: yAxisUnit = " radians"

            backgroundTHStack.GetYaxis().SetTitle("Events / " + str(backgroundMergedTH1.GetBinWidth(1) )+" GeV" )
            backgroundTHStack.GetYaxis().SetTitleSize(0.05)
            backgroundTHStack.GetYaxis().SetTitleOffset(1.1)
            backgroundTHStack.GetYaxis().CenterTitle()
            
            #backgroundTHStack.GetXaxis().SetTitleSize(0.12)
            backgroundTHStack.GetXaxis().SetTitleOffset(1.1)

            statsTexts.append( "  " )       
            #statsTexts.append( "Background + Signal: %.2f #pm %.2f" %( getHistIntegralWithUnertainty(backgroundMergedTH1)) )
            statsTexts.append( "Background : %.2f #pm %.2f" %( getHistIntegralWithUnertainty(backgroundTallyTH1)) )
            statsTexts.append( "Signal: %.2f #pm %.2f" %( getHistIntegralWithUnertainty(signalTallyTH1)) )




            # use the x-axis label from the original plot in the THStack, needs to be called after 'Draw()'
            #backgroundTHStack.GetXaxis().SetTitle( mergedHist.GetXaxis().GetTitle() )

            if gotDataSample: # add data samples
                dataTH1.Draw("same")
                #if max(getBinContentsPlusError(dataTH1)) > backgroundTHStack.GetMaximum(): backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)) +1 ) # rescale Y axis limit
                #backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)*1.3) )

                legend.AddEntry(currentTH1, "data", "l")

                statsTexts.append("Data: %.2f #pm %.2f" %( getHistIntegralWithUnertainty(dataTH1) ) )  

            # rescale Y-axis
            largestYValue = [max(getBinContentsPlusError(backgroundMergedTH1) )]
            if gotDataSample:  largestYValue.append( max( getBinContentsPlusError(dataTH1) ) )
            backgroundTHStack.SetMaximum( max(largestYValue) * 1.3 )

            #rescale X-axis
            axRangeLow, axRangeHigh = histHelper.getFirstAndLastNonEmptyBinInHist(backgroundTHStack, offset = 1)
            backgroundTHStack.GetXaxis().SetRange(axRangeLow,axRangeHigh)

            #statsOffset = (0.6,0.55), statsWidths = (0.3,0.32)
            statsTPave=ROOT.TPaveText(0.55,0.55,0.9,0.87,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
            for stats in statsTexts:   statsTPave.AddText(stats);
            statsTPave.Draw();
            legend.Draw(); # do legend things


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
                ratioHist.Divide(backgroundMergedTH1)
                ratioHist.GetXaxis().SetRange(axRangeLow, axRangeHigh)
                ratioHist.SetStats( False) # remove stats box
                
                ratioHist.SetTitle("")
                
                ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
                ratioHist.GetYaxis().SetLabelSize(0.1)

                ratioHist.GetYaxis().SetTitle("Data / MC")
                ratioHist.GetYaxis().SetTitleSize(0.11)
                ratioHist.GetYaxis().SetTitleOffset(0.4)
                ratioHist.GetYaxis().CenterTitle()

                ratioHist.GetXaxis().SetLabelSize(0.12)
                ratioHist.GetXaxis().SetTitleSize(0.13)
                ratioHist.GetXaxis().SetTitleOffset(1.0)
                ratioHist.Draw()
            else: backgroundTHStack.GetXaxis().SetTitle( sortedSamples.values()[0].GetXaxis().GetTitle()  )



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

    if args.outputName is None: outputName = postProcessedDataFileName.split(".")[0] + "_" + "_".join(args.mcCampaign)+"_"
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

    print("All plots processed!")
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

