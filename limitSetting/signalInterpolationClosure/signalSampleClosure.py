import ROOT # to do all the ROOT stuff

import argparse # to parse command line options
import time # for measuring execution time
import re

# import sys and os.path to be able to import functions from parent directory (and parentparent directory)
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.rootDictAndTDirTools as rootDictAndTDirTools
from plotPostProcess import DSIDHelper



sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) )  ) # add also the direct parent directory
import limitFunctions.makeHistDict as makeHistDict
from limitFunctions.visualizeSignalOverview import getMasspointDict
import limitFunctions.RooIntegralMorphWrapper as integralMorphWrapper
import limitFunctions.reportMemUsage as reportMemUsage



def makeInterpolatedSignalSamples(masterHistDict, channels = None, flavors = ["All"]):
    startTimeInterp = time.time()

    if channels is None: channels = masterHistDict.keys()
    elif not isinstance(channels, list):  channels = [channels]

    for channel in channels:
        masspointDict = getMasspointDict(masterHistDict , channel = channel )
        sortedMasses = masspointDict.keys(); 
        sortedMasses.sort()

        # don't forget to loop over all flavors:
        if flavors is None: flavors = masterHistDict[channel][masspointDict.values()[0]]["Nominal"].keys()
        for systematic in masterHistDict[channel][masspointDict.values()[0]].keys():
            #if systematic != "Nominal": continue
            for flavor in flavors:

                for massToInterpolate in sortedMasses[1:-1]:
                    # getInterpolatedHistogram takes not as input a list of tuples [(hist,parameter at which hist is realized),...]
                    # remember to exclude the hist that we want to interpolate at
                    histsAndMasses = [ (masterHistDict[channel][ masspointDict[mass]  ][systematic][flavor], mass) for mass in masspointDict if  mass != massToInterpolate ]

                    # we want to interpolate between lowHist and highHist in 1GeV steps
                    newMass = massToInterpolate#(float(highMass) + float(lowMass))/2
                    # do the actual interpolation                                                                                                       #                             errorInterpolation = simulateErrors,  morph1SigmaHists, or morphErrorsToo
                    #newSignalHist = integralMorphWrapper.getInterpolatedHistogram(lowHist, highHist,  paramA = lowMass , paramB = highMass, interpolateAt = newMass, morphType = "momentMorph", errorInterpolation = "morph1SigmaHists", nSimulationRounds = 10)
                    newSignalHist = integralMorphWrapper.getInterpolatedHistogram(histsAndMasses, interpolateAt = massToInterpolate, errorInterpolation = "morph1SigmaHists" , morphType = "momentMorph", nSimulationRounds = 100)
                    # determine new names and eventType
                    newMass = int(newMass)
                    newEventType = re.sub('\d{2}', str(newMass), masspointDict[massToInterpolate]) # make the new eventType string, by replacing the mass number in a given old one
                    newTH1Name   = re.sub('\d{2}', str(newMass), masterHistDict[channel][ masspointDict[massToInterpolate] ][systematic][flavor].GetName())+"_Interpolated"
                    newSignalHist.SetName(newTH1Name)
                    # add the new histogram to the sample
                    masterHistDict["interpolated"][ newEventType ][systematic][flavor] = newSignalHist

                    print (massToInterpolate,masterHistDict[channel][ masspointDict[massToInterpolate] ][systematic][flavor].Integral(), newSignalHist.Integral() )

                    reportMemUsage.reportMemUsage(startTime = startTimeInterp)

                    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


