# let's try some limit setting with the output from limitSettingHistPrep.py

# for a start we will follow this tutorial
# http://ghl.web.cern.ch/ghl/html/HistFactoryDoc.html
# and then expand on it


import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re

# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.rootDictAndTDirTools as TDirTools
import plotPostProcess as postProcess


def drawNominalHists(inputFileName, myDrawDSIDHelper = postProcess.DSIDHelper() ):

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        TLegend = ROOT.TLegend(0.15,0.65,0.45,0.87)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(2);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend


    inputTFile = ROOT.TFile(inputFileName, "OPEN")

    histDict = {"H4l" : None, "ZZ" : None, "const" : None}

    flavor = "All"

    nominalHistStack = ROOT.THStack("nominalStack","nominalStack")

    legend = setupTLegend()

    for key in histDict:
        histPath = "ZXSR/"+key+"/Nominal/"+flavor
        
        histTDir = inputTFile.Get(histPath)

        histList = TDirTools.TDirToList(histTDir)

        assert len(histList) == 1

        currentTH1 = histList[0].Clone(key)

        nominalHistStack.Add(currentTH1)

        histDict[key] = currentTH1
        legend.AddEntry(currentTH1 , key , "f");

        #TDirTools.generateTDirContents(inputTFile.Get(histPath))

    myDrawDSIDHelper.colorizeHistsInDict(histDict) # sets fill color to solid and pics consistent color scheme
    
    canvas = ROOT.TCanvas("overviewCanvas","overviewCanvas",1300/2,1300/2);
    nominalHistStack.Draw("Hist")
    #nominalHistStack.Draw("same E2 ")   # "E2" Draw error bars with rectangles:  https://root.cern.ch/doc/v608/classTHistPainter.html
    legend.Draw(); # do legend things
    canvas.Update()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


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


def addSystematicsToSample(histFactorySample, inputFileOrName, region = "ZXSR", eventType = "H4l", flavor = "All", finishAfterNSystematics = -1 ):

    # let's allow inputFileOrName to be the name of a root file, or or an opened root file, i.e. a ROOT.TFile object
    if   isinstance(inputFileOrName, str):         inputTFile = ROOT.TFile(inputFileOrName,"OPEN")
    elif isinstance(inputFileOrName, ROOT.TFile):  inputTFile = inputFileOrName
    else:  warnings.warn("addSystematicsToSample is not properly configured. No systematics Added"); return None

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


