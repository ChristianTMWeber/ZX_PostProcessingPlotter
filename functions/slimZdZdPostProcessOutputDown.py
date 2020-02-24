#####################
# slimZdZdPostProcessOutputDown.py
#
# Small script to slimm the output of a ZdZdPostProcessing run down.
# It removes all the folders and histograms associated with systematics
# and leaves the 'nominal' ones to be saved in an output file.
#
#####################



import ROOT # to do all the ROOT stuff

import re # for using regular expressions
import argparse # to parse command line options

import functions.rootDictAndTDirTools as rootDictAndTDirTools


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    args = parser.parse_args()

    # post_20200219_204021__ZX_Run2_AllReducibles_May.root

    inputFileName = args.input

    inputTFile = ROOT.TFile(inputFileName,"OPEN")

    outputFileName = re.sub(".root", "_slimmed.root",inputFileName)

    outputTFile = ROOT.TFile(outputFileName,"RECREATE")

    for tObj in rootDictAndTDirTools.generateTDirContents(inputTFile): 

        if isinstance( tObj, ROOT.TDirectoryFile): writeSubsetOfTDir(tObj, outputTFile, "Nominal")
        else:
            outputTFile.cd()
            tObj.Write()


    outputTFile.Close()

    print( "\'"+inputFileName + "\' slimmed down and saved to \'" + outputFileName +"\'")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
