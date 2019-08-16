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
        histPath = " ZXSR/"+key+"/Nominal/"+flavor
        
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

    return allTheHistoSys


if __name__ == '__main__':

    inputFileName = "preppedHists_mc16a.root"

    inputTFile = ROOT.TFile(inputFileName,"OPEN")
    

    


    masterDict = TDirTools.buildDictTreeFromTDir(inputTFile)

    prepHistoSys(masterDict['ZXSR']["H4l"])

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here # signalRegion/H4l

    #drawNominalHists(inputFileName)

    ### Create the measurement object
    ### This is the top node of the structure
    ### We do some minor configuration as well
    meas = ROOT.RooStats.HistFactory.Measurement("ZXMeasurement", "ZXMeasurement")

    ### Set the prefix that will appear before
    ### all output for this measurement
    ### We Set ExportOnly to false, meaning
    ### we will fit the measurement and make 
    ### plots in addition to saving the workspace
    meas.SetOutputFilePrefix("./testHistfactoryOutput/")
    meas.SetExportOnly(False)

    ### Set the name of the parameter of interest
    ### Note that this parameter hasn't yet been
    ### created, we are anticipating it
    meas.SetPOI("SigXsecOverSM")

    meas.AddConstantParam("Lumi")           # this is not part of the C++ exsample
    meas.AddConstantParam("alpha_syst1")    # this is not part of the C++ exsample

    ### Set the luminosity
    ### There are a few conventions for this.
    ### Here, we assume that all histograms have
    ### already been scaled by luminosity
    ### We also set a 10% uncertainty
    meas.SetLumi(1.0)
    meas.SetLumiRelErr(0.10)


    # Create a channel

    ### Okay, now that we've configured the measurement,
    ### we'll start building the tree.
    ### We begin by creating the first channel
    chan = ROOT.RooStats.HistFactory.Channel("signalRegion")

    ### First, we set the 'data' for this channel
    ### The data is a histogram represeting the 
    ### measured distribution.  It can have 1 or many bins.
    ### In this example, we assume that the data histogram
    ### is already made and saved in a ROOT file.  
    ### So, to 'set the data', we give this channel the
    ### path to that ROOT file and the name of the data
    ### histogram in that root file
    ### The arguments are: SetData(HistogramName, HistogramFile)
    chan.SetData("signalRegion/mockData/Nominal/All/h_ZXSR_All_HWindow_m34", InputFile)
    #chan.SetStatErrorConfig(0.05, "Poisson") # this seems to be not part of the C++ exsample


    # Now, create some samples

    # Create the signal sample
    ### Now that we have a channel and have attached
    ### data to it, we will start creating our Samples
    ### These describe the various processes that we
    ### use to model the data.
    ### Here, they just consist of a signal process
    ### and a single background process.
    signal = ROOT.RooStats.HistFactory.Sample("signal", "signalRegion/H4l/Nominal/All/h_ZXSR_All_HWindow_m34", InputFile)
    ### Having created this sample, we configure it
    ### First, we add the cross-section scaling
    ### parameter that we call SigXsecOverSM
    ### Then, we add a systematic with a 5% uncertainty
    ### Finally, we add it to our channel
    #signal.AddOverallSys("syst1",  0.1, 1.9) # review what does this exactly do
    signal.AddNormFactor("SigXsecOverSM", 1, 0, 3)
    chan.AddSample(signal)

    # Background 1
    ### We do a similar thing for our background
    background1 = ROOT.RooStats.HistFactory.Sample("background1", "signalRegion/ZZ/Nominal/All/h_ZXSR_All_HWindow_m34", InputFile)
    #background1.ActivateStatError()#ActivateStatError("background1_statUncert", InputFile)
    #background1.AddOverallSys("syst2", 0.95, 1.05 )
    #background1.AddNormFactor("background1Norm", 1, 0, 3) # let's add this to fit the normalization of the background
    chan.AddSample(background1)

    # Background 2
    ### And we create a second background for good measure
    # background2 = ROOT.RooStats.HistFactory.Sample("background2", "rooHistGaussData1TH1__indepVariable", InputFile)
    # background2.ActivateStatError()
    # background2.AddOverallSys("syst3", 0.95, 1.05 )
    # chan.AddSample(background2)


    # Done with this channel
    # Add it to the measurement:
    ### Now that we have fully configured our channel,
    ### we add it to the main measurement
    meas.AddChannel(chan)

    # Collect the histograms from their files,
    # print some output,
    ### At this point, we have only given our channel
    ### and measurement the input histograms as strings
    ### We must now have the measurement open the files,
    ### collect the histograms, copy and store them.
    ### This step involves I/O 
    meas.CollectHistograms()

    ### Print to the screen a text representation of the model
    ### just for minor debugging
    meas.PrintTree();

    # One can print XML code to an output directory:
    # meas.PrintXML("xmlFromCCode", meas.GetOutputFilePrefix());

    meas.PrintXML("tutorialBuildingHistFactoryModel", meas.GetOutputFilePrefix());

    # Now, do the measurement

    ### Finally, run the measurement.
    ### This is the same thing that happens when
    ### one runs 'hist2workspace' on an xml files
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