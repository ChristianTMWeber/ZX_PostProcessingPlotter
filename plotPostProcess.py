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


def binStringListByEnding(listOfStrings, endingStr):
    # sorts a list of strings into two other lists, by asking for each of the strings
    # if it ends with the desired ending string
    hasCorrectEnding = []
    hasWrongEnding = []

    for string in listOfStrings:
        if string.endswith(endingStr): hasCorrectEnding.append(string)
        else:                       hasWrongEnding.append(string)

    return hasCorrectEnding, hasWrongEnding

def splitHistNamesByPlotvariable(histNameList, delimeter = "_", nonEndingStringParts = 2): 
    # we wanna group the hist names together that shall be plotted together
    # we we are doing that by grouping them together by the endings
    # by default we take the strings to be splittable by the delimeter "_"
    # and that only the first two parts of the string are not part of the ending

    histsByPlotVariable = {}

    while(histNameList): # while that list is not empty
        
        histNameParts = histNameList[0].split(delimeter)
        currentEnding = delimeter.join(histNameParts[nonEndingStringParts:]) # by conventoin we take the first part of the hist name to be an indicator of the type of object, and the second part the DSID

        currentHists, histNameList = binStringListByEnding(histNameList, currentEnding)

        histsByPlotVariable[currentEnding] = currentHists

    return histsByPlotVariable

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

def importMetaData(metadataFileLocation):
    # parse the metada data from a metadata text file that we furnish
    # we expect the metadata file to have the stucture:
    # <DSID> <crossSection> <kFactor> <genFiltEff>   <...>
    # There the different values are seperate by whitespace
    # We ignore lines that do not start with a DSID (i.e. a 6 digit number)

    metaDataDict = {}
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

    return metaDataDict

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

if __name__ == '__main__':

    #activateATLASPlotStyle() 

    campaign = "mc16a"

    bkgMetaFilePaths= {"mc16a" : "production_20180414_18/md_bkg_datasets_mc16a.txt",
                       "mc16d" : "production_20180414_18/md_bkg_datasets_mc16d.txt"}

    lumiMap= { "mc16a" : 36.1029, "mc16d" : 43.5382, "units" : "fb-1"}  # campaigns integrated luminosity,  complete + partial




    metdataMC16a = importMetaData(bkgMetaFilePaths["mc16a"])


    inputRootFileName = "data15_mc16a.root"

    postProcessedData = ROOT.TFile(inputRootFileName,"READ");

    dirsAndContents = getTDirsAndContents(postProcessedData, recursiveCounter = 1)

    topLevelTObjects = {postProcessedData : dirsAndContents[postProcessedData]}
    del dirsAndContents[postProcessedData] # remove the top level entries, they are only ought to contain the sumOfWeights

    sumOfWeights = getSumOfWeigts(topLevelTObjects)

    

    for TDir in dirsAndContents.keys():
        histNames = dirsAndContents[TDir]

        nonCutflowHists = []
        for histName in histNames :  
            if "cutflow" in histName: continue
            if histName.startswith("h2_"): continue
            if histName.endswith("Weight"): continue
            nonCutflowHists.append(histName)
            print(histName)


        histsByEnding = splitHistNamesByPlotvariable(nonCutflowHists)

        for histEnding in histsByEnding.keys():

            dataTH1 = None 

            backgroundTHStack = ROOT.THStack(histEnding,histEnding)
            

            # define fill colors, use itertools to cycle through them, access via fillColors.next()
            fillColors = itertools.cycle([ROOT.kBlue,   ROOT.kMagenta,  ROOT.kRed,    ROOT.kYellow,   
                                          ROOT.kGreen,  ROOT.kCyan,     ROOT.kViolet, ROOT.kPink, 
                                          ROOT.kOrange, ROOT.kSpring,    ROOT.kTeal,   ROOT.kAzure]) 






            canvas = ROOT.TCanvas(histEnding,histEnding,1280,720);
            legend = setupTLegend()

            for histName in histsByEnding[histEnding]: 
                print(histName)
                DSID = histName.split("_")[1]
                currentTH1 = TDir.Get(histName)


                
                if int(DSID) > 0: # Signal & Background have DSID > 0
                    currentTH1.SetFillStyle(1001) # 1001 - Solid Fill: https://root.cern.ch/doc/v608/classTAttFill.html
                    currentTH1.SetFillColor(fillColors.next())

                    
                    scale = lumiMap[campaign] * 1000000. * metdataMC16a[int(DSID)]["crossSection"] * metdataMC16a[int(DSID)]["kFactor"] * metdataMC16a[int(DSID)]["genFiltEff"] / sumOfWeights[int(DSID)]
                    currentTH1.Scale(scale)
                    backgroundTHStack.Add(currentTH1) 
                    legend.AddEntry(currentTH1 ,histName, "f");
                else:   # data has DSID 0 for us  
                    dataTH1 = currentTH1
                    legend.AddEntry(currentTH1 ,histName)
                    




            backgroundTHStack.Draw("Hist")
            dataTH1.Draw("same")
            legend.Draw();


            canvas.Update() # we need to update the canvas, so that changes to it (like the drawing of a legend get reflected in its status)
            import pdb; pdb.set_trace()


        import pdb; pdb.set_trace()





currentTH1.SetFillStyle(3004)
currentTH1.SetFillColor(ROOT.kBlue+1)




topLevelTObjects = []     # will store the names of the sumOfWeights here
higherLevelTObjects = {}  # will store here directory : [dirContents] here


dirContents=[]





import pdb; pdb.set_trace()