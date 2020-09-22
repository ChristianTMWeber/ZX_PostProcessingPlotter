import ROOT

import collections
import re
import numpy as np

# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.rootDictAndTDirTools as TDirTools
import functions.histNumpyTools as histNumpyTools
import functions.histHelper as histHelper


def makeReducibleShapeVariationProxy(hist, skewAroundBin = None , leftPartScale = .5):



    if skewAroundBin is None:  

        cumulativeHist = hist.GetCumulative() 

        skewAroundBin = cumulativeHist.FindFirstBinAbove( hist.Integral()/2 ) -1



    rightPartScale = ( hist.Integral() - leftPartScale * hist.Integral(1,skewAroundBin) ) / hist.Integral(skewAroundBin+1,  hist.GetNbinsX() )  

    for binNr in xrange(1,hist.GetNbinsX()+1): 

        if binNr <= skewAroundBin: scale = leftPartScale
        else:                      scale = rightPartScale

        hist.SetBinContent( binNr, hist.GetBinContent(binNr) * scale )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return hist

def makePlot( histList , titleString = "overviewPLot"):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.5; yOffset = 0.4
        xWidth  = 0.4; ywidth = 0.3
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    colors = [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen ]
    lineStyles = [ ROOT.kSolid , ROOT.kDashed, ROOT.kDotted , ROOT.kDashDotted ]  

    canvas = ROOT.TCanvas( titleString, titleString , int(1920 / 2.**0.5) , int(1080 / 2.**0.5)  )

    legend = setupTLegend()

    counter = 0

    histMaxima = [ hist.GetMaximum() for hist in histList ]

    for hist in histList:

        hist.SetTitle(titleString)

        hist.SetLineColor( colors[counter]  )
        hist.SetLineStyle( lineStyles[counter] )
        hist.SetLineWidth( 2 )

        hist.GetYaxis().SetRangeUser( 0 , max( histMaxima ) * 1.1 )

        hist.Draw( "same HIST" )

        legend.AddEntry(hist , hist.GetName() + ", yield = %.2f"%hist.Integral() , "l");

        counter +=1

    legend.Draw()
    canvas.Update()

    canvas.Print(titleString + ".png")
    canvas.Print(titleString + ".pdf")
    canvas.Print(titleString + ".root")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return None


if __name__ == '__main__':


    inputFileName = "post_20200809_203927_ZX_Run2_BckgSignal_PreppedHist_PMGWeights_V4.root"

    myFile = ROOT.TFile(inputFileName, "OPEN")


    masterHistDict = TDirTools.buildDictTreeFromTDir(myFile)

    signalKeyTemplate  = 'ZZd, m_{Zd} = %iGeV'
    expectedDataString = 'expectedData'

    tempMetaDict = collections.defaultdict(lambda: collections.defaultdict(dict))


    ######### inject signal to asimov data


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


    #########  make reducible shape variation proxi   ############



    reducibleUpVariationDict = collections.defaultdict(lambda: collections.defaultdict(dict))
    reducibleDownVariationDict = collections.defaultdict(lambda: collections.defaultdict(dict))



    for flavor in masterHistDict['ZXSR']["reducibleDataDriven"]['Nominal'].keys():

        reducibleOriginal = masterHistDict['ZXSR']["reducibleDataDriven"]['Nominal'][flavor]

        reducibleCopy = reducibleOriginal.Clone( "reducible_nominal")

        reducibleDownShape = reducibleOriginal.Clone(  "reducible_shape_variation_proxy_DOWN" )
        reducibleUpShape = reducibleOriginal.Clone(  "reducible_shape_variation_proxy_UP" )

        reducibleDownShape.Integral()
        reducibleOriginal.Integral()


        makeReducibleShapeVariationProxy(reducibleDownShape , leftPartScale = .5)
        makeReducibleShapeVariationProxy(reducibleUpShape , leftPartScale = 1.5)

        for x in [reducibleCopy, reducibleDownShape , reducibleUpShape ] : print( x.Integral() )


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        if flavor == "All": 
            makePlot( [reducibleCopy, reducibleDownShape , reducibleUpShape ] , titleString = "Reducible shape variation proxi comparison")


        H4l = masterHistDict['ZXSR']["H4l"]['Nominal'][flavor]
        ZZ =  masterHistDict['ZXSR']["ZZ"]['Nominal'][flavor]
        const = masterHistDict['ZXSR']["VVV_Z+ll"]['Nominal'][flavor]

        for redHist in [reducibleCopy, reducibleDownShape , reducibleUpShape ] :

            for otherBackground in [H4l, ZZ, const]: 

                redHist.Add(otherBackground)

        if flavor == "All": 
            makePlot( [reducibleCopy, reducibleDownShape , reducibleUpShape ] , titleString = "Asimov datasets with reducible shape variation proxi comparison")


        reducibleUpVariationDict["Nominal"][flavor] = reducibleUpShape
        reducibleDownVariationDict["Nominal"][flavor] = reducibleDownShape

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    masterHistDict['ZXSR']["asimovData_"+reducibleUpShape.GetName()    ] = reducibleUpVariationDict
    masterHistDict['ZXSR']["asimovData_"+reducibleDownShape.GetName()    ] = reducibleDownVariationDict

    masterHistDict['ZXSR']["reducibleDataDriven"]["reducibleShapeProxy_1up"] = reducibleUpVariationDict["Nominal"]
    masterHistDict['ZXSR']["reducibleDataDriven"]["reducibleShapeProxy_1down"] = reducibleDownVariationDict["Nominal"]

    TDirTools.writeDictTreeToRootFile( masterHistDict, targetFilename = re.sub(".root", "_reducibleShapeVariationProxySystematic.root", inputFileName) )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here