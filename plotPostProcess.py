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
import numpy as np # good ol' numpy
import warnings # to warn about things that might not have gone right
import itertools # to cycle over lists in a nice automated way
import re # to do regular expression matching
import copy # for making deep copies
import argparse # to parse command line options
#import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import functions.RootTools as RootTools# root tool that I have taken from a program by Turra
import os
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly


class DSIDHelper:


    physicsProcess={"H->ZZ*->4l" : [341964, 341947, 345060, 341488, 345046, 345047, 345048, 345066, 344973, 344974],
                      "ZZ*->4l" :    [364250, 364251, 364252, 361603, 342556, 343232, 343212, 343213, 345708, 345709],
                      "Reducible (Z+Jets, WZ, ttbar)"  : [364114, 364115, 364116, 364117, 364118, 364119, 364120, 364121, 364122, 
                                                          364123, 364124, 364125, 364126, 364127, 364100, 364101, 364102, 364103, 
                                                          364104, 364105, 364106, 364107, 364108, 364109, 364110, 364111, 364112, 
                                                          364113, 364128, 364129, 364130, 364131, 364132, 364133, 364134, 364135, 
                                                          364136, 364137, 364138, 364139, 364140, 364141, 361601, 410472],
                       "VVV/VBS" : [364248, 364247, 364245, 364243, 364364],
                       "Z+(ttbar/J/Psi/Upsilon)" : [410142] 
                    }

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

    def __init__(self):
        self.physicsProcessByDSID    = self.makeReverseDict( self.physicsProcess);
        self.physicsSubProcessByDSID = self.makeReverseDict( self.physicsSubProcess);




    def getProduct_CrossSec_kFactor_genFiltEff(self, DSID):
        DSID = int(DSID)
        
        prod = self.metaDataDict[DSID]["crossSection"] * self.metaDataDict[DSID]["kFactor"] * self.metaDataDict[DSID]["genFiltEff"]
        
        return prod


        
    
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


    def importMetaData(self,metadataFileLocation):
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
        return metaDataDict, physicsShort

# end  class DSIDHelper



def getTDirsAndContents(TDir, outputDict = {}, recursiveCounter = 0):
    # for a given TDirectory (remember that a TFile is also a TDirectory) get all TH1 (recursively if needed)
    # output will be {TDirObject : names of objects that are not TDirs themselves}
    # we can do this recursively up to a depth of 'recursiveCounter' (if it is set to >0)
    # Then the output will be like 
    # {TDirObject1 : names of objects in TDirObject1 that are not TDirs themselves,
    #  TDirObject2 : names of objects in TDirObject2 that are not TDirs themselves }
    # The relationship between the TDirs is not being stored in this way

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    TH1List = [] # store the non-TDirecotry contents of the current dir here

    for TKey in TDirKeys: 
        # if current TKey refers to a dir, look recursively within (if our recursive counter is still not zero)
        # otherwise note the name of the contents
        if TKey.IsFolder() :
            if isinstance( TDir.Get(TKey.GetName()) ,ROOT.TTree): continue # turns out TTrees are also folders, but they don't contain Hists that we are interested in
            if recursiveCounter < 1       : continue # make sure we can exhaust our recursion counter
            
            subdir = TDir.Get(TKey.GetName())
            outputDict = getTDirsAndContents(subdir, outputDict, recursiveCounter = recursiveCounter-1 )
        elif isinstance(TDir.Get(TKey.GetName()), ROOT.TH1 ) and not isinstance(TDir.Get(TKey.GetName()), ROOT.TH2 ):  #check that the TKey indeed refers to a TH1
            TH1List.append(TKey.GetName())

    outputDict[TDir] = TH1List

    return outputDict

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

