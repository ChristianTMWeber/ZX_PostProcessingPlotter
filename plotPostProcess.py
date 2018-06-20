#############################
#   
# python programm to make plotsout of the post processing outputs   
#
#
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
                     "lllljj" : [364364], "ttll" : [410142], "WZ" : [361601],
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





def getTDirsAndContents(TDir, outputDict = {}, recursiveCounter = 0):
    # for a given TDirectory (remember that a TFile is also a TDirectory) get its contents
    # output will be {TDirObject : names of objects that are not TDirs themselves}
    # we can do this recursively up to a depth of 'recursiveCounter' (if it is set to >0)
    # Then the output will be like 
    # {TDirObject1 : names of objects in TDirObject1 that are not TDirs themselves,
    #  TDirObject2 : names of objects in TDirObject2 that are not TDirs themselves }
    # The relationship between the TDirs is not being stored in this way

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    contentList = [] # store the non-TDirecotry contents of the current dir here

    for TKey in TDirKeys: 
        # if current TKey refers to a dir, look recursively within (if out recursive counter is still not zero)
        # otherwise note the name of the contents
        if TKey.IsFolder() and recursiveCounter >= 1 : 
            subdir = TDir.Get(TKey.GetName())
            outputDict = getTDirsAndContents(subdir, outputDict, recursiveCounter = recursiveCounter-1 )
        else: contentList.append(TKey.GetName())

    outputDict[TDir] = contentList

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
        else:                                       mergedSamplesDICT[DSIDTarget]=histogram.Clone()

    return mergedSamplesDICT






#def binStringListByEnding(listOfStrings, endingStr):
#    # sorts a list of strings into two other lists, by asking for each of the strings
#    # if it ends with the desired ending string
#    hasCorrectEnding = []
#    hasWrongEnding = []
#
#    for string in listOfStrings:
#        if string.endswith(endingStr): hasCorrectEnding.append(string)
#        else:                       hasWrongEnding.append(string)
#
#    return hasCorrectEnding, hasWrongEnding
#
#def splitHistNamesByPlotvariable(histNameList, delimeter = "_", nonEndingStringParts = 2): 
#    # we wanna group the hist names together that shall be plotted together
#    # we we are doing that by grouping them together by the endings
#    # by default we take the strings to be splittable by the delimeter "_"
#    # and that only the first two parts of the string are not part of the ending
#
#    histsByPlotVariable = {}
#
#    while(histNameList): # while that list is not empty
#        
#        histNameParts = histNameList[0].split(delimeter)
#        currentEnding = delimeter.join(histNameParts[nonEndingStringParts:]) # by conventoin we take the first part of the hist name to be an indicator of the type of object, and the second part the DSID
#
#        currentHists, histNameList = binStringListByEnding(histNameList, currentEnding)
#
#        histsByPlotVariable[currentEnding] = currentHists
#
#    return histsByPlotVariable

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

    if tableOfContents is None: myRootCanvas.Print(fileName)
    else: myRootCanvas.Print(fileName, "Title:" + tableOfContents)

