#############################
#   
# python programm to make plotsout of the post processing outputs   
#
#
#
#############################

import ROOT # to do all the ROOT stuff
import numpy as np # good ol' numpy




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

if __name__ == '__main__':

    inputRootFileName = "data15_mc16a.root"

    postProcessedData = ROOT.TFile(inputRootFileName,"READ");

    dirsAndContents = getTDirsAndContents(postProcessedData, recursiveCounter = 1)

    topLevelTObjects = {postProcessedData : dirsAndContents[postProcessedData]}
    del dirsAndContents[postProcessedData]

    for TDir in dirsAndContents.keys():
        HistNames = dirsAndContents[TDir]


        nonCutflowHists = []
        for HistName in HistNames :  
            if "cutflow" in HistName: continue
            if HistName.startswith("h2_"): continue
            if HistName.endswith("Weight"): continue
            nonCutflowHists.append(HistName)
            print(HistName)


        histsByEnding = splitHistNamesByPlotvariable(nonCutflowHists)

        for histEnding in histsByEnding.keys():

            dataTH1 = None 

            backgroundTHStack = ROOT.THStack(histEnding,histEnding)

            for histName in histsByEnding[histEnding]: 
                print(histName)
                DSID = histName.split("_")[1]
                currentTH1 = TDir.Get(histName)
                
                if DSID > 0: backgroundTHStack.Add(currentTH1) # take Data to have DSID 0
                else:        dataTH1 = currentTH1


            import pdb; pdb.set_trace()

        import pdb; pdb.set_trace()











topLevelTObjects = []     # will store the names of the sumOfWeights here
higherLevelTObjects = {}  # will store here directory : [dirContents] here


dirContents=[]





import pdb; pdb.set_trace()