def colorDictOfHists(mergedSamplesDICT):
    mergeFillColors = itertools.cycle([ ROOT.kViolet,   ROOT.kYellow,   ROOT.kCyan,   ROOT.kBlue,   ROOT.kRed,   ROOT.kMagenta,   ROOT.kPink,   ROOT.kOrange,   ROOT.kSpring,   ROOT.kGreen,   ROOT.kTeal,   ROOT.kAzure,
                                        ROOT.kViolet-6, ROOT.kYellow-6, ROOT.kCyan-6, ROOT.kBlue-6, ROOT.kRed-6, ROOT.kMagenta-6, ROOT.kPink-6, ROOT.kOrange-6, ROOT.kSpring-6, ROOT.kGreen-6, ROOT.kTeal-6, ROOT.kAzure-6,
                                        ROOT.kViolet-2, ROOT.kYellow-2, ROOT.kCyan-2, ROOT.kBlue-2, ROOT.kRed-2, ROOT.kMagenta-2, ROOT.kPink-2, ROOT.kOrange-2, ROOT.kSpring-2, ROOT.kGreen-2, ROOT.kTeal-2, ROOT.kAzure-2,]) 

    if isinstance(mergedSamplesDICT, dict ):
        for process in mergedSamplesDICT.keys(): mergedSamplesDICT[process].SetFillColor(mergeFillColors.next())

    elif isinstance(mergedSamplesDICT, list ):
        for hist in mergedSamplesDICT.keys():    hist.SetFillColor(mergeFillColors.next())

    return None


def getHistIntegralWithUnertainty(hist, lowerLimit = 0, upperLimit = None ):

    #TH1::Integral returns the integral of bins in the bin range (default(1,Nbins).
    #If you want to include the Under/Overflow, use h.Integral(0,Nbins+1)
    
    if upperLimit is None: upperLimit = hist.GetNbinsX() +1
    integralUncertainty = ROOT.Double()

    integral = hist.IntegralAndError( lowerLimit , upperLimit, integralUncertainty)
    return integral, integralUncertainty


def splitHistNamesByPlotvariable(histNameList, delimeter = "_", nonEndingStringParts = 2): 
    # create a mapping {ending1 : [histogram names with ending1], ending2 : ...}
    # we wanna group the hist names together that shall be plotted together
    # we we are doing that by grouping them together by the endings
    # by default we take the strings to be splittable by the delimeter "_"
    # and that only the first two parts of the string are not part of the ending

    histsByEnding = {}

    for histName in histNameList:
        histNameParts = histName.split(delimeter)
        currentEnding = delimeter.join(histNameParts[nonEndingStringParts:]) # by conventoin we take the first part of the hist name to be an indicator of the type of object, and the second part the DSID

        if currentEnding in histsByEnding.keys():   histsByEnding[currentEnding].append(histName)
        else:                               histsByEnding[currentEnding] = [histName]

    # sort hist names alphabetically, to have a well defined squence of histograms 
    for histEnding in histsByEnding.keys(): # iterate over all the 'endings'
        histsByEnding[histEnding].sort() # sort hist names alphabetically, to have a well defined squence of histograms 

    return histsByEnding




def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.15,0.65,0.45,0.87)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(2);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend



def getSumOfWeigts(topLevelTObjects):
    # get the sum of weights for our MC samples
    # expects as input the following data structure:
    # {TDirObject1 : [list of the names of the TH1s in the TDirObject1 which contain the sum of weights in the bin named 'sumOfEventWeights_xAOD' ],
    #  TDirObject2 : [ same like above, but now for the TH1 names in TDirObject2 ],
    #   etc }
    # will get the sum of weigts and output them in a dict like  {DSID : sumAODWeights}

    sumOfEventWeightsDict = {}

    for TDir in topLevelTObjects.keys():
        histNames = topLevelTObjects[TDir]

        for name in histNames:
            currentTH1 = TDir.Get(name)

            sumAODWeights = currentTH1.GetBinContent(currentTH1.GetXaxis().FindBin("sumOfEventWeights_xAOD"))

            DSID = name.split("_")[1]
            sumOfEventWeightsDict[int(DSID)] = sumAODWeights

    return sumOfEventWeightsDict

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

def mergeTHStackHists(myTHStack):
    # Take a THStack and merge all the histograms comprising it into a single new one
    # requires that all the thists hace identical binning

    ROOT.SetOwnership(backgroundTHStack, False) # We need to set this, to aoid a segmentation fault: https://root-forum.cern.ch/t/crash-on-exit-with-thstack-draw-and-gethists/11221
    constituentHists =  myTHStack.GetHists() 

    mergedHist  = constituentHists[0].Clone( constituentHists.GetName() + "_merged")

    for hist in constituentHists:
        if hist != constituentHists[0]: mergedHist.Add(hist)

    return mergedHist

