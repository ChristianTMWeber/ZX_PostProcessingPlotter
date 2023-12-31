import ROOT

##################################################
# Functions to traverse TDirs and select TObjects
##################################################

def TDirToList(TDir): # return the contents of a TDir as a list
    outputList = []
    for TKey in TDir.GetListOfKeys(): outputList.append( TKey.ReadObj() ) # this is how I access the element that belongs to the current TKey
    return outputList

def getTDirContentNames(TDir): return [tObj.GetName() for tObj in TDirToList(TDir)] 

def generateTDirContents(TDir):
    # this is a python generator 
    # this one allows me to loop over all of the contents in a given ROOT TDir with a for loop

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    for TKey in TDirKeys: 
        yield TKey.ReadObj() # this is how I access the element that belongs to the current TKey


def generateTDirPathAndContentsRecursive(TDir, baseString = "" , newOwnership = None, maxRecursionDepth = -1):
    # for a given TDirectory (remember that a TFile is also a TDirectory) get all non-directory objects
    # redturns a tuple ('rootFolderPath', TObject) and is a generator

    if isinstance(TDir, list): 

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        for listElement in TDir: 
            for recursiveTObject in generateTDirPathAndContentsRecursive(listElement, baseString = baseString, newOwnership = newOwnership, maxRecursionDepth = maxRecursionDepth):
                yield recursiveTObject

    else: 

        #baseString += TDir.GetName() +"/"

        for TObject in generateTDirContents(TDir):

            
            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            if newOwnership is not None: ROOT.SetOwnership(TObject, newOwnership) # do this to prevent an std::bad_alloc error, setting it to to 'True' gives permission to delete it, https://root.cern.ch/root/htmldoc/guides/users-guide/ObjectOwnership.html
            if isinstance(TObject, ROOT.TDirectoryFile ) and maxRecursionDepth != 0:

                for recursiveTObject in generateTDirPathAndContentsRecursive(TObject, baseString = baseString +"/"+ TObject.GetName() , newOwnership = newOwnership, maxRecursionDepth = maxRecursionDepth -1):
                    yield recursiveTObject

            else :
                yield baseString +"/"+  TObject.GetName() , TObject

def makeListOfTDirAndTObjects(inputTFile):

    outputList = []

    for path, tObject in generateTDirPathAndContentsRecursive(inputTFile):

        pathComponents = path.split("/")

        if len(pathComponents) >=4 : newPath = pathComponents[1:-1]
        elif len(pathComponents) == 3: newPath = pathComponents[1]
        else:   newPath = ""

        outputList.append( (newPath,tObject))

    return outputList

def getSubTDirList( currentTDir) : # provides a list of subdirectories in the current TDirectory
    listOfSubdirectories = [TObject.GetName() for TObject in generateTDirContents(currentTDir) if isinstance(TObject, ROOT.TDirectoryFile)]
    return listOfSubdirectories


def buildDictTreeFromTDir(TDir, newOwnership = None):
    outputDict = {}
    #def expandDict(aDict, keyList):
    #    addToEndOfDict(aDict, keyList, None)
    #    return None

    def addToEndOfDict(aDict, keyList, thingToInsert):
        if len(keyList) > 1:
            if keyList[0] not in aDict: aDict[keyList[0]] = {}
            addToEndOfDict(aDict[keyList[0]], keyList[1:], thingToInsert )
        else: 
            aDict[keyList[0]]=thingToInsert
        return None
    # def addToEndOfDict(aDict, keyList, thingToInsert):

    for path, TObject in generateTDirPathAndContentsRecursive(TDir, baseString = "" , newOwnership = newOwnership):
        truncatedPath = path.split("/")[1:-1] # split into dir names and remove the first entry, i.e. the name of the TDir/Tfile, and the last one, i.e. the TObject name
        addToEndOfDict(outputDict, truncatedPath, TObject )         

    return outputDict


###################################################################
# Functions to convert tree like nested dicts into TDir hierarchies
###################################################################


def writeDictTreeToRootFile( aDict, targetFilename = "dictTree.root" ):
    # use this function with the 'convertDictTree' one to map a tree like nested dict structure to
    # a tree like nested TDir one

        outoutROOTFile = ROOT.TFile( targetFilename, "RECREATE")
        convertDictTree( aDict, outoutROOTFile )
        outoutROOTFile.Close()

        print( "Nested dict written to: " +  targetFilename)

        return None


def convertDictTree( aDict, TDir ):
    # let's say I have a nested dict structure that resemebles a tree like structue 
    # with ROOT TH1s or other TObjects at the end
    # this function creates a structure of TDirs that maintains that hirarchy 
    # and since a TFile is also a TDir, we can save that structure to disk

    # recursively call this function, creating and switching TDirs that are names as the keys of dict
    if isinstance( aDict, dict): 

        existingSubdirectories = getSubTDirList(TDir) # get list of existing TDirs to check against
        for key in aDict: 

            if key not in existingSubdirectories: TDir.mkdir(key) # create a TDirectory if it is not already in existence
            subTDir = TDir.Get(key)
            convertDictTree( aDict[key], subTDir ) # call this function again, but not with the current subdirectory as the new directory etc.

    elif isinstance( aDict, list ):

        for element in aDict: convertDictTree( element, TDir ) # don't switch the TDir if we ended up with a list

    elif isinstance( aDict, ROOT.TObject ): # if ended up with a TObject, we write it to the TFile
        TDir.cd()
        aDict.Write()

    return None

###################################################################
# Other functions to make root objects more accessible
###################################################################

def rooArgSetToList( aRooArgSet ): # turn a RooArgSet into a python list
    outputList = []
    iter = aRooArgSet.createIterator()
    tObj = iter.Next();             
    while tObj: 
        outputList.append(tObj)
        tObj = iter.Next(); 
    return outputList

def getElementFromRooArgSetByName( targetName, aRooArgSet ):
    for element in rooArgSetToList( aRooArgSet ):
        if targetName == element.GetName(): return element
    return None


if __name__ == '__main__':

    # let's make up a nested DICT structure that carries Histograms, 
    # turn that nested dict structure into a root TDir hirarchy, import it and check if it has the structure we expect


    # create the nested dict structure
    import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly

    testDict = collections.defaultdict(lambda: collections.defaultdict(dict)) 

    testDict["A1"]["B1"] = ROOT.TH1D("Test_B1","Test_B2",10,0,10)
    testDict["A1"]["B2"] = ROOT.TH1D("Test_B2","Test_B2",10,0,10)
    testDict["A2"] = ROOT.TH1D("Test_A2","Test_A2",10,0,10)


    # use our functions to write it to disc
    tFileName = "testDictToRoot.root"
    writeDictTreeToRootFile(testDict, targetFilename = tFileName)


    # open it and check the file contents
    testTFile = ROOT.TFile(tFileName, "OPEN")

    fileContents = []

    for path, tObject in generateTDirPathAndContentsRecursive(testTFile): fileContents.append( path  )


    # the contents that we expect
    expectedFileContents = [    tFileName + "/A1/B1/Test_B1",
                                tFileName + "/A1/B2/Test_B2",
                                tFileName + "/A2/Test_A2" ]

    # check if our expectation is born out
    assert set(expectedFileContents) == set(fileContents)

    # delete the file we created
    import os
    os.remove(tFileName)

    print( "All good!" )
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here




