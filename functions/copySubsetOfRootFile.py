#####################
# copySubsetOfRootFile.py
#
# Small script to copy a parts of a .root file into another
# Uses regular expressions to select / veta that gets copied
# 
#
#####################



import ROOT # to do all the ROOT stuff

import re # for using regular expressions
import argparse # to parse command line options

import rootDictAndTDirTools as rootDictAndTDirTools

from  collections import defaultdict

import os.path


def writeSubsetOfTDir(parentTDir, outputTFile, tDirNamesToWrite = "Nominal"):

    parentName = parentTDir.GetName()


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    if not isinstance(tDirNamesToWrite, list): tDirNamesToWrite = [tDirNamesToWrite]

    #[x.GetName() for x in rootDictAndTDirTools.generateTDirContents(inputTFile) if isinstance(x, ROOT.TDirectoryFile) ]

    #listOfTDirNamesInParentTDir = [x.GetName() for x in rootDictAndTDirTools.generateTDirContents(parentTDir) if isinstance(x, ROOT.TDirectoryFile) ]

    #tDirsNamesWeWillWriteOut = set(listOfTDirNamesInParentTDir) & set(tDirNamesToWrite)

    listOfObjectsToWrite = [x for x in rootDictAndTDirTools.generateTDirContents(parentTDir) if  ( x.GetName() in tDirNamesToWrite)]

    if len(listOfObjectsToWrite) > 0: 
        outputParentTDir = outputTFile.mkdir( parentTDir.GetName() )
        outputParentTDir.cd()


    for tObj in listOfObjectsToWrite: 
    
        if isinstance(tObj, ROOT.TDirectoryFile): 
            outputSubDir = outputParentTDir.mkdir(tObj.GetName())
            outputSubDir.cd()

            tObj.ReadAll()
            tObj.GetList().Write()

            outputParentTDir.cd()

        else: tObj.Write()


    return None


def prepOutputTFile_and_TDir_structure( outputFileName , outputDict ):

    TDirList  = sorted(list(set(outputDict.keys())))

    if None in TDirList: TDirList.remove(None)

    outputTFile = ROOT.TFile(outputFileName,"RECREATE")

    outputTFile.cd()

    for TDir in TDirList: outputTFile.mkdir(TDir)

    return outputTFile


def writeTObjectsToOutput(outputTFile, outputDict):


    for path in outputDict:

        if path is None: outputTFile.cd()
        else:            outputTFile.cd(path)

        for TObject in outputDict[path]: TObject.Write()

    outputTFile.cd()

    outputTFile.Close()


    return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input",    type=str, help="name or path to the input file")
    parser.add_argument("--output", type=str, help="name of the output file", default=None)
    parser.add_argument("--tag",   type=str, default=None, 
        help="Regular expression patter. Checked against the full TDir path + TObject name. \
        If there is a regex match, we will copy the TObject and the TDir structure to the output file\
        If there is also a 'veto' specified, the tag has to match, and the veto has to fail to give a regex match\
        to copy the TObject to the output file")
    parser.add_argument("--veto",  type=str, default=None, 
        help="Regular expression patter. Checked against the full TDir path + TObject name. \
        If there is a regex match, we will _not_ copy the TObject and the TDir structure to the output file\
        If there is also a 'tag' specified, the tag has to match, and the veto has to fail to give a regex match\
        to copy the TObject to the output file")

    args = parser.parse_args()

    if args.output is None: outputFileName = re.sub(".root", "_slimmed.root", os.path.abspath(args.input))
    else:                   outputFileName = args.output

    inputTFile = ROOT.TFile(args.input,"READ")

    counter = 0

    TDirPath_to_TOjectDict = defaultdict(list)

    for TDirPathWithObjectName, TObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive( inputTFile , newOwnership = None, maxRecursionDepth = -1) :        

        if isinstance(TObject, ROOT.TDirectoryFile): continue

        if args.tag is None: tagMatch = True
        else: tagMatch = re.search(args.tag,TDirPathWithObjectName)

        if args.veto is None: vetoMatch = False
        else: vetoMatch = re.search(args.veto,TDirPathWithObjectName)


        #TDirPathWithObjectName=re.sub("343234","999999",TDirPathWithObjectName)
        #TObjectName = TObject.GetName()
        #TObjectName=re.sub("343234","999999",TObjectName)
        #TObject.SetName(TObjectName)

        if tagMatch and not vetoMatch: 

            # consider the look behind and look ahead patterns
            TPathMatch = re.search("(?<=/).*(?=/)",TDirPathWithObjectName)

            if TPathMatch is None: TDirPath = None
            else:                  TDirPath = TPathMatch.group()

            TDirPath_to_TOjectDict[TDirPath].append(TObject)
        

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    outputTFile = prepOutputTFile_and_TDir_structure( outputFileName , TDirPath_to_TOjectDict )

    writeTObjectsToOutput(outputTFile, TDirPath_to_TOjectDict)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    ## post_20200219_204021__ZX_Run2_AllReducibles_May.root
    #inputFileName = args.input
    #inputTFile = ROOT.TFile(inputFileName,"OPEN")
    #outputFileName = re.sub(".root", "_slimmed.root",inputFileName)
    #outputTFile = ROOT.TFile(outputFileName,"RECREATE")
    #for tObj in rootDictAndTDirTools.generateTDirContents(inputTFile): 
    #    if isinstance( tObj, ROOT.TDirectoryFile): writeSubsetOfTDir(tObj, outputTFile, "Nominal")
    #    else:
    #        outputTFile.cd()
    #        tObj.Write()
    #outputTFile.Close()
    print( "\'"+args.input + "\' slimmed down and saved to \'" + outputFileName +"\'")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