def getFirstAndLastNonEmptyBinInHist(hist, offset = 0, adjustXAxisRange = False):

    if isinstance(hist,ROOT.THStack):  hist = mergeTHStackHists(hist)

    nBins = hist.GetNbinsX()

    first =0 ;last=0

    for n in xrange(1,nBins+1): 
        if hist.GetBinContent(n) != 0: 
            first = n ; break
    for n in xrange(nBins+1,1,-1):
        if hist.GetBinContent(n) != 0: 
            last = n ; break

    #if adjustXAxisRange:

    if first is not 0: first -= offset
    if last  is not 0: last  += offset


    return (first, last)


def getFirstAndLastNonEmptyBinInTPad(myTPad):



    first = float("-inf"); last = float("+inf")

    TPadPrimitives = myTPad.GetListOfPrimitives()



    for prim in TPadPrimitives:
        if isinstance(prim,ROOT.TH1) or isinstance(prim,ROOT.THStack): 
            (firstTmp,lastTmp) = getFirstAndLastNonEmptyBinInHist(prim)
            foundAnyHists = True


#To get the y value corresponding to bin k, h->GetBinContent(k);
#To get the bin number k corresponding to an x value, do
#  int k = h->GetXaxis()->FindBin(x);


def getWellStructedDictFromCommandLineOptions( args, inputFileDict = collections.defaultdict(dict) ):

    # assemble the input files, mc-campaign tags and metadata file locations into dict
    # well structered dict is sorted by mc-campign tag and has 

    inputFileDict = collections.defaultdict(dict)

    for n in xrange(0, len(args.input) ): 

        mcCampaign = args.mcCampaign[n]

        inputFileDict[mcCampaign]["inputStr"] = args.input[n]
        inputFileDict[mcCampaign]["TFile"] =  ROOT.TFile(args.input[n],"READ"); # open the file with te data from the ZdZdPostProcessing

        # fill in the metadata location
        inputFileDict[mcCampaign]["bkgMetaFilePath"] = args.metaData

        ######################################################
        # Set up DSID helper
        ######################################################
        # the DSID helper has two main functions
        # 1) administrating the metadata 
        #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
        # 2) grouping DSIDs into physics categories for the plots
        #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process

        inputFileDict[mcCampaign]["DSIDHelper"] = DSIDHelper()
        inputFileDict[mcCampaign]["DSIDHelper"].importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati

    return inputFileDict


def fillMasterHistDict( inputFileDict , masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):

    # split the histograms in inputFileDict by HistEnding, mcCampaign, and DSID 
    # and put them into a collections.defaultdict to indext them by HistEnding, mcCampaign, and DSID
    #
    # masterHistDict[ HistEnding ][ mcCampaign ][ DSID ][ ROOT.TH1 ] 


    for mcTag in inputFileDict.keys():

        postProcessedData = inputFileDict[mcTag]["TFile"]
        DSIDHelper = inputFileDict[mcTag]["DSIDHelper"]

        # get the histograms in the diffrent TDirectories within the provided .root file
        dirsAndContents = getTDirsAndContents(postProcessedData, outputDict = {}, recursiveCounter = float("inf"))



        ######### get sumOfWeights #########
        # we take the histograms that store the sumOfWeights are in the top-level of the TFile, i.e. not in a sub-TDirectory
        topLevelTObjects = {postProcessedData : dirsAndContents[postProcessedData]}
        del dirsAndContents[postProcessedData] # remove the top level entries, they are only ought to contain the sumOfWeights
        sumOfWeights = getSumOfWeigts(topLevelTObjects)

        for TDir in dirsAndContents.keys(): # We iterate through the different TDirs in the files
            histNames = dirsAndContents[TDir] # get the list of histograms in this TDir, specifically get the list of histogram names in that directory

            # we have histograms that show distributions of kinematic variables after cuts (analysisHists)
            # and histograms that show how many events are left after each cut (cutflowHists), we wanna plot the former (analysisHists)
            # so let's get a list of the analysisHists
            analysisHists = []
            for histName in histNames :  
                if "cutflow" in histName: continue
                if histName.startswith("h2_"): continue
                if histName.endswith("Weight"): continue
                analysisHists.append(histName)

            # get a mapping like {ending, [histnames with that ending], ... }, because hists with a common ending shall be plotted together
            histsByEnding = splitHistNamesByPlotvariable(analysisHists) 

            for histEnding in histsByEnding.keys(): # iterate over all the 'endings'
                for histName in histsByEnding[histEnding]: 

                    DSID = histName.split("_")[1] # get the DSID from the name of the histogram, which should be like bla_DSID_bla_...
                    currentTH1 = TDir.Get(histName)#.Clone() # get a clone of the histogram, so that we can scale it, without changeing the original
                    
                    if int(DSID) > 0: # Signal & Background have DSID > 0
                        scale = lumiMap[mcTag] * 1000000. * DSIDHelper.getProduct_CrossSec_kFactor_genFiltEff(DSID) / sumOfWeights[int(DSID)]
                        currentTH1.Scale(scale) # scale the histogram

                    masterHistDict[ histEnding ][ mcTag ][ DSID ] = currentTH1

    return masterHistDict

