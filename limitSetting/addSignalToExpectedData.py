import ROOT

import collections
import re

# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.rootDictAndTDirTools as TDirTools

inputFileName = "post_20200809_203927_ZX_Run2_BckgSignal_PreppedHist_PMGWeights_V4.root"

myFile = ROOT.TFile(inputFileName, "OPEN")


masterHistDict = TDirTools.buildDictTreeFromTDir(myFile)

signalKeyTemplate  = 'ZZd, m_{Zd} = %iGeV'
expectedDataString = 'expectedData'

tempMetaDict = collections.defaultdict(lambda: collections.defaultdict(dict))


for flavor in masterHistDict['ZXSR']['expectedData']['Nominal'].keys():

    expectedData = masterHistDict['ZXSR'][expectedDataString]['Nominal'][flavor]

    for mass in range(15,56,5):

        signalSample = masterHistDict['ZXSR'][signalKeyTemplate%mass]['Nominal'][flavor]

        newSuffix = "_signal%iGeV" %mass

        dataPlusSignal = signalSample.Clone(expectedData.GetName() + newSuffix)

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        dataPlusSignal.Scale(0.3)

        dataPlusSignal.Add(expectedData)
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        
        #dataPlusSignal.Add(signalSample)

        tempMetaDict[expectedDataString +newSuffix    ]['Nominal'][flavor] = dataPlusSignal

        masterHistDict['ZXSR'][expectedDataString +newSuffix    ] = tempMetaDict[expectedDataString +newSuffix    ]


TDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = re.sub(".root", "_asimovDataWSignals.root", inputFileName) )

#import pdb; pdb.set_trace() # import the debugger and instruct it to stop here