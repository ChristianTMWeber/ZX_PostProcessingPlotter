import ROOT # to do all the ROOT stuff
import argparse # to parse command line options
import re
import time # for measuring execution time
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import math


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import plotPostProcess as postProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
import limitSetting.limitFunctions.makeHistDict as makeHistDict # things to fill what I call later the masterHistDict



def getBackgroundYieldVariations( backgroundDict):

    yieldVariationDict = collections.defaultdict(dict)

    for flavor in backgroundDict["Nominal"].keys(): 
    
        nominalYield = backgroundDict["Nominal"][flavor].Integral()
    
        for systematicVariation in backgroundDict: 

            yieldVariationDict[systematicVariation][flavor] = backgroundDict[systematicVariation][flavor].Integral() / nominalYield - 1

    return yieldVariationDict

def getYieldTableEntry(yieldVariationDict , systematic, flavor):

    upVariation = yieldVariationDict[systematic+"1up"][flavor] 
    downVariation = yieldVariationDict[systematic+"1down"][flavor] 

    # convert to percent and round to two digits 
    upVariation   = round(upVariation * 1e4)/1e2
    downVariation = round(downVariation * 1e4)/1e2

    if upVariation == 0  and downVariation == 0 :   textBox = "--"
    elif abs(upVariation) == abs(downVariation): 
        if upVariation >= downVariation :            textBox = "$\\pm %.2f$ " %upVariation
        elif upVariation < downVariation :          textBox = "$\\mp %.2f$ " % abs(upVariation)
    else:                                           textBox = "$\\substack{ %+.2f \\\\ %+.2f }$" %(upVariation , downVariation)

    return textBox


def addTotalVariationYields(yieldDict, systematicNames):

    for flavor in masterHistDict["ZXSR"]["H4l"]["Nominal"].keys():

        totalVariation1Up = 0.
        totalVariation1Down = 0.
        for systeamticName in systematicNames: 
            #                  math.copysign(           use this number                     ,   with the sign of this number              )
            totalVariation1Up   +=  math.copysign(yieldDict[systeamticName + "1up"][flavor]**2  , yieldDict[systeamticName + "1up"][flavor])
            totalVariation1Down +=  math.copysign(yieldDict[systeamticName + "1down"][flavor]**2, yieldDict[systeamticName + "1down"][flavor])

            yieldDict[ "Total_" + "1up"][flavor]   = math.copysign( abs(totalVariation1Up)**0.5, totalVariation1Up)
            yieldDict[ "Total_" + "1down"][flavor] = math.copysign( abs(totalVariation1Down)**0.5, totalVariation1Down)

    return yieldDict


def outputYieldTableForLatex(listOfYieldDicts, outputFileName):

    outputLines = []

    for systeamticName in systematicNames: 

        outputLine = re.sub( "_" , "\\_" ,systeamticName.strip("_"))


        for yieldDict in listOfYieldDicts:
            for flavor in ["4e", "2mu2e" , "2e2mu", "4mu"]:
                outputLine += "\t&"
                outputLine += getYieldTableEntry(yieldDict , systeamticName, flavor)

        outputLine += " \\tabularnewline \hline"

        outputLines.append(outputLine)
    outputLines.append("\hline" )

    outputLine = "Total "
    for yieldDict in listOfYieldDicts:
        for flavor in ["4e", "2mu2e" , "2e2mu", "4mu"]:
            outputLine += "\t&"
            outputLine += getYieldTableEntry(yieldDict , "Total_", flavor)

    outputLine += " \\tabularnewline \hline"
    outputLines.append( outputLine )


        
    for line in outputLines:  print( line )

    outputFile = open( outputFileName, "w")


    for line in outputLines: 
      # write line to output file
      outputFile.write(line ) 
      outputFile.write("\n")
    outputFile.close()

    return None




if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument("--outputTo", type=str, default="yieldTableForLatex.txt" , help="name of the output file" )

    parser.add_argument("-c", "--mcCampaign", type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], default="mc16ade",
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument("-d", "--metaData", type=str, default="../metadata/md_bkg_datasets_mc16e_All.txt" ,
        help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument( "--DSID_Binning", type=str, help = "set how the different DSIDS are combined, ",
        choices=["physicsProcess","physicsSubProcess","DSID","analysisMapping"] , default="analysisMapping" )

    args = parser.parse_args()

    channelMapping = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZZCR"}

    ######################################################
    # do some checks to make sure the command line options have been provided correctly
    ######################################################

    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = postProcess.DSIDHelper()
    myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.setMappingOfChoice( args.DSID_Binning )


    ######################################################
    # Open the attached .root file and loop over all elements over it
    ######################################################
    startTime = time.time()
    postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)

    nRelevantHistsProcessed = 0

    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) 

    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if makeHistDict.skipTObject(path, myTObject, selectChannels = channelMapping.keys() ): continue # skip non-relevant histograms

        #if myTObject.GetBinWidth(1) != 1.0:
        #    if myTObject.GetBinWidth(1) == 0.5: myTObject.Rebin(2)
        #    else: raise ValueError('Bin size is neither 1 nor 0.5. Check the binwidth, and decide which binwidth you want.')


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        if "MUONS_SAGITTA" in path: continue
        if "PMG_" in path: continue
        if "m34" not in path: continue

        masterHistDict = makeHistDict.fillHistDict(path, myTObject , args.mcCampaign, myDSIDHelper, channelMap = channelMapping , masterHistDict = masterHistDict) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    H4lYieldDict = getBackgroundYieldVariations( masterHistDict["ZXSR"]["H4l"] )
    ZZYieldDict  = getBackgroundYieldVariations( masterHistDict["ZXSR"]["ZZ"] )
    signalYieldDict15GeV  = getBackgroundYieldVariations( masterHistDict["ZXSR"]["ZZd, m_{Zd} = 15GeV"] )
    signalYieldDict35GeV  = getBackgroundYieldVariations( masterHistDict["ZXSR"]["ZZd, m_{Zd} = 35GeV"] )
    signalYieldDict55GeV  = getBackgroundYieldVariations( masterHistDict["ZXSR"]["ZZd, m_{Zd} = 55GeV"] )

    systematicNameList = [ re.sub('(1down)|(1up)', '', sysVariation) for sysVariation in H4lYieldDict ] 

    systematicNameSet = set(systematicNameList)
    systematicNameSet.discard("Nominal") # remove the Nominal variation from list

    systematicNames = sorted(list(systematicNameSet))

    backgroundYieldDicts = [H4lYieldDict, ZZYieldDict]
    signalYieldDicts = [signalYieldDict15GeV, signalYieldDict35GeV, signalYieldDict55GeV]

    allYieldDicts = []
    allYieldDicts.extend(backgroundYieldDicts)
    allYieldDicts.extend(signalYieldDicts)



    #   add the total impact of the experimental variations
    for yieldDict in allYieldDicts:    addTotalVariationYields(yieldDict, systematicNames)



    # output the table parts to I can copy them over to the support note
    outputYieldTableForLatex(backgroundYieldDicts, "H4l_and_ZZ_yieldVariationTable.txt")
    outputYieldTableForLatex(signalYieldDicts, "signal_yieldVariationTable_15_35_55Gev.txt")


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