def mergeMultiMCTagMasterHistDict(masterHistDict, combinedMCTagHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) ):

    if len( masterHistDict.values()[0].keys() ) == 1:  # if there's only one MCTag we do not need to combine the hists, and we can return the input dict
        return masterHistDict 

    for histEnding in masterHistDict.keys():
        for mcTag in masterHistDict[histEnding].keys():
            for DSID in masterHistDict[histEnding][mcTag].keys():

                currentTH1 =  masterHistDict[histEnding][mcTag][DSID]

                if DSID not in combinedMCTagHistDict[histEnding]["allMCCampaigns"].keys(): 
                    combinedMCTagHistDict[histEnding]["allMCCampaigns"][DSID] = currentTH1.Clone()
                else : combinedMCTagHistDict[histEnding]["allMCCampaigns"][DSID].Add(currentTH1)

    return combinedMCTagHistDict

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

def addRegionAndChannelToStatsText(canvasName):

    outList = ""

    shortName = canvasName.split("_")[0]

    # fill in region
    if "SR" in shortName:    outList += "Signal Region"
    elif "CRC" in shortName: outList += "VR1"
    elif "CRD" in shortName: outList += "VR2"

    outList += ", "

    if "4m" in shortName:     outList += "4#mu"
    elif "2e2m" in shortName: outList += "2e2#mu"
    elif "2m2e" in shortName: outList += "2#mu2e"
    elif "4e" in shortName:   outList += "4e"
    else:     outList += "4#mu, 2e2#mu, 2#mu2e, 2#mu2e"

    return outList

