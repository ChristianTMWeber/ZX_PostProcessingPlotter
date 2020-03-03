import ROOT

import re # to do regular expression matching
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import copy # for making deep copies




import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.dirname( path.abspath(__file__) ) ) ) ) # need to append the parent directory here explicitly to be able to import files from parent directories

import plotPostProcess
import functions.rootDictAndTDirTools as rootDictAndTDirTools
import functions.histHelper as histHelper # to help me with histograms


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    TLegend = ROOT.TLegend(0.50,0.65,0.90,0.90)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(2);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    return TLegend



if __name__ == '__main__':

    inputFileName = "Prod_v20_mc16e_Nominal.root"

    inputTFile = ROOT.TFile(inputFileName,"OPEN")

    mcCampaign = "mc16a"

    DSID_Binning = "analysisMapping"

    myDSIDHelper = plotPostProcess.DSIDHelper()

    masterHistDict = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict))) 
    # masterHistDict[ HistEnding ][ mcCampaign ][ DSID ][ ROOT.TH1 ] +

    ownershipSetpoint = False


    for path, baseHist  in rootDictAndTDirTools.generateTDirPathAndContentsRecursive(inputTFile, newOwnership = ownershipSetpoint): 

        if not isinstance(baseHist,ROOT.TH1): continue

        # discern DSID and plotTitle to use them when sorting into a tree structure
        DSID = myDSIDHelper.idDSID(path)

        if int(DSID) not in myDSIDHelper.physicsProcessByDSID: continue
        #if int(DSID) not in myDSIDHelper.analysisMapping["Reducible"]: continue

        baseHist.GetName()

        plotType = re.sub("\d{6}", "",  baseHist.GetName() )

        #masterHistDict = plotPostProcess.fillMasterHistDict2( baseHist, plotType, mcCampaign, DSID, myDSIDHelper )

        masterHistDict[ plotType ][ mcCampaign ][ int(DSID) ] = baseHist

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    combinedMCTagHistDict = masterHistDict

    canvasList = []

    stackDict = {}
    legendDict = {}

    for histEnding in combinedMCTagHistDict.keys():

        backgroundTHStack = ROOT.THStack(histEnding,histEnding)
        backgroundSamples = [] # store the background samples as list of tuples [ (DSID, TH1) , ...] 
        #backgroundTHStack.SetMaximum(25.)
        canvas = ROOT.TCanvas(histEnding,histEnding,1300/2,1300/2);
        ROOT.SetOwnership(canvas, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
        legend = setupTLegend()


        gotDataSample = False # change this to true later if we do have data samples

        assert len( combinedMCTagHistDict[histEnding].keys() ) == 1, "We ended up with more than MC tag after the comining the masterHistDict. That shouldn't be the case"

        for mcTag in combinedMCTagHistDict[histEnding].keys():



            for DSID in combinedMCTagHistDict[histEnding][mcTag].keys():

                    currentTH1 = combinedMCTagHistDict[histEnding][mcTag][DSID]

                    if int(DSID) > 0: # Signal & Background have DSID > 0
                        backgroundSamples.append( ( int(DSID), currentTH1) )
                    else:   # data has DSID 0 for us  
                        gotDataSample = True
                        dataTH1 = currentTH1




            if   DSID_Binning == "physicsProcess" :    DSIDMappingDict = myDSIDHelper.physicsProcessByDSID
            elif DSID_Binning == "physicsSubProcess" : DSIDMappingDict = myDSIDHelper.physicsSubProcessByDSID
            elif DSID_Binning == "analysisMapping" : DSIDMappingDict = myDSIDHelper.analysisMappingByDSID
            elif DSID_Binning == "DSID" : # if we choose to do the DSID_Binning by DSID, we build here a a mapping DSID -> str(DSID)
                DSIDMappingDict = {}
                for aTuple in backgroundSamples: DSIDMappingDict[aTuple[0]] = str( aTuple[0] )  #DSID, histogram = aTuple

            #print(backgroundSamples)
            #import pdb; pdb.set_trace() # import the debugger and instruct
            sortedSamples = plotPostProcess.mergeHistsByMapping(backgroundSamples, DSIDMappingDict)

            myDSIDHelper.colorizeHistsInDict(sortedSamples) # change the fill colors of the hists in a nice way
            statsTexts = []

            statsTexts.append( "#font[72]{ATLAS} internal")
            statsTexts.append( "#sqrt{s} = 13 TeV, %.1f fb^{-1}" %( myDSIDHelper.lumiMap[mcTag] ) ) 

            statsTexts.append( plotPostProcess.addRegionAndChannelToStatsText(canvas.GetName() ) ) 
            statsTexts.append( "  " ) 

            # use these to report the total number of background and signal samples each later on
            backgroundTallyTH1 = sortedSamples.values()[0].Clone( "backgroundTally")
            backgroundTallyTH1.Scale(0)
            signalTallyTH1 = backgroundTallyTH1.Clone("signalTally")

            for key in myDSIDHelper.defineSequenceOfSortedSamples( sortedSamples  ): # add merged samples to the backgroundTHStack 


                mergedHist = sortedSamples[key]

                backgroundTHStack.Add( mergedHist )

                keyProperArrow = re.sub('->', '#rightarrow ', key) # make sure the legend displays the proper kind of arrow
                legend.AddEntry(mergedHist , keyProperArrow , "f");
                statsTexts.append( keyProperArrow + ": %.2f #pm %.2f" %( plotPostProcess.getHistIntegralWithUnertainty(mergedHist)) )

                if myDSIDHelper.isSignalSample( key ): signalTallyTH1.Add(sortedSamples[key])
                else:                                  backgroundTallyTH1.Add(sortedSamples[key])

            # create a pad for the CrystalBall fit + data
            if gotDataSample and not args.skipRatioHist: histPadYStart = 3.5/13
            else:  histPadYStart = 0
            histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
            ROOT.SetOwnership(histPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
            if gotDataSample and not args.skipRatioHist: histPad.SetBottomMargin(0.06); # Seperation between upper and lower plots
            else: histPad.SetBottomMargin(0.12)
            #histPad.SetGridx();          # Vertical grid
            histPad.Draw();              # Draw the upper pad: pad1
            histPad.cd();                # pad1 becomes the current pad

            backgroundTHStack.SetTitle("")

            backgroundTHStack.Draw("Hist")


            backgroundMergedTH1 = histHelper.mergeTHStackHists(backgroundTHStack) # get a merged background to draw uncertainty bars on the total backgroun

            backgroundMergedTH1.Draw("same E2 ")   # "E2" Draw error bars with rectangles:  https://root.cern.ch/doc/v608/classTHistPainter.html
            backgroundMergedTH1.SetMarkerStyle(0 ) # SetMarkerStyle(0 ) remove marker from combined backgroun
            backgroundMergedTH1.SetFillStyle(3244)#(3001) # fill style: https://root.cern.ch/doc/v614/classTAttFill.html#F2
            backgroundMergedTH1.SetFillColor(1)    # black: https://root.cern.ch/doc/v614/classTAttFill.html#F2

            legend.AddEntry(backgroundMergedTH1 , "MC stat. uncertainty" , "f");

            #if "eta"   in backgroundMergedTH1.getTitle: yAxisUnit = ""
            #elif "phi" in backgroundMergedTH1.getTitle: yAxisUnit = " radians"

            backgroundTHStack.GetYaxis().SetTitle("Unweighted Events / " + str(backgroundMergedTH1.GetBinWidth(1) )+" GeV" )
            backgroundTHStack.GetYaxis().SetTitleSize(0.05)
            backgroundTHStack.GetYaxis().SetTitleOffset(0.9)
            backgroundTHStack.GetYaxis().CenterTitle()
            
            #backgroundTHStack.GetXaxis().SetTitleSize(0.12)
            backgroundTHStack.GetXaxis().SetTitleOffset(1.1)

            statsTexts.append( "  " )       
            #statsTexts.append( "Background + Signal: %.2f #pm %.2f" %( plotPostProcess.getHistIntegralWithUnertainty(backgroundMergedTH1)) )
            statsTexts.append( "Background : %.2f #pm %.2f" %( plotPostProcess.getHistIntegralWithUnertainty(backgroundTallyTH1)) )




            # use the x-axis label from the original plot in the THStack, needs to be called after 'Draw()'
            #backgroundTHStack.GetXaxis().SetTitle( mergedHist.GetXaxis().GetTitle() )

            if gotDataSample: # add data samples
                dataTH1.Draw("same")
                #if max(getBinContentsPlusError(dataTH1)) > backgroundTHStack.GetMaximum(): backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)) +1 ) # rescale Y axis limit
                #backgroundTHStack.SetMaximum( max(getBinContentsPlusError(dataTH1)*1.3) )

                legend.AddEntry(currentTH1, "data", "l")

                if dataTH1.Integral >0: statsTexts.append("Data: %.2f #pm %.2f" %( plotPostProcess.getHistIntegralWithUnertainty(dataTH1) ) )  

            # rescale Y-axis
            largestYValue = [max(plotPostProcess.getBinContentsPlusError(backgroundMergedTH1) )]
            if gotDataSample:  largestYValue.append( max( plotPostProcess.getBinContentsPlusError(dataTH1) ) )
            backgroundTHStack.SetMaximum( max(largestYValue) * 1.3 )

            #rescale X-axis
            axRangeLow, axRangeHigh = histHelper.getFirstAndLastNonEmptyBinInHist(backgroundTHStack, offset = 1)
            backgroundTHStack.GetXaxis().SetRange(axRangeLow,axRangeHigh)

            #statsOffset = (0.6,0.55), statsWidths = (0.3,0.32)
            statsTPave=ROOT.TPaveText(0.4,0.40,0.9,0.87,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
            for stats in statsTexts:   statsTPave.AddText(stats);
            statsTPave.Draw();
            legend.Draw(); # do legend things


            canvas.cd()


            canvas.Update() # we need to update the canvas, so that changes to it (like the drawing of a legend get reflected in its status)
            canvasList.append( copy.deepcopy(canvas) ) # save a deep copy of the canvas for later use


            stackDict[histEnding] = backgroundTHStack
            legendDict[histEnding] = legend




    #ZConstrFSRHist = histHelper.mergeTHStackHists( stackDict[histEnding] )

    overviewOutput = ROOT.TFile("OverviewOutput.root", "UPDATE")

    overviewOutput.cd()

    for suffix in ["", "_m4lAll"]:

        uncorrectedHist = stackDict["uncorrectedHist_"+suffix]
        ZConstrFSRHist = stackDict["ZConstrFSRHist_"+suffix]


        if suffix == "": canvasName = "115 GeV < m4l < 130 GeV"
        else:            canvasName = "m4l unconstrained"


        canvas = ROOT.TCanvas(canvasName, canvasName,2560/2, 1080)

        histPadYStart = 3.5/13
        histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
        histPad.Draw();              # Draw the upper pad: pad1
        histPad.cd();                # pad1 becomes the current pad

        uncorrectedHist.SetTitle(canvasName)
        uncorrectedHist.GetXaxis().SetTitle("m_{34} [GeV]")

        uncorrectedHist.Draw("HIST")

        uncorrectedHistMergedTH1 = histHelper.mergeTHStackHists(uncorrectedHist) # get a merged background to draw uncertainty bars on the total backgroun
        ZConstrFSRHistMergedTH1 = histHelper.mergeTHStackHists(ZConstrFSRHist) # get a merged background to draw uncertainty bars on the total backgroun

        #ZConstrFSRHist.Draw("same P")

        ZConstrFSRHistMergedTH1.SetMarkerColor(1)
        ZConstrFSRHistMergedTH1.SetMarkerSize(2)
        ZConstrFSRHistMergedTH1.SetMarkerStyle(33)
        ZConstrFSRHistMergedTH1.Draw("same P HIST")


        legendDict["uncorrectedHist_"+suffix].AddEntry(ZConstrFSRHistMergedTH1 , "FSR recovered and Z constrained" , "p");
        legendDict["uncorrectedHist_"+suffix].Draw()

        #ZConstrFSRHistMergedTH1 = histHelper.mergeTHStackHists(ZConstrFSRHist) # get a merged background to draw uncertainty bars on the total backgroun
        #ZConstrFSRHistMergedTH1.Draw("same P")

        canvas.cd()
        canvas.Update()


        ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);

        ratioPad.SetTopMargin(0.)
        ratioPad.SetBottomMargin(0.3)
        ratioPad.SetGridy(); #ratioPad.SetGridx(); 
        ratioPad.Draw();              # Draw the upper pad: pad1
        ratioPad.cd();                # pad1 becomes the current pad




        ratioHist = ZConstrFSRHistMergedTH1.Clone( ZConstrFSRHistMergedTH1.GetName()+"_Clone" )#ZConstrFSRHist.Clone( ZConstrFSRHist.GetName()+"_Clone" )
        ratioHist.Divide(uncorrectedHistMergedTH1)


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        ratioHist.SetTitle("")

        ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
        ratioHist.GetYaxis().SetLabelSize(0.1)
        
        ratioHist.GetYaxis().SetTitleSize(0.12)
        ratioHist.GetYaxis().SetTitleOffset(0.3)
        ratioHist.GetYaxis().CenterTitle()

        ratioHist.GetXaxis().SetLabelSize(0.12)
        ratioHist.GetXaxis().SetTitleSize(0.13)
        ratioHist.GetXaxis().SetTitleOffset(1.0)
        ratioHist.GetXaxis().SetTitle("m_{34} [GeV]")

        #ratioHist.SetMarkerStyle(8)

        ratioHist.GetYaxis().SetTitle("ratio")
        ratioHist.Draw("P HIST")


        maxRatioVal , _ = histHelper.getMaxBin(ratioHist , useError = False, skipZeroBins = True)
        minRatioVal , _ = histHelper.getMinBin(ratioHist , useError = False, skipZeroBins = True)

        if maxRatioVal is not None: ratioHist.GetYaxis().SetRangeUser(minRatioVal * 0.99, maxRatioVal * 1.01)



        canvas.Update()


        printStr = inputFileName.split(".")[0]+suffix+ ".pdf"

        canvas.Print( printStr )
        canvas.Write()
        canvas.Clear()

    overviewOutput.Close()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here