if __name__ == '__main__':

    inputFileName = "preppedHists_mc16a.root"

    inputTFile = ROOT.TFile(inputFileName,"OPEN")
    masterDict = TDirTools.buildDictTreeFromTDir(inputTFile) # we'll use this dict for the systematics histograms etc.

    

    #drawNominalHists(inputFileName)

    ### Create the measurement object
    ### This is the top node of the structure
    ### We do some minor configuration as well
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
    meas.SetLumiRelErr(0.10)


    # Create a channel

    ### Okay, now that we've configured the measurement, we'll start building the tree. We begin by creating the first channel
    chan = ROOT.RooStats.HistFactory.Channel("signalRegion")

    ### First, we set the 'data' for this channel The data is a histogram represeting the measured distribution.  It can have 1 or many bins. In this example, we assume that the data histogram is already made and saved in a ROOT file.   So, to 'set the data', we give this channel the path to that ROOT file and the name of the data histogram in that root file The arguments are: SetData(HistogramName, HistogramFile)
    chan.SetData("ZXSR/mockData/Nominal/All/ZXSR_H4l_Nominal_All", inputFileName)
    #chan.SetStatErrorConfig(0.05, "Poisson") # this seems to be not part of the C++ exsample


    # Now, create some samples

    # Create the signal sample Now that we have a channel and have attached data to it, we will start creating our Samples These describe the various processes that we use to model the data. Here, they just consist of a signal process and a single background process.
    signal = ROOT.RooStats.HistFactory.Sample("signal", "ZXSR/ZZd, m_{Zd} = 35GeV/Nominal/All/ZXSR_ZZd, m_{Zd} = 35GeV_Nominal_All", inputFileName)
    ### Having created this sample, we configure it First, we add the cross-section scaling parameter that we call SigXsecOverSM Then, we add a systematic with a 5% uncertainty Finally, we add it to our channel
    #signal.AddOverallSys("syst1",  0.1, 1.9) # review what does this exactly do
    signal.AddNormFactor("SigXsecOverSM", 1, 0, 3)
    chan.AddSample(signal)

    # Background 1
    ### We do a similar thing for our background
    backgroundZZ = ROOT.RooStats.HistFactory.Sample("backgroundZZ", "ZXSR/ZZ/Nominal/All/ZXSR_ZZ_Nominal_All", inputFileName)
    #backgroundZZ.ActivateStatError()#ActivateStatError("backgroundZZ_statUncert", inputFileName)
    #backgroundZZ.AddOverallSys("syst2", 0.95, 1.05 )
    backgroundZZ.AddNormFactor("ZZNorm", 1, 0, 3) # let's add this to fit the normalization of the background
    chan.AddSample(backgroundZZ)


    # Background 2
    ### And we create a second background for good measure
    backgroundH4l = ROOT.RooStats.HistFactory.Sample("backgroundH4l", "ZXSR/H4l/Nominal/All/ZXSR_H4l_Nominal_All", inputFileName)
    # backgroundH4l.ActivateStatError()
    # backgroundH4l.AddOverallSys("syst3", 0.95, 1.05 )
    backgroundH4l.AddNormFactor("H4lNorm", 1, 0, 3) # let's add this to fit the normalization of the background

    #histoSysList = prepHistoSys(masterDict['ZXSR']["H4l"])
    #backgroundH4l.AddHistoSys(histoSysList[0])


    addSystematicsToSample(backgroundH4l, inputTFile, region = "ZXSR", eventType = "H4l", flavor = "All", finishAfterNSystematics = 2)

    # let's see what happens when we add systematcs

    #backgroundH4l.AddOverallSys( "background_uncertainty",  -1., 1. )
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
    meas.PrintTree();

    # One can print XML code to an output directory:
    # meas.PrintXML("xmlFromCCode", meas.GetOutputFilePrefix());

    meas.PrintXML("tutorialBuildingHistFactoryModel", meas.GetOutputFilePrefix());

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here #  ZXSR/H4l
    # Now, do the measurement

    ### Finally, run the measurement. This is the same thing that happens when one runs 'hist2workspace' on an xml files
    ROOT.RooStats.HistFactory.MakeModelAndMeasurementFast(meas);

    #pass
    #if __name__ == "__main__":
    #    main()
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    ##################### end of the tutorial, everything below here is me tinkering
    # I am tinkering with things from here: https://www.nikhef.nl/~vcroft/KaggleFit-Histfactory.html
    hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast(meas)
    #workspace = hist2workspace.MakeSingleChannelModel(meas, chan)
    workspace = hist2workspace.MakeCombinedModel(meas)

    mc = workspace.obj("ModelConfig")
    data = workspace.data("obsData")
    x = workspace.var("SigXsecOverSM")


    workspace.var("SigXsecOverSM").Print()


    pl = ROOT.RooStats.ProfileLikelihoodCalculator(data,mc)
    pl.SetConfidenceLevel(0.95); 

    pl.GetInterval()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    workspace.var("SigXsecOverSM").Print()
    workspace.var("SigXsecOverSM").getError() # gets me the error of the on the parameter of interest 
    x.var("SigXsecOverSM").getError() # this as well!

    # 



    #plot = ROOT.RooStats.LikelihoodIntervalPlot(interval)
    #plot.SetNPoints(50)
    #plot.SetMaximum(5)
    #c = ROOT.TCanvas()
    #plot.Draw()
    #c.Draw()


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    ############################## 

    # me playing around with things

    ROOT.RooStats.HistFactory.GetChannelEstimateSummaries(meas,chan)