if __name__ == '__main__':

    ######################################################
    # Define some default or hardcoded values
    ######################################################


    # campaigns integrated luminosity,  complete + partial
    lumiMap= { "mc16a" : 36.21496, "mc16d" : 44.3074, "mc16e": 59.9372, "mc16ade": 140.45956, "units" : "fb-1"}
    #taken by Justin from: https://twiki.cern.ch/twiki/bin/view/Atlas/LuminosityForPhysics#2018_13_TeV_proton_proton_placeh
    #2015: 3.21956 fb^-1 +- 2.1% (final uncertainty) (3.9 fb^-1 recorded)
    #2016: 32.9954 fb^-1 +- 2.2% (final uncertainty) (35.6 fb^-1 recorded)
    #2017: 44.3074 fb^-1 +- 2.4% (preliminary uncertainty) (46.9 fb^-1 recorded)
    #2018: 59.9372 fb^-1 +- 5% (uncertainty TBD, use this as a placeholder) (62.2 fb^-1 recorded)
    #Total: 140.46 fb^-1


    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, nargs='*', help="name or path to the input files")

    parser.add_argument("-c", "--mcCampaign", nargs='*', type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], required=True,
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="metadata/md_bkg_datasets.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument( "--DSID_Binning", type=str, help = "set how the different DSIDS are combined, ",
        choices=["physicsProcess","physicsSubProcess","DSID"] , default="physicsProcess" )

    parser.add_argument( "--holdAtPlot", type=bool, default=False , 
        help = "Debugging option. If True sets a debugger tracer and \
        activates the debugger at the point where the plot has has been fully assembled." ) 

    parser.add_argument( "--outputName", type=str, default=None , 
        help = "Pick the name of the output files. \
        We'll produce three of them: a root file output (.root), pdfs of the histograms (.pdf) and a .txt indexing the histogram names.\
        If no outputName is choosen, we will default to <inputFileName>_<mcCampaign>_outHistograms." ) 

    parser.add_argument( "--rebin", type=int, default=1 , 
    help = "We can rebin the bins. Choose rebin > 1 to rebin #<rebin> bins into 1." ) 

    args = parser.parse_args()


    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    assert len(args.input) ==  len(args.mcCampaign), "We do not have exactly one mc-campaign tag per input file"

    
    assert all( x==1   for x in collections.Counter( args.mcCampaign ).values() ), "\
    Some mc-campaign tags have been declared more than once. \
    For now we are only setup to support one file per MC-tag. Until we changed that, 'hadd' them in bash"


    # assemble the input files, mc-campaign tags and metadata file locations into dict
    # well structered dict is sorted by mc-campign tag and has 
    inputFileDict = getWellStructedDictFromCommandLineOptions( args, inputFileDict = collections.defaultdict(dict) )




    ######################################################
    # Do the data processing from here on
    ######################################################



    masterHistDict = fillMasterHistDict( inputFileDict )

    combinedMCTagHistDict = mergeMultiMCTagMasterHistDict(masterHistDict)

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
                        currentTH1.SetFillStyle(1001) # 1001 - Solid Fill: https://root.cern.ch/doc/v608/classTAttFill.html
                        currentTH1.SetFillColor(fillColors.next())

                        backgroundSamples.append( ( int(DSID), currentTH1) )

                    else:   # data has DSID 0 for us  
                        gotDataSample = True
                        dataTH1 = currentTH1

