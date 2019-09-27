# let's try some limit setting with the output from limitSettingHistPrep.py

# for a start we will follow this tutorial
# http://ghl.web.cern.ch/ghl/html/HistFactoryDoc.html
# and then expand on it


import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import difflib # so I can be a bit lazier with identification of signal region masspoints via 'difflib.get_close_matches'
import warnings # to warn about things that might not have gone right
import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
import time # for measuring execution time
import datetime # to convert seconds to hours:minutes:seconds
import argparse # to parse command line options
import os # to check existence of directories for example

from limitFunctions.listsToTTree import fillTTreeWithDictOfList # concert of dict of lists into a TTree
import limitFunctions.sampleTH1FromTH1 as sampleTH1FromTH1 # generate a new TH1 from a given one, each bin is taken from a poission distribution


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.rootDictAndTDirTools as TDirTools
import plotPostProcess as postProcess
import functions.histHelper as histHelper
import functions.tGraphHelpers as graphHelper


def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None


def drawNominalHists(inputFileName, drawDict, myDrawDSIDHelper = postProcess.DSIDHelper(), writeToFile = False ):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.6; yOffset = 0.5
        xWidth  = 0.3; ywidth = 0.4
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    def scaleByRooRealVar(hist, aRooRealVar):
        factor = aRooRealVar.getVal()
        error  = aRooRealVar.getError()

        hist.Scale(factor)
        for x in xrange(1,hist.GetNbinsX()+1): 
            oldBinError = hist.GetBinError(x)
            newBinError = oldBinError*(factor + error) / factor  # hist.Scale( ) scalesthe bin contents as well as the error. So we have to do it this way
            hist.SetBinError(x, newBinError )
        return None

    nominalHistStack = ROOT.THStack("nominalStack","nominalStack")

    if isinstance(drawDict,list): drawDict = { x: None for x in drawDict }

    legend = setupTLegend()

    

    histDict={}

    sortedDrawKeys = drawDict.keys()
    sortedDrawKeys.sort()

    for histPath in sortedDrawKeys:

        histogram = inputTFile.Get(histPath)
        currentTH1 = histogram.Clone()
        eventType = histPath.split("/")[1]

        scaleString = ""

        if  "data" in histPath.lower() : # make all characters lowercase to avoid missing "Data" or so
            dataHist = currentTH1
            #dataHist.SetLineWidth(1)
            #dataHist.SetLineColor(1)
        else:
            if isinstance(drawDict[histPath], ROOT.RooRealVar): # do scaling if we send a RooRealVar along with the histogram path
                fittedRooReal = drawDict[histPath]
                scaleByRooRealVar(currentTH1, fittedRooReal)
                scaleString = ", scaled by %.2f #pm %.2f" %( fittedRooReal.getVal(), fittedRooReal.getError() )
            elif isinstance(drawDict[histPath],ROOT.RooStats.LikelihoodInterval): # do scaling if we send a ROOT.RooStats.LikelihoodInterval along with the histogram path
                interval = drawDict[histPath]
                intervalVariables = {x.GetName() : x for x in TDirTools.rooArgSetToList(interval.GetParameters())}

                upperLimit = interval.UpperLimit(intervalVariables["SigXsecOverSM"])
                currentTH1.Scale(upperLimit)
                scaleString = ", #sigma = %.2f fb" %( upperLimit )

            elif isinstance(drawDict[histPath],float): # do scaling if we send a ROOT.RooStats.LikelihoodInterval along with the histogram path
                factor = drawDict[histPath]
                currentTH1.Scale(factor)
                scaleString = ", XS scaled by %.2f" %( factor )




            #currentTH1.SetBinError(12,1)
            #currentTH1.GetBinError(12)  
            currentTH1.SetMarkerStyle(0 ) # SetMarkerStyle(0 ) remove marker from combined backgroun
            nominalHistStack.Add(currentTH1)
            histDict[eventType] = currentTH1

        legend.AddEntry(currentTH1 , eventType + scaleString  , "f");

        #TDirTools.generateTDirContents(inputTFile.Get(histPath))
   
    myDrawDSIDHelper.colorizeHistsInDict(histDict) # sets fill color to solid and pics consistent color scheme
    
    # prepare the canvas and histpad for the histograms, we'll have another for the ratio TPad
    canvas = ROOT.TCanvas("overviewCanvas","overviewCanvas",1300/2,1300/2);

    histPadYStart = 3./13
    histPad = ROOT.TPad("histPad", "histPad", 0, histPadYStart, 1, 1);
    #histPad.SetBottomMargin(0.06); # Seperation between upper and lower plots
    histPad.Draw();              # Draw the upper pad: pad1
    histPad.cd();                # pad1 becomes the current pad

    # prepare scaling of the x axis
    axRangeLow, axRangeHigh = histHelper.getFirstAndLastNonEmptyBinInHist(nominalHistStack, offset = 1)

    # draw the 'regular' histograms
    dataHist.GetXaxis().SetRange(axRangeLow,axRangeHigh) # let's scale the first histogram we draw
    dataHist.Draw()

    dataHist.GetYaxis().SetTitle("Events / " + str(dataHist.GetBinWidth(1) )+" GeV" )
    dataHist.GetYaxis().SetTitleSize(0.05)
    dataHist.GetYaxis().SetTitleOffset(1.0)
    dataHist.GetYaxis().CenterTitle()

    nominalHistStack.Draw("Hist same")
    nominalHistStack.Draw("same E2 ")   # "E2" Draw error bars with rectangles:  https://root.cern.ch/doc/v608/classTHistPainter.html
    dataHist.Draw("same E1")
    legend.Draw(); # do legend things

    canvas.cd()
    
    # setup and draw the ratio pad
    ratioPad = ROOT.TPad("ratioPad", "ratioPad", 0, 0, 1, histPadYStart);
    ROOT.SetOwnership(ratioPad, False) # Do this to prevent a segfault: https://sft.its.cern.ch/jira/browse/ROOT-9042
    #ratioPad.SetTopMargin(0.)
    ratioPad.SetBottomMargin(0.3)
    ratioPad.SetGridy(); #ratioPad.SetGridx(); 
    ratioPad.Draw();              # Draw the upper pad: pad1
    ratioPad.cd();                # pad1 becomes the current pad

    ratioHist = dataHist.Clone( dataHist.GetName()+"_Clone" )
    backgroundMergedTH1 = histHelper.mergeTHStackHists(nominalHistStack) # get a merged background to draw uncertainty bars on the total backgroun
    ratioHist.Divide(backgroundMergedTH1)
    #ratioHist.GetXaxis().SetRange(axRangeLow, axRangeHigh)
    ratioHist.SetStats( False) # remove stats box
    
    ratioHist.SetTitle("")
    
    ratioHist.GetYaxis().SetNdivisions( 506, True)  # XYY x minor divisions YY major ones, optimizing around these values = TRUE
    ratioHist.GetYaxis().SetLabelSize(0.1)

    ratioHist.GetYaxis().SetTitle("Data / MC")
    ratioHist.GetYaxis().SetTitleSize(0.13)
    ratioHist.GetYaxis().SetTitleOffset(0.4)
    ratioHist.GetYaxis().CenterTitle()

    ratioHist.GetXaxis().SetLabelSize(0.12)
    ratioHist.GetXaxis().SetTitleSize(0.12)
    ratioHist.GetXaxis().SetTitleOffset(1.0)
    ratioHist.Draw()

    canvas.Update()
    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    if writeToFile:
        canvas.Write()
        canvas.Print("overview.pdf")
    canvas.Close()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None