def getSmallestInterval(myRootHist,desiredWidth = 0.9):
    #if isinstance(myRootHist,ROOT.TH1)

    totalIntegral = myRootHist.Integral();

    nBins = myRootHist.GetNbinsX()

    binInterval = [1, nBins]

    # Let's bruteforce this
    # To determine the smallest intervall that contains a fraction of <desiredWidth> 
    # calculate all possible integrals that contain a fraction of <desiredWidth> of the total integral
    # and select the one where the integral limits are closes together

    for leftIntegralLimit in range(1,nBins): # iterate over the left integral limit
        localIntegral = 0;                   # reset each time the local integral when we start over with the right integral limit
        for rightIntegralLimit in range(leftIntegralLimit,nBins+1): 
            localIntegral = myRootHist.Integral(leftIntegralLimit,rightIntegralLimit); #calculate the integral in the limits
            if localIntegral >= desiredWidth*totalIntegral: 
                # if the integral approaches the desired fraction of the total integral, reset advacne the left integral limit
                # But beforehand check if the limits are closer togehter than our previous limits, and save them if that's the case
                if rightIntegralLimit - leftIntegralLimit < binInterval[1]-binInterval[0]:  binInterval = [leftIntegralLimit, rightIntegralLimit]
                continue

            
    # Get the x-axis values from the bin numbers, and return them
    return  [myRootHist.GetBinLowEdge(binInterval[0]), myRootHist.GetBinLowEdge(binInterval[1]) + myRootHist.GetBinWidth(binInterval[1])]


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.10,0.70,0.60,0.90)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend


def getContiguousSubsetOfHist(histIn, okRange):

    histOut = histIn.Clone( histIn.GetName()+"_subset")

    minX = min(okRange)
    maxX = max(okRange)

    for xBinNr in xrange(0, histOut.GetNbinsX() +1 ):

        xVal = histOut.GetXaxis().GetBinCenter(xBinNr)

        withinLimits = xVal > minX and xVal < maxX

        if not withinLimits: histOut.SetBinContent(xBinNr,0)

    return histOut