#    ######### process the cutflow histograms #########


            if   args.DSID_Binning == "physicsProcess" :    DSIDMappingDict = inputFileDict.values()[0]['DSIDHelper'].physicsProcessByDSID
            elif args.DSID_Binning == "physicsSubProcess" : DSIDMappingDict = inputFileDict.values()[0]['DSIDHelper'].physicsSubProcessByDSID
            elif args.DSID_Binning == "DSID" : # if we choose to do the DSID_Binning by DSID, we build here a a mapping DSID -> str(DSID)
                DSIDMappingDict = {}
                for aTuple in backgroundSamples: DSIDMappingDict[aTuple[0]] = str( aTuple[0] )  #DSID, histogram = aTuple

            #print(backgroundSamples)
            #import pdb; pdb.set_trace() # import the debugger and instruct
            sortedSamples = mergeHistsByMapping(backgroundSamples, DSIDMappingDict)
            colorDictOfHists(sortedSamples) # change the fill colors of the hists in a nice way
            statsTexts = []

            statsTexts.append( "#font[72]{ATLAS} internal")
            statsTexts.append( "#sqrt{s} = 13 TeV, %.1f fb^{-1}" %(lumiMap[mcTag] ) ) 

            statsTexts.append( addRegionAndChannelToStatsText(canvas.GetName() ) ) 
            statsTexts.append( "  " ) 


            for key in sortedSamples.keys(): # add merged samples to the backgroundTHStack
                mergedHist = sortedSamples[key]
                backgroundTHStack.Add( mergedHist )
                legend.AddEntry(mergedHist , key , "f");
                statsTexts.append( key + ": %.2f #pm %.2f" %( getHistIntegralWithUnertainty(mergedHist)) )

            # create a pad for the CrystalBall fit + data
            histPadYStart = 3./13
            histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
            ROOT.SetOwnership(histPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
            histPad.SetBottomMargin(0.04); # Upper and lower plot are joined
            #histPad.SetGridx();          # Vertical grid
            histPad.Draw();              # Draw the upper pad: pad1
            histPad.cd();                # pad1 becomes the current pad

            backgroundTHStack.Draw("Hist")


            backgroundMergedTH1 = mergeTHStackHists(backgroundTHStack) # get a merged background to draw uncertainty bars on the total backgroun

            backgroundMergedTH1.Draw("same E2 ")
            #backgroundMergedTH1.SetMarkerStyle(25 )
            backgroundMergedTH1.SetFillStyle(3004)
            backgroundMergedTH1.SetFillColor(1)

            #if "eta"   in backgroundMergedTH1.getTitle: yAxisUnit = ""
            #elif "phi" in backgroundMergedTH1.getTitle: yAxisUnit = " radians"

            backgroundTHStack.GetYaxis().SetTitle("Events / " + str(backgroundMergedTH1.GetBinWidth(1) )+" GeV" )
            backgroundTHStack.GetYaxis().SetTitleSize(0.05)
            backgroundTHStack.GetYaxis().SetTitleOffset(0.8)
            backgroundTHStack.GetYaxis().CenterTitle()
            
            statsTexts.append( "  " )       
            statsTexts.append( "Background: %.2f #pm %.2f" %( getHistIntegralWithUnertainty(backgroundMergedTH1)) )




            # use the x-axis label from the original plot in the THStack, needs to be called after 'Draw()'
            #backgroundTHStack.GetXaxis().SetTitle( mergedHist.GetXaxis().GetTitle() )

            if gotDataSample: # add data samples
                dataTH1.Draw("same")
                if max(getBinContentsPlusError(dataTH1)) > backgroundTHStack.GetMaximum(): backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)) +1 )

                legend.AddEntry(currentTH1, "data", "l")

                statsTexts.append("Data: %.2f #pm %.2f" %( getHistIntegralWithUnertainty(dataTH1) ) )  

            axRangeLow, axRangeHigh = getFirstAndLastNonEmptyBinInHist(backgroundTHStack, offset = 1)
            backgroundTHStack.GetXaxis().SetRange(axRangeLow,axRangeHigh)
            
            statsTPave=ROOT.TPaveText(0.60,0.65,0.9,0.87,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
            for stats in statsTexts:   statsTPave.AddText(stats);
            statsTPave.Draw();
            legend.Draw(); # do legend things


            canvas.cd()

            # define a TPad where we can add a histogram of the ratio of the data and MC bins
            ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);
            ROOT.SetOwnership(ratioPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
            ratioPad.SetTopMargin(0.)
            ratioPad.SetBottomMargin(0.3)
            ratioPad.SetGridy(); #ratioPad.SetGridx(); 
            ratioPad.Draw();              # Draw the upper pad: pad1
            ratioPad.cd();                # pad1 becomes the current pad



            if gotDataSample: # fill the ratio pad with the ratio of the data bins to  mc bckground bins
                ratioHist = dataTH1.Clone( dataTH1.GetName()+"_Clone" )
                ratioHist.Divide(backgroundMergedTH1)
                ratioHist.GetXaxis().SetRange(axRangeLow, axRangeHigh)
                ratioHist.SetStats( False) # remove stats box
                
                ratioHist.SetTitle("")
                
                ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
                ratioHist.GetYaxis().SetLabelSize(0.1)

                ratioHist.GetYaxis().SetTitle("Data / MC")
                ratioHist.GetYaxis().SetTitleSize(0.13)
                ratioHist.GetYaxis().SetTitleOffset(0.25)
                ratioHist.GetYaxis().CenterTitle()

                ratioHist.GetXaxis().SetLabelSize(0.12)
                ratioHist.GetXaxis().SetTitleSize(0.12)
                ratioHist.Draw()



            canvas.Update() # we need to update the canvas, so that changes to it (like the drawing of a legend get reflected in its status)
            canvasList.append( copy.deepcopy(canvas) ) # save a deep copy of the canvas for later use
            if args.holdAtPlot: import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    #for histogram in canvasList: 
    #    if "ZXSR" not in histogram.GetName():
    #        canvasList.remove(histogram)

    # sort canvasList by hist title, use this nice lambda construct        
    canvasList.sort( key = lambda x:x.GetTitle()) # i.e. we are sorting the list by the output of a function, where the function provides takes implicitly elements of the list, and in our case calls the .GetTitle() method of that element of the list and outputs it



    postProcessedDataFileName = os.path.basename( args.input[0] ) # split off the file name from the path+fileName string if necessary

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

    printSubsetOfHists( canvasList, searchStrings=["M12","M34","M4l"], outputDir = "supportnoteFigs")

    print("All plots processed!")
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