def makeGraphOverview( extractedLimit,  expectedLimit1Sig, expectedLimit2Sig , colorScheme = ROOT.kRed, writeTo = False):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.6; yOffset = 0.7
        xWidth  = 0.3; ywidth = 0.2
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    canv = ROOT.TCanvas("GraphOverview", "GraphOverview")
 

    expectedLimit2Sig.GetYaxis().SetTitle("95% CL on #sigma_{ZZ_{d}} [fb] ")
    expectedLimit2Sig.GetYaxis().SetTitleSize(0.06)
    expectedLimit2Sig.GetYaxis().SetTitleOffset(0.6)
    expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetXaxis().SetTitleOffset(0.85)
    #expectedLimit2Sig.GetXaxis().CenterTitle()

    expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
    #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit2Sig.Draw("A3") # use 'A' option only for first TGraph apparently

    #expectedLimit1Sig.SetFillColorAlpha(ROOT.kRed+1,0.5) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
    expectedLimit1Sig.SetFillColor(colorScheme-9)
    #expectedLimit1Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit1Sig.Draw("3 same")

    expectedLimitMedian = graphHelper.getTGraphWithoutError( expectedLimit1Sig  , ySetpoint = "median")

    expectedLimitMedian.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    expectedLimitMedian.SetLineWidth(2)
    expectedLimitMedian.SetLineColor(colorScheme)
    expectedLimitMedian.Draw("same")

    extractedLimit.SetLineStyle(1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    extractedLimit.SetLineWidth(2)
    extractedLimit.SetLineColor(colorScheme)
    extractedLimit.Draw("same")

    legend = setupTLegend()
    legend.AddEntry(extractedLimit , "observed Limit"  , "l");
    legend.AddEntry(expectedLimitMedian , "expected limit"  , "l");
    legend.AddEntry(expectedLimit1Sig , "#pm1#sigma expected limit"  , "f");
    legend.AddEntry(expectedLimit2Sig , "#pm2#sigma expected limit"  , "f");    

    legend.Draw()

    canv.Update() #"a3" also seems to work https://root.cern/doc/master/classTGraphPainter

    if writeTo: writeTo.cd(); canv.Write()

    return canv

def prepHistoSys(eventDict, flavor = "All"):

    #### Get all the systematics by name ####
    systematicNames = set()

    for key in eventDict:
        if key == "Nominal": continue # nominal is not a systematic
        aSystematic = re.search("(?:(?!(1down|1up)).)*", key).group()  # systematics ends with 1up or 1down, find the string parts beforehand
        systematicNames.add(aSystematic)

    #### build 'HystoSys' objects for each systematic ####
    allTheHistoSys = []

    for systematicsName in systematicNames:
        aHistoSys = ROOT.RooStats.HistFactory.HistoSys( systematicsName.strip("_") ) # use strip here to remove trailing underscores

        downVariation = eventDict[systematicsName + "1down"][flavor]
        upVariation   = eventDict[systematicsName + "1up"][flavor]

        aHistoSys.SetHistoHigh( downVariation )
        aHistoSys.SetHistoLow( upVariation )

        allTheHistoSys.append(aHistoSys)

    #import pdb; pdb.set_trace() # import the debugger and

    allTheHistoSys.sort( key = lambda x:x.GetName()) # i.e. we are

    return allTheHistoSys

def prepMeasurement( templatePaths, region, flavor, inputFileName, inputTFile):


    ### Create the measurement object ### This is the top node of the structure  ### We do some minor configuration as well
    meas = ROOT.RooStats.HistFactory.Measurement("ZXMeasurement", "ZXMeasurement")

    ### Set the prefix that will appear before all output for this measurement We Set ExportOnly to false, meaning we will fit the measurement and make  plots in addition to saving the workspace
    meas.SetOutputFilePrefix("./testHistfactoryOutput/")
    meas.SetExportOnly(False)

    ### Set the name of the parameter of interest Note that this parameter hasn't yet been created, we are anticipating it
    meas.SetPOI("SigXsecOverSM")

    meas.AddConstantParam("Lumi")           # this is not part of the C++ exsample
    meas.AddConstantParam("alpha_syst1")    # this is not part of the C++ exsample

    ### Set the luminosity There are a few conventions for this. Here, we assume that all histograms have already been scaled by luminosity We also set a 10% uncertainty
    meas.SetLumi(1.0)
    #meas.SetLumiRelErr(0.10)

    # Create a channel

    ### Okay, now that we've configured the measurement, we'll start building the tree. We begin by creating the first channel
    chan = ROOT.RooStats.HistFactory.Channel("signalRegion")
    ### First, we set the 'data' for this channel The data is a histogram represeting the measured distribution.  It can have 1 or many bins. In this example, we assume that the data histogram is already made and saved in a ROOT file.   So, to 'set the data', we give this channel the path to that ROOT file and the name of the data histogram in that root file The arguments are: SetData(HistogramName, HistogramFile)
    chan.SetData(templatePaths["Data"] )   # <- this seems to work, everything seems to run ok, but the programm completeres with a segmentation violation.
    #chan.SetData(templatePaths["Data"], inputFileName) # <- this one compleres without a segmentation vialation. Switch to this one if necessary
    
    chan.SetStatErrorConfig(0.05, "Poisson") # ??? # this seems to be not part of the C++ exsample

    # Now, create some samples

    # Create the signal sample Now that we have a channel and have attached data to it, we will start creating our Samples These describe the various processes that we use to model the data. Here, they just consist of a signal process and a single background process.
    signal = ROOT.RooStats.HistFactory.Sample("signal", templatePaths["Signal"], inputFileName)
    ### Having created this sample, we configure it First, we add the cross-section scaling parameter that we call SigXsecOverSM Then, we add a systematic with a 5% uncertainty Finally, we add it to our channel
    #signal.AddOverallSys("syst1",  0.1, 1.9) # ??? # review what does this exactly do
    signal.AddNormFactor("SigXsecOverSM", 0, 0, 10)
    chan.AddSample(signal)

    # ZZ background
    ### We do a similar thing for our background
    backgroundZZ = ROOT.RooStats.HistFactory.Sample("backgroundZZ", templatePaths["ZZ"], inputFileName)
    #backgroundZZ.ActivateStatError()#ActivateStatError("backgroundZZ_statUncert", inputFileName)
    #backgroundZZ.AddOverallSys("syst2", 0.95, 1.05 )
    #backgroundZZ.AddNormFactor("ZZNorm", 1, 0, 3) # let's add this to fit the normalization of the background
    addSystematicsToSample(backgroundZZ, inputTFile, region = region, eventType = "ZZ", flavor = flavor, finishAfterNSystematics = doNSystematics)

    chan.AddSample(backgroundZZ)

    # H4l Background
    ### And we create a second background for good measure
    backgroundH4l = ROOT.RooStats.HistFactory.Sample("backgroundH4l",templatePaths["H4l"] , inputFileName)
    # backgroundH4l.ActivateStatError()
    # backgroundH4l.AddOverallSys("syst3", 0.95, 1.05 )
    backgroundH4l.AddNormFactor("H4lNorm", 1, 0, 3) # let's add this to fit the normalization of the background
    addSystematicsToSample(backgroundH4l, inputTFile, region = region, eventType = "H4l", flavor = flavor, finishAfterNSystematics = doNSystematics)
    chan.AddSample(backgroundH4l)


    # Done with this channel
    # Add it to the measurement:
    ### Now that we have fully configured our channel, we add it to the main measurement
    meas.AddChannel(chan)

    # Collect the histograms from their files,
    # print some output,
    ### At this point, we have only given our channel and measurement the input histograms as strings We must now have the measurement open the files, collect the histograms, copy and store them. This step involves I/O 
    meas.CollectHistograms()

    ### Print to the screen a text representation of the model just for minor debugging
    #meas.PrintTree();

    # One can print XML code to an output directory:
    # meas.PrintXML("xmlFromCCode", meas.GetOutputFilePrefix());

    meas.PrintXML("tutorialBuildingHistFactoryModel", meas.GetOutputFilePrefix());

    #meas.CollectHistograms()
    chan.CollectHistograms() #  see here why this is needed: https://root-forum.cern.ch/t/histfactory-issue-with-makesinglechannelmodel/34201

    return meas



def addSystematicsToSample(histFactorySample, inputFileOrName, region = "ZXSR", eventType = "H4l", flavor = "All", finishAfterNSystematics = -1 ):

    # let's allow inputFileOrName to be the name of a root file, or or an opened root file, i.e. a ROOT.TFile object
    if   isinstance(inputFileOrName, str):         inputTFile = ROOT.TFile(inputFileOrName,"OPEN")
    elif isinstance(inputFileOrName, ROOT.TFile):  inputTFile = inputFileOrName
    else:  warnings.warn("addSystematicsToSample is not properly configured. No systematics Added"); return None

    if finishAfterNSystematics == 0 : return None # no need to do the whole rigmarole if we are not adding any systematics anyway

    # let's store information about the systematics here in the following way
    # systematicsDict[ name of systematis][up or down variation][  ] = <aString>
    systematicsDict = collections.defaultdict(lambda: collections.defaultdict(dict))

    # let's parste all the contents of the root file and select the relevant information
    for path, myTObject  in TDirTools.generateTDirPathAndContentsRecursive(inputTFile, newOwnership = None):  

        if not all([x in path for x in [region,eventType,flavor] ]): continue # ignore the regions, etc. that we are not concerned with are right now
        if "Nominal" in path: continue # nominal is not a systematic

        # determine the systematics name
        filenameUpToSystematic = re.search("(?:(?!(1down|1up)).)*", path).group() # systematics ends with 1up or 1down, find the string parts beforehand
        systematicsName = filenameUpToSystematic.split("/")[-1] # we split at the slash to get the systematics name (and we do it this way because regex is hard :-/ )

        # find out if this the up or down variation of the given systematic
        variationType = re.search("(?<="+systematicsName+")(.*?)(?=\/)", path).group() # find smallest stringt between the systematics name and a '/', should be the up or down variation signifier
        assert variationType == '1down' or variationType == "1up"

        # discern the fineName, the path to the histogram within the TFile, and the name of the histogram
        fileName = re.search("(.*?).root", path).group() # grab everything up to and including the word '.root' (in a lazy way due to the '?') 
        tDirPath = re.search("(?<=.root/)(.*)\/", path).group() # find everyting between '.root' and the last slash
        histName = re.search("[^\/]+$", path).group() # find everything after last slash 

        # store the information we just discerned        
        systematicsDict[systematicsName][variationType]['histName'] = histName
        systematicsDict[systematicsName][variationType]['fileName'] = fileName
        systematicsDict[systematicsName][variationType]['tDirPath'] = tDirPath

    if isinstance(inputFileOrName, str): inputTFile.Close() # close the file if we had opened it

    # add the histograms to the histFactory sample
    sysCounter = 0 # but remember how many systematics we added, so that we can limit that number
    for systematicsName in systematicsDict:
        if finishAfterNSystematics == sysCounter : return None
        sysCounter += 1

        # get the proper parts of the dict tree, and add the systematics
        upSys = systematicsDict[systematicsName]["1up"]
        downSys = systematicsDict[systematicsName]["1down"]
        # AddHistoSys (                 Name         , HistoNameLow         , HistoFileLow       ,  HistoPathLow       ,  HistoNameHigh      , HistoFileHigh    ,  HistoPathHigh)
        histFactorySample.AddHistoSys(systematicsName, downSys['histName'] , downSys['fileName'],  downSys['tDirPath'],  upSys['histName'] , upSys['fileName'],  upSys['tDirPath'])

    return None

def getProfileLikelihoodLimits(workspace, confidenceLevel = 0.95, drawLikelihoodIntervalPlot = False):
    # get the limits on the (first) parameter of interest by doing a profile likelyhood scan
    # pl.SetConfidenceLevel(0.6827 ) # remember 1 sigma =0.6827, 2 sigma=0.9545,  3 sigma=0.9973 

    mc = workspace.obj("ModelConfig")
    data = workspace.data("obsData")
    
    parameterOfInterest = mc.GetParametersOfInterest().first() # use this, so we don't have to pass the name of the parameter of interest along

    pl = ROOT.RooStats.ProfileLikelihoodCalculator(data,mc)
    #pl.SetConfidenceLevel(0.6827 ) # remember 1 sigma =0.6827, 2 sigma=0.9545,  3 sigma=0.9973 
    #pl.SetConfidenceLevel(0.9545 )
    pl.SetConfidenceLevel(0.95 )

    interval = pl.GetInterval()

    #intervalVariables = {x.GetName() : x for x in TDirTools.rooArgSetToList(interval.GetParameters())}
    #interval.UpperLimit(intervalVariables["SigXsecOverSM"])
    #interval.LowerLimit(intervalVariables["SigXsecOverSM"])

    # we need to call this here, so that we can retrieve the limits later on with the elements of interval.GetBestFitParameters() later on. It's weird.
    interval.UpperLimit( parameterOfInterest )
    interval.LowerLimit( parameterOfInterest )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if drawLikelihoodIntervalPlot:
        plot = ROOT.RooStats.LikelihoodIntervalPlot(interval)
        plot.SetNPoints(50)
        plot.SetMaximum(5)
        canvas = ROOT.TCanvas()
        plot.Draw()
        canvas.Draw()
        canvas.Print("ProfileLikelihood.pdf")

    return interval

def expectedLimitsAsimov(workspace, confidenceLevel = 0.95, drawLimitPlot = False ):
    # get expected upper limits on the parameter of interest using the 'AsymptoticCalculator'
    # provides also +/- n sigma intervals on the expected limits
    # I don't understand this 'AsymptoticCalculator' fully yet, but the expected limits look reasonable 
    # I based this here on the following tutorial: https://roostatsworkbook.readthedocs.io/en/latest/docs-cls.html#

    modelConfig = workspace.obj("ModelConfig") # modelConfig = modelConfig
    data = workspace.data("obsData")

    # setup the cloned modelConfig
    modelConfigClone = modelConfig.Clone( modelConfig.GetName()+"Clone" )
    mcClonePOI = modelConfigClone.GetParametersOfInterest().first()

    mcClonePOI.setVal(1.0)
    modelConfigClone.SetSnapshot( ROOT.RooArgSet( mcClonePOI ) )

    #setup the background only model

    bModel = modelConfig.Clone("BackgroundOnlyModel")
    bModelPOI = bModel.GetParametersOfInterest().first()

    bModelPOI.setVal(0)
    bModel.SetSnapshot( ROOT.RooArgSet( bModelPOI )  )

    #  AsymptoticCalculator(data, alternativeModel, nullModel)
    asympCalc = ROOT.RooStats.AsymptoticCalculator(data, bModel, modelConfigClone ) # asymptotic calculator is for the profile likelihood ratio
    asympCalc.SetOneSided(True);


    inverter = ROOT.RooStats.HypoTestInverter(asympCalc)
    inverter.SetConfidenceLevel( confidenceLevel );
    inverter.UseCLs(True);
    inverter.SetVerbose(False);
    inverter.SetFixedScan(60,0.0,6.0); # set number of points , xmin and xmax

    result =  inverter.GetInterval();

    if drawLimitPlot: 
        hypoCanvas = ROOT.TCanvas("hypoCanvas", "hypoCanvas", 1300/2,1300/2)
        inverterPlot = ROOT.RooStats.HypoTestInverterPlot("HTI_Result_Plot","HypoTest Scan Result",result);
        inverterPlot.Draw("CLb 2CL");  # plot also CLb and CLs+b
        hypoCanvas.Update()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return result

def translateLimits( rooStatsObject, nSigmas = 1 ):
    # we assume that there is always only one parameter of interest
    
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if isinstance( rooStatsObject , ROOT.RooStats.LikelihoodInterval ):
        limitObject = TDirTools.rooArgSetToList( rooStatsObject.GetBestFitParameters() )[0]
        
        bestEstimate = limitObject.getVal()
        lowLimit  = rooStatsObject.LowerLimit( limitObject )
        highLimit = rooStatsObject.UpperLimit( limitObject )

        suffix = "ProfileLikelihood"

    elif isinstance( rooStatsObject , ROOT.RooStats.HypoTestInverterResult ):
        limitObject = rooStatsObject

        bestEstimate = limitObject.GetExpectedUpperLimit(0)

        lowLimit  = rooStatsObject.GetExpectedUpperLimit(-nSigmas)
        highLimit = rooStatsObject.GetExpectedUpperLimit(+nSigmas)

        suffix = "expectedUpperLimit"

    name = limitObject.GetName() +"_"+str(nSigmas) +"SigmaLimit" + "_" + suffix
    title = limitObject.GetTitle() +"_"+str(nSigmas) +"SigmaLimit" + "_" + suffix

    outputRooRealvar = ROOT.RooRealVar( name, title ,bestEstimate,lowLimit , highLimit)
    # get the limits via .getVal(), .getMin(), .getMax()

    return outputRooRealvar

        

def getFullTDirPath(masterDict, region, eventType, systVariation , flavor):

    histName = masterDict[region][eventType][systVariation][flavor].GetName()
    fullTDirPath = region+"/"+eventType+"/"+systVariation+"/"+flavor+"/"+histName

    return fullTDirPath



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--outputDir", type=str, default="." ,
        help="directory of where to save the output. Default is the direcotry of the .py file" )
    parser.add_argument("--outputFileName", type=str, default=None ,
        help="name of the output file. We'll add .root if necessary" )

    args = parser.parse_args()


    startTime = time.time()
    activateATLASPlotStyle()

    doNSystematics = -1

    # RooFit command to suppress all the Info and Progress message is below
    # the message are ordered by the following enumeration defined in RooGlobalFunc.h
    # enum MsgLevel { DEBUG=0, INFO=1, PROGRESS=2, WARNING=3, ERROR=4, FATAL=5 } ;
    rooMsgServe = ROOT.RooMsgService.instance()                
    rooMsgServe.setGlobalKillBelow(ROOT.RooFit.WARNING)
    

    #inputFileName = "preppedHists_mc16a_unchangedErros_3GeVBins.root" 
    #inputFileName = "preppedHists_mc16a_sqrtErros_3GeVBins.root"
    #inputFileName = "preppedHists_mc16a_sqrtErros_1GeVBins.root"
    inputFileName = "preppedHists_mc16a_sqrtErros_0.5GeVBins.root"
    #inputFileName = "preppedHists_mc16ade_sqrtErros_0.5GeVBins.root"

    inputTFile = ROOT.TFile(inputFileName,"OPEN")
    masterDict = TDirTools.buildDictTreeFromTDir(inputTFile) # use this dict for an overview of what hists / channels / systematics / flavors are available


    #limitType =  "asymptotic"# options: "toys", "asymptotic", "observed"
    limitType =  "toys"      # options: "toys", "asymptotic", "observed"
    #limitType =  "observed"  # options: "toys", "asymptotic", "observed"

    # deal with the output file

    if args.outputFileName is None: outputFileName = "limitOutput_"+limitType+".root"
    else:                           outputFileName = args.outputFileName

    if not outputFileName.endswith(".root"): outputFileName += ".root"

    if not os.path.exists(args.outputDir): os.makedirs(args.outputDir)
    outputFileNameFull = args.outputDir + "/" + outputFileName # "limitOutput_H4lNormFloating_allSystematic_allmassPoints_fullRun2.root"  # 

    writeTFile = ROOT.TFile( outputFileNameFull,  "RECREATE")# "UPDATE")


    region = "ZXSR"
    flavor = "All"

    massesToProcess =  range(15,56,1)#[30]#range(15,56,5)
    # setup some output datastructures
    overviewHist = ROOT.TH1D("ZX_limit_Overview","ZX_limit_Overview", len(massesToProcess), min(massesToProcess), max(massesToProcess) + 1 ) # construct the hist this way, so that we have a bin for each mass point

    observedLimitGraph    = graphHelper.createNamedTGraphAsymmErrors("observedLimitGraph")
    expectedLimitsGraph_1Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_1Sigma")
    expectedLimitsGraph_2Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_2Sigma")

    bestEstimateDict   = collections.defaultdict(list)
    upperLimits1SigDict = collections.defaultdict(list)
    upperLimits2SigDict = collections.defaultdict(list)

    myHistSampler = sampleTH1FromTH1.histSampler()

    if limitType == "toys":   nIterations = 30
    else:                     nIterations = 1

    for limitIteration in xrange(nIterations):

        # setup data hist

        if limitType == "toys":
            dataHistPath = getFullTDirPath(masterDict, region, "expectedData" , "Nominal",  flavor)
            expectedDataHist = inputTFile.Get( dataHistPath )

            dataHist = myHistSampler.sampleFromTH1(expectedDataHist)

        else :   # either do asymptotic expected limits, or get real data limits
            dataHistPath = getFullTDirPath(masterDict, region, "data" , "Nominal",  flavor)
            dataHist = inputTFile.Get( dataHistPath )

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


        for massPoint in massesToProcess:

            templatePaths = {}

            # Prep signal sample locations
            signalSample = "ZZd %iGeV" %( massPoint )
            signalSampleExact = difflib.get_close_matches( signalSample  , masterDict[region].keys())[0]
            templatePaths["Signal"]  = getFullTDirPath(masterDict, region, signalSampleExact , "Nominal",  flavor) # region+"/ZZd, m_{Zd} = 35GeV/Nominal/"+flavor+"/ZXSR_ZZd, m_{Zd} = 35GeV_Nominal_All"

            templatePaths["ZZ"]      = getFullTDirPath(masterDict, region, "ZZ" , "Nominal",  flavor)
            templatePaths["H4l"]     = getFullTDirPath(masterDict, region, "H4l" , "Nominal",  flavor)

            templatePaths["Data"]    = dataHist

            
            meas = prepMeasurement(templatePaths, region, flavor, inputFileName, inputTFile)

            chan = meas.GetChannel("signalRegion")

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            #One can also create a workspace for only a single channel of a model by supplying that channel:
            hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast(meas)
            #chan.CollectHistograms() #  see here why this is needed: https://root-forum.cern.ch/t/histfactory-issue-with-makesinglechannelmodel/34201
            workspace = hist2workspace.MakeSingleChannelModel(meas, chan)


            if limitType == "asymptotic":
                # from: https://roostatsworkbook.readthedocs.io/en/latest/docs-cls.html

                asymptoticResuls = expectedLimitsAsimov( workspace , drawLimitPlot = False)

                likelihoodLimit = translateLimits(asymptoticResuls, nSigmas = 1)
                likelihoodLimit_2Sig = translateLimits(asymptoticResuls, nSigmas = 2)

            else :  # profile limits, for actual limits or expected limits from toys 

                # profile limit: profileLimit.getVal(), profileLimit.getErrorHi(), profileLimit.getErrorLo()
                interval = getProfileLikelihoodLimits(workspace , drawLikelihoodIntervalPlot = False)

                likelihoodLimit = translateLimits( interval, nSigmas = 1 )
                likelihoodLimit_2Sig = translateLimits( interval, nSigmas = 2 )


            graphHelper.fillTGraphWithRooRealVar(observedLimitGraph, massPoint, likelihoodLimit)
            graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_1Sigma, massPoint, likelihoodLimit)
            graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_2Sigma, massPoint, likelihoodLimit_2Sig)


            bestEstimateDict[signalSample].append( likelihoodLimit.getVal() )
            upperLimits1SigDict[signalSample].append(likelihoodLimit.getMax())
            upperLimits2SigDict[signalSample].append(likelihoodLimit_2Sig.getMax())





            continue

            
            histHelper.fillBin(overviewHist, massPoint, interval.UpperLimit(intervalVariables["SigXsecOverSM"]) )

            #allWorkspaceVariables = TDirTools.rooArgSetToList( workspace.allVars() )
            #workspaceVarDict = {x.GetName() : x for x in allWorkspaceVariables}
            #keysafeDictReturn = lambda x,aDict : aDict[x] if x in aDict else None # returns none if x is not among the dict's keys
            #keysafeDictReturn("H4lNorm", workspaceVarDict)

            drawDict = {templatePaths["Data"]   : None, 
                        templatePaths["H4l"]    : keysafeDictReturn("H4lNorm", workspaceVarDict),
                        templatePaths["ZZ"]     : None,
                        templatePaths["Signal"] : interval}


            writeTFile.mkdir( signalSample ); 
            writeTDir = writeTFile.Get( signalSample )
            writeTDir.cd()


            drawNominalHists(inputFileName, drawDict, writeToFile =  None)
            #drawNominalHists(inputFileName, drawDict, writeToFile =  writeTDir)


            #TDirTools.rooArgSetToList( interval.GetBestFitParameters() )

            # stop here so we can experiment with the limit extracting process
            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            #############################################################
            # likeli working limit estimation below
            #############################################################

            # Now, do the measurement

            ### Finally, run the measurement. This is the same thing that happens when one runs 'hist2workspace' on an xml files
            ROOT.RooStats.HistFactory.MakeModelAndMeasurementFast(meas);

            ##################### end of the tutorial, everything below here is me tinkering
            # I am tinkering with things from here: https://www.nikhef.nl/~vcroft/KaggleFit-Histfactory.html
            hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast(meas)
            #workspace = hist2workspace.MakeSingleChannelModel(meas, chan)
            workspace = hist2workspace.MakeCombinedModel(meas)

            mc = workspace.obj("ModelConfig")
            data = workspace.data("obsData")
            x = workspace.var("SigXsecOverSM")

            pl = ROOT.RooStats.ProfileLikelihoodCalculator(data,mc)
            pl.SetConfidenceLevel(0.95); 

            pl.GetInterval()

            #ROOT.RooStats.HistFactory.GetChannelEstimateSummaries(meas,chan)

        ###############################################
        # end of "for massPoint in ... "
        ###############################################


        writeTFile = ROOT.TFile( outputFileNameFull,  "RECREATE")# "UPDATE")
        writeTFile.cd()
        bestEstimatesTTree   = fillTTreeWithDictOfList(bestEstimateDict, treeName = "bestEstimates_"+limitType)
        upperLimits1SigTTree = fillTTreeWithDictOfList(upperLimits1SigDict, treeName = "upperLimits1Sig_"+limitType)
        upperLimits2SigTTree = fillTTreeWithDictOfList(upperLimits2SigDict, treeName = "upperLimits2Sig_"+limitType)

        writeTFile.Write()


    ###############################################
    # end of "for limitIteration in xrange(nIterations): "
    ###############################################

    graphOverviewCanvas = makeGraphOverview( graphHelper.getTGraphWithoutError( observedLimitGraph , ySetpoint = "yHigh"), 
                                             expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = writeTFile)


    #overviewCanvas = ROOT.TCanvas( "XS limits", "XS limits", 1300/2,1300/2)
    #overviewHist.Draw("L"); overviewCanvas.Update()
    #overviewHist.Write()
    #observedLimitGraph.Write()
    #expectedLimitsGraph_1Sigma.Write()
    #expectedLimitsGraph_2Sigma.Write()


    #bestEstimatesTTree.Write()
    #upperLimits1SigTTree.Write()
    #upperLimits2SigTTree.Write()

    #limitType = ROOT.TString( str(limitType) )
    #limitType.Write()


    writeTFile.Close()

    runtime = time.time() - startTime

    print "Memory usage: %s kB \t Runtime: " % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8) + str(datetime.timedelta(seconds=runtime) )



    print("All Done!")
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