if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", "-i", type=str, default="../../post_20190905_233618_ZX_Run2_BckgSignal.root",
        help="name or path to the input files")

    args = parser.parse_args()

    ######################################################
    # Open the attached .root file and loop over all elements over it
    ######################################################
    startTime = time.time()
    postProcessedData = ROOT.TFile(args.input,"READ"); # open the file with te data from the ZdZdPostProcessing

    ######################################################
    # Set up DSID helper
    ######################################################
    # the DSID helper has two main functions
    # 1) administrating the metadata 
    #    i.e. parsing the meta data files and based on them providing a scaling for the MC samples
    # 2) grouping DSIDs into physics categories for the plots
    #    e.g. grouping DSIDs 345060 and 341488 (among others) into one histogram for the "H->ZZ*->4l" process
    myDSIDHelper = DSIDHelper()
    myDSIDHelper.importMetaData("../../metadata/md_bkg_datasets_mc16e_All.txt") # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.setMappingOfChoice( "analysisMapping" )

    myDSIDHelper.fillSumOfEventWeightsDict(postProcessedData)


    # sort hists into a convinient Dict

    nRelevantHistsProcessed = 0

    DSIDList = set()

    for path, myTObject  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(postProcessedData, newOwnership = None):  
        # set newOwnership to 'None' here and let root handle the ownership itself for now, 
        # otherwise we are getting a segmentation fault?!

        if makeHistDict.skipTObject(path, myTObject): continue # skip non-relevant histograms

        if "Nominal" not in path: continue

        DSID = myDSIDHelper.idDSID( path)

        DSIDList.add(DSID)
        if not myDSIDHelper.isSignalSample( DSID ): continue

        myTObject.Rebin(1)

        masterHistDict = makeHistDict.fillHistDict(path, myTObject , "mc16ade", myDSIDHelper ) 

        nRelevantHistsProcessed += 1

        if nRelevantHistsProcessed %100 == 0:  print( path, myTObject)
        #if args.quick and (nRelevantHistsProcessed == 2000): break

    makeInterpolatedSignalSamples(masterHistDict, channels = None, flavors = ["All"])


    signalSampleKeyList = masterHistDict["interpolated"].keys()
    signalSampleKeyList.sort()


    canvasCounter = 0

    canvasName = "0.55Bins_0.05BinsPre_momentMorph_morph1SigmaHists_NonLinear"
    canv = ROOT.TCanvas(canvasName,canvasName, 1080, 1920 )
    canv.Divide(2,4)

    ratioHistList = []
    padList = []

    for signalSampleKey in signalSampleKeyList:         
        #for signalSampleKey in masterHistDict["signalRegion"]:    masterHistDict["signalRegion"][signalSampleKey]["Nominal"][flavor]      

        # Get the relevant hists

        flavor = "All"
        interpHist = masterHistDict["interpolated"][signalSampleKey]["Nominal"][flavor]
        simHist = masterHistDict["signalRegion"][signalSampleKey]["Nominal"][flavor]

        commonRebin = 10
        interpHist.Rebin(commonRebin)
        simHist.Rebin(commonRebin)

        
        # prep the look of the histograms
        interpHist.SetLineColor(2)
        #interpHist.SetMarkerStyle(5)
        

        mass = re.search("\d+",signalSampleKey).group()


        ksResult = simHist.KolmogorovTest(interpHist)
        titleString = "mZd = %i GeV, ksTest = %.3g" %(int(mass), ksResult)
        print(titleString)



        simHist.SetTitle(titleString)
        simHist.SetStats( False)
        #simHist.GetYaxis().SetTitle("#Events ")
        simHist.GetYaxis().SetTitle("Events / " + str(simHist.GetBinWidth(1) )+" GeV" )


        xMin,xMax = getSmallestInterval(simHist, desiredWidth= 0.99)
        simHist.GetXaxis().SetRangeUser(xMin,xMax)


        #simHist.KolmogorovTest(interpHist,"M")

        #simHistShort = getContiguousSubsetOfHist(simHist, [xMin,xMax])
        #interpHistShort = getContiguousSubsetOfHist(interpHist, [xMin,xMax])
        #ksResult = simHistShort.KolmogorovTest(interpHistShort)

        

        #canvasName = "checkInterpolation: mZd = "+str(mass)+"GeV"

        canvasCounter  += 1
        canv.cd(canvasCounter)
        #canv = ROOT.TCanvas(canvasName,canvasName, 700, 700)

        histPadYStart = 3.5/13
        histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
        histPad.Draw();              # Draw the upper pad: pad1
        histPad.cd();                # pad1 becomes the current pad

        padList.append(histPad)




        simHist.Draw()
        interpHist.Draw("same")


        legend = setupTLegend()
        legend.AddEntry(simHist , "MonteCarlo Sample" , "l");
        legend.AddEntry(interpHist , "interpolated histogram" , "l");
        legend.Draw()



        canv.cd(canvasCounter)

        ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);

        ratioPad.SetTopMargin(0.)
        ratioPad.SetBottomMargin(0.3)
        ratioPad.SetGridy(); #ratioPad.SetGridx(); 
        ratioPad.Draw();              # Draw the upper pad: pad1
        ratioPad.cd();   
        padList.append(ratioPad)

        ratioHist = simHist.Clone( simHist.GetName()+"_Clone" )
        ratioHist.Divide(interpHist)

        ratioHistList.append(ratioHist)

        #ratioHist.GetYaxis().SetRangeUser(0, 2)


        ratioHist.SetTitle("")
        
        ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
        ratioHist.GetYaxis().SetLabelSize(0.1)

        ratioHist.GetYaxis().SetTitle("Ratio ")
        ratioHist.GetYaxis().SetTitleSize(0.06)
        ratioHist.GetYaxis().SetTitleOffset(0.8)
        ratioHist.GetYaxis().CenterTitle()

        ratioHist.Draw("P")

        #canv.Update()

        printString = "interpolation closure, mZd = %i GeV" %(int(mass))

        #canv.Print(printString+".png")
        #canv.Print(printString+".pdf")

        #canv.Close()

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    canv.Update()


    canv.Print(canvasName+".png")
    canv.Print(canvasName+".pdf")
    canv.Print(canvasName+".root")



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here





    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here