if __name__ == '__main__':

    ######################################################
    # Define some default or hardcoded values
    ######################################################

    # default locations of the meta data files for mc16a and mc16d, 
    # alternative can be provided via command line argument
    bkgMetaFilePaths= {"mc16a" : "production_20180414_18/md_bkg_datasets_mc16a.txt",
                       "mc16d" : "production_20180414_18/md_bkg_datasets_mc16d.txt"}
    
    # campaigns integrated luminosity,  complete + partial
    lumiMap= { "mc16a" : 36.1029, "mc16d" : 43.5382, "units" : "fb-1"}


    ######################################################
    #Parse Command line options
    ######################################################

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input file")
    parser.add_argument("-c", "--mcCampaign", type=str, help="name of the mc campaign, i.e. mc16a or mc16d", default="mc16a")
    parser.add_argument("-d", "--metaData", type=str, 
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    args = parser.parse_args()

    # open the file with te data from the ZdZdPostProcessing
    postProcessedData = ROOT.TFile(args.input,"READ");

    # define the MC campaign that we are using
    mcCampaign = args.mcCampaign

    # get the default metadata if a custom one has not been specified in the command line arguments
    if args.metaData is None: metaDataFile = bkgMetaFilePaths[mcCampaign]


    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process

    DISDHelper = DSIDHelper()
    DISDHelper.importMetaData(metaDataFile) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data location


    dirsAndContents = getTDirsAndContents(postProcessedData, recursiveCounter = 1)


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


        histsByEnding = splitHistNamesByPlotvariable(analysisHists) # get a mapping like {ending, [hists with that ending], ... }
        # hists with a common ending shall be plotted together
        

        canvasList = []

        for histEnding in histsByEnding.keys():

            # define fill colors, use itertools to cycle through them, access via fillColors.next()
            fillColors = itertools.cycle([ROOT.kBlue,   ROOT.kMagenta,  ROOT.kRed,    ROOT.kYellow,   
                                          ROOT.kGreen,  ROOT.kCyan,     ROOT.kViolet, ROOT.kPink, 
                                          ROOT.kOrange, ROOT.kSpring,    ROOT.kTeal,   ROOT.kAzure]) 

      
            #histEnding = "ZXSR_HiggsMassVeto_M4l"
            #histEnding = "SRHM_Final_M4l"
            #histEnding = "SRHM_Final_avgMll"
            #histEnding = "VR1HM_Final_avgMll"

            backgroundTHStack = ROOT.THStack(histEnding,histEnding)
            #backgroundTHStack.SetMaximum(25.)
            canvas = ROOT.TCanvas(histEnding,histEnding,1280,720);
            legend = setupTLegend()


            gotDataSample = False # change this to true later if we do have data samples

            backgroundSamples = [] # store the background samples as list of tuples [ (DSID, TH1) , ...] 

            for histName in histsByEnding[histEnding]: 
                #print(histName)
                DSID = histName.split("_")[1] # get the DSID from the name of the histogram, which should be like bla_DSID_bla_...
                currentTH1 = TDir.Get(histName).Clone() # get a clone of the histogram, so that we can scale it, without changeing the original

                #currentTH1.GetYaxis().SetRange(0,25);

                
                if int(DSID) > 0: # Signal & Background have DSID > 0
                    currentTH1.SetFillStyle(1001) # 1001 - Solid Fill: https://root.cern.ch/doc/v608/classTAttFill.html
                    currentTH1.SetFillColor(fillColors.next())

                    scale = lumiMap[mcCampaign] * 1000000. * DISDHelper.getProduct_CrossSec_kFactor_genFiltEff(DSID) / sumOfWeights[int(DSID)]

                    #print( DSID, currentTH1.Integral(), scale, currentTH1.Integral()*scale)
                    currentTH1.Scale(scale)

                    backgroundSamples.append( ( int(DSID), currentTH1) )

                    #if int(DSID) == 345047:
                    #    currentTH1.Draw()
                    #    canvas.Update()
                    #    import pdb; pdb.set_trace()

                    #if currentTH1.Integral() < 1. : continue

                    #backgroundTHStack.Add(currentTH1) 
                    #legend.AddEntry(currentTH1 ,histName, "f");
                else:   # data has DSID 0 for us  
                    gotDataSample = True
                    dataTH1 = currentTH1
                    #legend.AddEntry(currentTH1 ,histName)


            #DSIDMappingDict = DISDHelper.physicsSubProcessByDSID
            DSIDMappingDict = DISDHelper.physicsProcessByDSID

            sortedSamples = mergeHistsByMapping(backgroundSamples, DSIDMappingDict)

            
            for key in sortedSamples.keys(): # add merged samples to the backgroundTHStack
                mergedHist = sortedSamples[key]
                backgroundTHStack.Add( mergedHist )
                legend.AddEntry(mergedHist , key , "f");

            backgroundTHStack.Draw("Hist")
            # use the x-axis label from the original plot in the THStack, needs to be called after 'Draw()'
            backgroundTHStack.GetXaxis().SetTitle( mergedHist.GetXaxis().GetTitle() )

            if gotDataSample: # add data samples
                dataTH1.Draw("same")
                legend.AddEntry(currentTH1, "data", "l")

            #backgroundTHStack.GetYaxis().SetRange(0,25);
            legend.Draw();

            canvas.Update() # we need to update the canvas, so that changes to it (like the drawing of a legend get reflected in its status)
            #import pdb; pdb.set_trace()

            canvasList.append( copy.deepcopy(canvas) ) # save a deep copy of the canvas for later use



        # Write the Histograms to a ROOT File
        outoutROOTFile = ROOT.TFile("outHistograms.root","RECREATE")
        counter = 0
        for histogram in canvasList: 
            histogram.Write() # write to the .ROOT file
            counter +=1
            printRootCanvasPDF(histogram, isLastCanvas = histogram==canvasList[-1] , 
                               fileName = "outHistograms.pdf", tableOfContents = str(counter) + " - " + histogram.GetTitle() ) # write to .PDF
        outoutROOTFile.Close()



    print("All plots processed!")
        #import pdb; pdb.set_trace()

