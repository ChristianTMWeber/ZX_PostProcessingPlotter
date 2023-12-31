# let's try some limit setting with the output from limitSettingHistPrep.py

# for a start we will follow this tutorial
# http://ghl.web.cern.ch/ghl/html/HistFactoryDoc.html
# and then expand on it


import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import difflib # so I can be a bit lazier with identification of signal region masspoints via 'difflib.get_close_matches'
import warnings # to warn about things that might not have gone right
import resource # print 'Memory usage: %s (kB)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
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
import functions.tGraphHelpers as graphHelper

import limitFunctions.reportMemUsage as reportMemUsage


def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

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

def prepMeasurement( templatePaths, region, flavor, inputFileName, inputTFile, doStatError = False, doTheoreticalError = False):


    ### Create the measurement object ### This is the top node of the structure  ### We do some minor configuration as well
    meas = ROOT.RooStats.HistFactory.Measurement("ZXMeasurement", "ZXMeasurement")

    ### Set the prefix that will appear before all output for this measurement We Set ExportOnly to false, meaning we will fit the measurement and make  plots in addition to saving the workspace
    meas.SetOutputFilePrefix("./testHistfactoryOutput/")
    meas.SetExportOnly(False)

    ### Set the name of the parameter of interest Note that this parameter hasn't yet been created, we are anticipating it
    meas.SetPOI("SigXsecOverSM")


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    #meas.AddConstantParam("Lumi")           # this is not part of the C++ exsample
    #meas.AddConstantParam("alpha_syst1")    # this is not part of the C++ exsample

    ### Set the luminosity There are a few conventions for this. Here, we assume that all histograms have already been scaled by luminosity We also set a 10% uncertainty
    meas.SetLumi(1.0)
    meas.SetLumiRelErr(0.017) # This is for full run2: https://twiki.cern.ch/twiki/bin/viewauth/Atlas/LuminosityForPhysics#Proton_proton_data

    # Create a channel

    ### Okay, now that we've configured the measurement, we'll start building the tree. We begin by creating the first channel
    chan = ROOT.RooStats.HistFactory.Channel("signalRegion")
    ### First, we set the 'data' for this channel The data is a histogram represeting the measured distribution.  It can have 1 or many bins. In this example, we assume that the data histogram is already made and saved in a ROOT file.   So, to 'set the data', we give this channel the path to that ROOT file and the name of the data histogram in that root file The arguments are: SetData(HistogramName, HistogramFile)
    chan.SetData(templatePaths["Data"] )   # <- this seems to work, everything seems to run ok, but the programm completeres with a segmentation violation.
    #chan.SetData(templatePaths["Data"], inputFileName) # <- this one compleres without a segmentation vialation. Switch to this one if necessary
    
    #chan.SetStatErrorConfig(0.05, "Poisson") # I cont discern what this does. So let's not use it. It was also not in the reference I used

    # Now, create some samples

    # Create the signal sample Now that we have a channel and have attached data to it, we will start creating our Samples These describe the various processes that we use to model the data. Here, they just consist of a signal process and a single background process.
    signal = ROOT.RooStats.HistFactory.Sample("signal", templatePaths["Signal"], inputFileName)
    ### Having created this sample, we configure it First, we add the cross-section scaling parameter that we call SigXsecOverSM Then, we add a systematic with a 5% uncertainty Finally, we add it to our channel
    signal.AddNormFactor("SigXsecOverSM", 0, 0, 10) #  (<parameterName>, <start>, <lowLimit>, <highLimit>) keep the lower limit here at 0, otherwise the norm factor may get negative, which will introduce errors in the optimization routine
    addSystematicsToSample(signal, inputTFile, region = region, eventType = templatePaths["Signal"].split("/")[1] , flavor = flavor, finishAfterNSystematics = doNSystematics)
    if doStatError: signal.ActivateStatError()
    if doTheoreticalError: signal.AddOverallSys("QCDUncert", 1.-0.039, 1.+0.039)
    if doTheoreticalError: signal.AddOverallSys("PDFUncert", 1.-0.032, 1.+0.032)

    chan.AddSample(signal)

    # H4l Background
    if "H4l" in templatePaths.keys():
        ### And we create a second background for good measure
        backgroundH4l = ROOT.RooStats.HistFactory.Sample("backgroundH4l",templatePaths["H4l"] , inputFileName)
        backgroundH4l.AddNormFactor("H4lNorm", 1, 0, 3) # let's add this to fit the normalization of the background
        addSystematicsToSample(backgroundH4l, inputTFile, region = region, eventType = "H4l", flavor = flavor, finishAfterNSystematics = doNSystematics)
        if doStatError: backgroundH4l.ActivateStatError()
        if doTheoreticalError: backgroundH4l.AddOverallSys("QCDUncert", 1.-0.0672, 1.+0.0456)
        if doTheoreticalError: backgroundH4l.AddOverallSys("PDFUncert", 1.-0.0320, 1.+0.0320)
        

        chan.AddSample(backgroundH4l)

    # ZZ background
    if "ZZ" in templatePaths.keys():
        ### We do a similar thing for our background
        backgroundZZ = ROOT.RooStats.HistFactory.Sample("backgroundZZ", templatePaths["ZZ"], inputFileName)
        addSystematicsToSample(backgroundZZ, inputTFile, region = region, eventType = "ZZ", flavor = flavor, finishAfterNSystematics = doNSystematics)
        if doStatError: backgroundZZ.ActivateStatError()#ActivateStatError("backgroundZZ_statUncert", inputFileName)
        if doTheoreticalError: backgroundZZ.AddOverallSys("QCDUncert", 1.-0.019, 1.+0.022,)
        if doTheoreticalError: backgroundZZ.AddOverallSys("PDFUncert", 1.-0.030, 1.+0.028,)

        chan.AddSample(backgroundZZ)

    
    # Triboson and Z+ll background
    ### We do a similar thing for our background
    if "VVV_Z+ll" in templatePaths.keys():
        backgroundVV = ROOT.RooStats.HistFactory.Sample("VVV_Z+ll", templatePaths["VVV_Z+ll"], inputFileName)
        addSystematicsToSample(backgroundVV, inputTFile, region = region, eventType = "VVV_Z+ll", flavor = flavor, finishAfterNSystematics = doNSystematics)
        if doStatError: backgroundVV.ActivateStatError()#ActivateStatError("backgroundVV_statUncert", inputFileName)

        chan.AddSample(backgroundVV)




    # reducible background
    ### We do a similar thing for our background
    if "reducibleDataDriven" in templatePaths.keys():
        reducible = ROOT.RooStats.HistFactory.Sample("reducible", templatePaths["reducibleDataDriven"], inputFileName)
        #addSystematicsToSample(reducible, inputTFile, region = region, eventType = "reducibleDataDriven", flavor = flavor, finishAfterNSystematics = doNSystematics)
        if doStatError: reducible.ActivateStatError()# It looks like this setting makes it so that the binerror in the background template is taken into account
        if doNSystematics != 0 : reducible.AddOverallSys("reducible_Syst", 1.-(0.0822 + 0.1), 1.+(0.0822 + 0.1)) # add extra 10% norm uncertainty for differences between H4l and ZX 

        
        chan.AddSample(reducible)
        
    #backgroundZZ.AddOverallSys("syst2", 0.95, 1.05 )
    #backgroundZZ.AddNormFactor("ZZNorm", 1, 0, 3) # let's add this to fit the normalization of the background
    #addSystematicsToSample(backgroundZZ, inputTFile, region = region, eventType = "ZZ", flavor = flavor, finishAfterNSystematics = doNSystematics)

    


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


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

    eventTDir = inputTFile.Get(region).Get(eventType)

    # let's parste all the contents of the root file and select the relevant information
    for path, myTObject  in TDirTools.generateTDirPathAndContentsRecursive(eventTDir, baseString = eventTDir.GetName(), newOwnership = None):  
        if not all([x in path for x in [flavor] ]): continue # ignore the regions, etc. that we are not concerned with are right now
        if "Nominal" in path: continue # nominal is not a systematic
        
        # determine the systematics name
        filenameUpToSystematic = re.search("(?:(?!(1down|1up)).)*", path).group() # systematics ends with 1up or 1down, find the string parts beforehand
        systematicsName = filenameUpToSystematic.split("/")[-1] # we split at the slash to get the systematics name (and we do it this way because regex is hard :-/ )

        #if "MUONS_SAGITTA" in systematicsName: continue

        # find out if this the up or down variation of the given systematic
        variationType = re.search("(?<="+systematicsName+")(.*?)(?=\/)", path).group() # find smallest stringt between the systematics name and a '/', should be the up or down variation signifier
        assert variationType == '1down' or variationType == "1up"

        # discern the fineName, the path to the histogram within the TFile, and the name of the histogram
        fileName = inputTFile.GetName()
        #fileName = re.search("(.*?).root", path).group() # grab everything up to and including the word '.root' (in a lazy way due to the '?') 
        tDirPathLast = re.search("(.*)\/", path).group() # find everyting up to the last slash,  if we wanted to look after the '.root', add '(?<=.root/)'
        tDirPath = os.path.join(region, tDirPathLast)
        histName = re.search("[^\/]+$", path).group() # find everything after last slash 

        # store the information we just discerned        
        systematicsDict[systematicsName][variationType]['histName'] = histName
        systematicsDict[systematicsName][variationType]['fileName'] = fileName
        systematicsDict[systematicsName][variationType]['tDirPath'] = tDirPath
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if isinstance(inputFileOrName, str): inputTFile.Close() # close the file if we had opened it
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

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

def runProfileLikelihoodCalculator(data, modelConfig, confidenceLevel):
    parameterOfInterest = modelConfig.GetParametersOfInterest().first() # use this, so we don't have to pass the name of the parameter of interest along

    pl = ROOT.RooStats.ProfileLikelihoodCalculator(data,modelConfig)
    pl.SetConfidenceLevel( confidenceLevel ) # remember 1 sigma =0.6827, 2 sigma=0.9545,  3 sigma=0.9973 

    interval = pl.GetInterval()
    # we need to call this here, so that we can retrieve the limits later on with the elements of interval.GetBestFitParameters() later on. It's weird.
    interval.UpperLimit( parameterOfInterest )
    interval.LowerLimit( parameterOfInterest )

    return interval


def getProfileLikelihoodLimits(workspace, confidenceLevel = 0.95, drawLikelihoodIntervalPlot = False):
    # get the limits on the (first) parameter of interest by doing a profile likelyhood scan
    # pl.SetConfidenceLevel(0.6827 ) # remember 1 sigma =0.6827, 2 sigma=0.9545,  3 sigma=0.9973 

    mc = workspace.obj("ModelConfig")
    data = workspace.data("obsData")

    interval = runProfileLikelihoodCalculator(data, mc, confidenceLevel)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if drawLikelihoodIntervalPlot:
        plot = ROOT.RooStats.LikelihoodIntervalPlot(interval)
        plot.SetNPoints(50)
        plot.SetMaximum(5)
        canvas = ROOT.TCanvas()
        plot.Draw()
        canvas.Draw()
        canvas.Print("ProfileLikelihood.pdf")


    pullParamDict = getPullRelevantedParametersFromModelConfig(mc)

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if args.doPrePostFitImpacts: prePostFitImpactDict = makePreAndPostFitImpact(data, mc, confidenceLevel, referenceInterval = interval)
    else:                        prePostFitImpactDict = None

    return interval , pullParamDict, prePostFitImpactDict


def makePreAndPostFitImpact(data, refModelConfig, confidenceLevel, referenceInterval = None):

    def constrainRooRalVar(aRooRealVar, constrainTo): 
        aRooRealVar.setRange( constrainTo , constrainTo )
        aRooRealVar.setVal( constrainTo )
        aRooRealVar.setError(0)
        return None


    def getNuisanceParamVariationImpact(relevantNuianceParam, nuisancePSetValue , impactModelConfig , data):
        
        constrainRooRalVar(relevantNuianceParam, nuisancePSetValue )
        impactModelConfig.SetSnapshot(ROOT.RooArgSet(relevantNuianceParam))
        interval = runProfileLikelihoodCalculator(data, impactModelConfig, confidenceLevel)
        upperLimit = translateLimits( interval, nSigmas = 1 ).getMax()
        return upperLimit

    def copyRooRealVarRangeValError( target, source):
        target.setRange( source.getMin() , source.getMax()     )
        target.setVal(   source.getVal()   )
        target.setError( source.getError() )
        return None

    prePostFitImpactDict = collections.defaultdict(list) 

    if referenceInterval is not None: 
        referenceUpperLimit = translateLimits( referenceInterval, nSigmas = 1 ).getMax()
        prePostFitImpactDict["mu_reference"] = [referenceUpperLimit]
    

    postFitNuisanceParameters = TDirTools.rooArgSetToList(refModelConfig.GetNuisanceParameters())

    # we use this to decide whether a given nuisance has a prefit equivalent, without one we can't calculate the prefit impact
    prePostFitNameMapping = getMapBetweenNuisanceParametersAndGlobalObservables(refModelConfig) 

    # RooRealVar::SigXsecOverSM_1SigmaLimit_ProfileLikelihood = 3.46046e-09  L(0 - 0.473894)


    for nuisanceParameter in postFitNuisanceParameters:
        if "gamma_stat" in nuisanceParameter.GetName(): continue # skip parameters related to individual bin statistics

        impactModelConfig = refModelConfig.Clone( "fitModelConfig_"+nuisanceParameter.GetName())

        # clone the model confic, so that fixing nuisance parameter A does not persist when we concern us with nuisance parameter B
        impactModelConfig = refModelConfig.Clone( "fitModelConfig_"+nuisanceParameter.GetName()) 

        savedNuisanceParameter = nuisanceParameter.Clone( nuisanceParameter.GetName() + "saved")

        nuisanceSetValueUP   = nuisanceParameter.getVal() + nuisanceParameter.getErrorHi()
        nuisanceSetValueDOWN = nuisanceParameter.getVal() - nuisanceParameter.getErrorHi()

        prePostFitImpactDict["mu_postFitUp_"+nuisanceParameter.GetName()] = [getNuisanceParamVariationImpact(nuisanceParameter, nuisanceSetValueUP , refModelConfig.Clone() , data)]
        print( nuisanceParameter.GetName()  +" "+ str(nuisanceSetValueUP)   +" mu_postFitUp_"+nuisanceParameter.GetName()   +" "+  str(prePostFitImpactDict["mu_postFitUp_"+nuisanceParameter.GetName()] ) )
        
        prefitNuisanceVarName = prePostFitNameMapping[nuisanceParameter.GetName()] # get name of the associarated variable that holds the prefit uncertainty

        if prefitNuisanceVarName is not None: 

            prefitNuisanceVar = TDirTools.getElementFromRooArgSetByName( prefitNuisanceVarName , refModelConfig.GetGlobalObservables() )

            nuisancePrefitSetValueUP   = prefitNuisanceVar.getVal() + (prefitNuisanceVar.getMax() - prefitNuisanceVar.getVal() ) / 10. # prefit uncertainties on the nuisance parameters aappear to be stored oddly
            nuisancePrefitSetValueDOWN = prefitNuisanceVar.getVal() - (prefitNuisanceVar.getMax() - prefitNuisanceVar.getVal() ) / 10.

            #
            prePostFitImpactDict["mu_preFitUp_"+nuisanceParameter.GetName()] = [getNuisanceParamVariationImpact(nuisanceParameter, nuisancePrefitSetValueUP , refModelConfig.Clone() , data)]
            print( nuisanceParameter.GetName()  +" "+ str(nuisancePrefitSetValueUP)   + " mu_preFitUp_"+nuisanceParameter.GetName()   +" "+  str(prePostFitImpactDict["mu_preFitUp_"+nuisanceParameter.GetName()] ) )

        copyRooRealVarRangeValError( nuisanceParameter, savedNuisanceParameter) # reset the nuisance paramter back to its original value
        runProfileLikelihoodCalculator(data, impactModelConfig, confidenceLevel)

        prePostFitImpactDict["mu_postFitDown_"+nuisanceParameter.GetName()] = [getNuisanceParamVariationImpact(nuisanceParameter, nuisanceSetValueDOWN , refModelConfig.Clone() , data)]
        print( nuisanceParameter.GetName()  +" "+ str(nuisanceSetValueDOWN) +" mu_postFitDown_"+nuisanceParameter.GetName() +" "+  str(prePostFitImpactDict["mu_postFitDown_"+nuisanceParameter.GetName()] ) )


        prefitNuisanceVarName = prePostFitNameMapping[nuisanceParameter.GetName()] # get name of the associarated variable that holds the prefit uncertainty

        if prefitNuisanceVarName is not None: 

            #continue

            copyRooRealVarRangeValError( nuisanceParameter, savedNuisanceParameter) # reset the nuisance paramter back to its original value
            runProfileLikelihoodCalculator(data, impactModelConfig, confidenceLevel)

            prefitNuisanceVar = TDirTools.getElementFromRooArgSetByName( prefitNuisanceVarName , refModelConfig.GetGlobalObservables() )

            nuisancePrefitSetValueUP   = prefitNuisanceVar.getVal() + (prefitNuisanceVar.getMax() - prefitNuisanceVar.getVal() ) / 10. # prefit uncertainties on the nuisance parameters aappear to be stored oddly
            nuisancePrefitSetValueDOWN = prefitNuisanceVar.getVal() - (prefitNuisanceVar.getMax() - prefitNuisanceVar.getVal() ) / 10.

            prePostFitImpactDict["mu_preFitDown_"+nuisanceParameter.GetName()] = [getNuisanceParamVariationImpact(nuisanceParameter, nuisancePrefitSetValueDOWN , refModelConfig.Clone() , data)]
            print( nuisanceParameter.GetName()  +" "+ str(nuisancePrefitSetValueDOWN) + " mu_preFitDown_"+nuisanceParameter.GetName() +" "+  str(prePostFitImpactDict["mu_preFitDown_"+nuisanceParameter.GetName()] ) )

        copyRooRealVarRangeValError( nuisanceParameter, savedNuisanceParameter) # reset the nuisance paramter back to its original value
        runProfileLikelihoodCalculator(data, impactModelConfig, confidenceLevel)


        #import pdb; pdb.set_trace()

        # for x in prePostFitImpactDict: (x , prePostFitImpactDict[x])

    return prePostFitImpactDict

def getPullRelevantedParametersFromModelConfig(aModelConfig):
    #   outputs mapping via  'value name' : [value] in the pullParamDict
    #   The values in pullParamDict are all lists, so that they work better with the fillTTreeWithDictOfList
    #   
    #   pullParamDict['alpha_EG_RESOLUTION_ALL']               = [-1.3846881863344151e-08]
    #   pullParamDict['alpha_EG_RESOLUTION_ALL_err']           = [0.9926310565779826]
    #   pullParamDict['nom_alpha_EG_RESOLUTION_ALL']           = [0.0]
    #   pullParamDict['nom_alpha_EG_RESOLUTION_ALLupperLimit'] = [1.0]
    #
    #   value names starting with 'nom' refer to the prefit values
    #

    pullParamDict = collections.defaultdict(list)

    # put the GetGlobalObservables / nominal values of the parameters in a dict so we can associate them well with their postfir values
    nominalObservables = TDirTools.rooArgSetToList( aModelConfig.GetGlobalObservables () )
    for nominalObs in nominalObservables :
        #nominalParameterDict[nominalObs.GetName()] = nominalObs

        if "gamma_stat" in nominalObs.GetName(): continue # skip parameters related to individual bin statistics
        #nominalObs.Print()

        pullParamDict[nominalObs.GetName()] = [nominalObs.getVal()]
        prefitError = (nominalObs.getMax() - nominalObs.getVal() ) / 10.
        pullParamDict[nominalObs.GetName() + "upperLimit"] = [prefitError]

    # values starting with 'nom' refer to the prefit values,

    nuisanceParamList = TDirTools.rooArgSetToList(aModelConfig.GetNuisanceParameters())
    
    for nuisanceParam in nuisanceParamList: 
        if "gamma_stat" in nuisanceParam.GetName(): continue
        #nuisanceParam.Print()
        pullParamDict[nuisanceParam.GetName()]  = [nuisanceParam.getVal()]
        pullParamDict[nuisanceParam.GetName()+"_err"]  = [nuisanceParam.getErrorHi()]

    return pullParamDict

def getMapBetweenNuisanceParametersAndGlobalObservables(modelConfig):
    # outputs correspondenceDict, which is a mapping like 
    # correspondenceDict[ postFit nuisance parameter name] = 'preFit nuisance parameter name'
    # e.g.
    #   correspondenceDict[ "alpha_MUONS_SAGITTA_RESBIAS" ] = "nom_alpha_MUONS_SAGITTA_RESBIAS"
    #   correspondenceDict[ "Lumi" ] = "nominalLumi"
    #   etc 
    #
    #   remember, value names starting with 'nom' refer to the prefit values

    nominalRooRealDict = {}
    for rooReal in TDirTools.rooArgSetToList( modelConfig.GetGlobalObservables () ): 
        nominalRooRealDict[rooReal.GetName() ]  = rooReal

    nuisanceRooRealDict = {}
    for rooReal in TDirTools.rooArgSetToList( modelConfig.GetNuisanceParameters () ): 
        nuisanceRooRealDict[rooReal.GetName() ]  = rooReal

    correspondenceDict = {}
    for nuisanceName in nuisanceRooRealDict:
        # try closest match  
        closestMatch = difflib.get_close_matches( nuisanceName  , nominalRooRealDict.keys(), n=1, cutoff =0.3 )

        if len(closestMatch) == 0 or nuisanceName not in closestMatch[0]: 
            correspondenceDict[  nuisanceName    ] = None
        else: 
            correspondenceDict[  nuisanceName    ] = closestMatch[0]  

    return correspondenceDict


def prepAsymptoticCalculator(workspace ):

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
    #asympCalc.SetOneSided(True);
    asympCalc.SetPrintLevel(0) # suppress command line output 

    keepInScopeList = [modelConfig, data, modelConfigClone, mcClonePOI, bModel, bModelPOI]

    return asympCalc , keepInScopeList

def expectedLimitsAsimov(workspace, confidenceLevel = 0.95, drawLimitPlot = False ):
    # get expected upper limits on the parameter of interest using the 'AsymptoticCalculator'
    # provides also +/- n sigma intervals on the expected limits
    # I don't understand this 'AsymptoticCalculator' fully yet, but the expected limits look reasonable 
    # I based this here on the following tutorial: https://roostatsworkbook.readthedocs.io/en/latest/docs-cls.html#

    asympCalc, keepInScopeList = prepAsymptoticCalculator( workspace )
    asympCalc.SetOneSided(True);

    inverter = ROOT.RooStats.HypoTestInverter(asympCalc)
    inverter.SetConfidenceLevel( confidenceLevel );
    inverter.UseCLs(True);
    inverter.SetVerbose(False);
    inverter.SetFixedScan(60,0.0,6.0); # set number of points , xmin and xmax

    result =  inverter.GetInterval();
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if drawLimitPlot: 
        hypoCanvas = ROOT.TCanvas("hypoCanvas", "hypoCanvas", 1300/2,1300/2)
        inverterPlot = ROOT.RooStats.HypoTestInverterPlot("HTI_Result_Plot","HypoTest Scan Result",result);
        inverterPlot.Draw("CLb 2CL");  # plot also CLb and CLs+b
        hypoCanvas.Update()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return result

def p0SignifianceCalculation(workspace):

    #asympCalc , keepInScopeList = prepAsymptoticCalculator( workspace )

    modelConfig = workspace.obj("ModelConfig") # modelConfig = modelConfig
    data = workspace.data("obsData")



    sbModel = modelConfig.Clone("BackgroundOnlyModel")
    sbModelPOI = sbModel.GetParametersOfInterest().first()
    sbModelPOI.setVal(1)
    sbModel.SetSnapshot( ROOT.RooArgSet( sbModelPOI )  )


    # setup the cloned modelConfig
    bModel = modelConfig.Clone()
    bModel.SetName("B_only_model" )
    #mcClonePOI = bModel.GetParametersOfInterest().first()
    sbModelPOI.setVal(0)
    bModel.SetSnapshot( ROOT.RooArgSet( sbModelPOI ) )

    #setup the background only model


    #  AsymptoticCalculator(data, alternativeModel, nullModel)
    #asympCalc = ROOT.RooStats.AsymptoticCalculator(data, sbModel, bModel ) # asymptotic calculator is for the profile likelihood ratio
    #asympCalc.SetOneSided(True);
    #asympCalc.SetPrintLevel(-1) # suppress command line output 

    #sbModel.Print()
    #bModel.Print()


    #asympCalc.SetOneSidedDiscovery(True);
    ## asympCalc.SetOneSided(True)

    #asymCalcResult = asympCalc.GetHypoTest()
    #asymCalcResult.Print()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here 


    freqCalculator = ROOT.RooStats.FrequentistCalculator(data, sbModel, bModel);
    freqCalculator.SetToys(200,50);

    profileLikeTestStat = ROOT.RooStats.ProfileLikelihoodTestStat( sbModel.GetPdf() ) # ? do we need the bModel here, or rather the S+B model?
    profileLikeTestStat.SetOneSidedDiscovery(True);
    profileLikeTestStat.SetPrintLevel(-1) # higher values provide more output, any value bigger than 3 might apears to give the same result as 3
    profileLikeTestStat.EnableDetailedOutput()

    aToyMCSampler = freqCalculator.GetTestStatSampler()
    aToyMCSampler.SetTestStatistic(profileLikeTestStat)

    fqResult = freqCalculator.GetHypoTest();
    fqResult.Print()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    # asymCalcResult.NullPValue()
    #expectedP0 = ROOT.RooStats.AsymptoticCalculator.GetExpectedPValues(   asymCalcResult.NullPValue(),  asymCalcResult.AlternatePValue(), 0, False)

    #name = "asymptoticSignificance"
    #title = name
    #value    = asymCalcResult.Significance()
    #lowLimit = asymCalcResult.Significance()
    #highLimit = asymCalcResult.Significance()

    name = "asymptoticNullPValue"
    title = name
    value    = fqResult.NullPValue()
    lowLimit = fqResult.NullPValueError()
    highLimit = fqResult.NullPValueError()

    outputRooRealvar = ROOT.RooRealVar( name, title ,value,lowLimit , highLimit)

    return outputRooRealvar

def toyHypoTestInverter(workspace, confidenceLevel = 0.95, drawLimitPlot = False ):
    # get expected upper limits on the parameter of interest using the 'AsymptoticCalculator'
    # provides also +/- n sigma intervals on the expected limits
    # I don't understand this 'AsymptoticCalculator' fully yet, but the expected limits look reasonable 
    # I based this here on the following tutorial: https://roostatsworkbook.readthedocs.io/en/latest/docs-cls.html#


    modelConfig = workspace.obj("ModelConfig") # modelConfig = modelConfig
    data = workspace.data("obsData")

    # setup the cloned modelConfig
    modelConfigClone = modelConfig.Clone( modelConfig.GetName()+"Clone" )
    mcClonePOI = modelConfigClone.GetParametersOfInterest().first()

    #ROOT.RooStats.SetAllConstant( modelConfigClone.GetNuisanceParameters() );
    mcClonePOI.setVal(1.0)
    modelConfigClone.SetSnapshot( ROOT.RooArgSet( mcClonePOI ) )

    #setup the background only model
    bModel = modelConfig.Clone("BackgroundOnlyModel")
    bModelPOI = bModel.GetParametersOfInterest().first()
    bModelPOI.setVal(0)
    bModel.SetSnapshot( ROOT.RooArgSet( bModelPOI )  )

    # https://roostatsworkbook.readthedocs.io/en/latest/docs-cls_toys.html
    freqCalculator = ROOT.RooStats.FrequentistCalculator(data, bModel, modelConfigClone);

    profileLikeTestStat = ROOT.RooStats.ProfileLikelihoodTestStat( modelConfigClone.GetPdf() ) # ? do we need the bModel here, or rather the S+B model?
    profileLikeTestStat.SetOneSided(True);
    profileLikeTestStat.SetPrintLevel(-1) # higher values provide more output, any value bigger than 3 might apears to give the same result as 3
    profileLikeTestStat.EnableDetailedOutput()

    aToyMCSampler = freqCalculator.GetTestStatSampler()
    aToyMCSampler.SetTestStatistic(profileLikeTestStat)
    #aToyMCSampler.SetNEventsPerToy(1); Usually recommended for counting experiments


    freqCalculator.SetToys(20,20) 
    # ((FrequentistCalculator*) hc)->StoreFitInfo(true);
    #


    #   RooStats::ToyMCSampler* toymcs = (RooStats::ToyMCSampler*) freqCalculator.GetTestStatSampler();
    #   toymcs->SetTestStatistic(plr);


    inverter = ROOT.RooStats.HypoTestInverter(freqCalculator)
    inverter.SetConfidenceLevel( confidenceLevel );
    inverter.UseCLs(True);
    inverter.SetVerbose(True);
    inverter.SetFixedScan(20,0.,1.); # set number of points , xmin and xmax

    startHypotestInverter = time.time()
    result =  inverter.GetInterval();
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    reportMemUsage.reportMemUsage(startTime = startHypotestInverter)

    print result.GetExpectedUpperLimit(-2)
    print result.GetExpectedUpperLimit(-1)
    print result.GetExpectedUpperLimit(0)
    print result.GetExpectedUpperLimit(+1)
    print result.GetExpectedUpperLimit(+2)


    drawLimitPlot = True

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if drawLimitPlot: 
        hypoCanvas = ROOT.TCanvas("hypoCanvas", "hypoCanvas", 1300/2,1300/2)
        inverterPlot = ROOT.RooStats.HypoTestInverterPlot("HTI_Result_Plot","HypoTest Scan Result",result);
        inverterPlot.Draw("CLb 2CL");  # plot also CLb and CLs+b
        hypoCanvas.Update()

        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return result

def writeOutWorkspaces(workspace, masspoint , outputDir = None):

    workspace.SetName("combined") # rename so that the workspace conforms with the expectation of StandardHypoTestInv at 
    # https://gitlab.cern.ch/atlas_higgs_combination/software/StandardHypoTestInv 

    modelConfig = workspace.obj("ModelConfig") # modelConfig = modelConfig

    #ROOT.RooStats.SetAllConstant( modelConfigClone.GetNuisanceParameters() );
    mcPOI = modelConfig.GetParametersOfInterest().first()
    mcPOI.setVal(1.0)
    modelConfig.SetSnapshot( ROOT.RooArgSet( mcPOI ) )

    if outputDir is None:  outputDir = "ZXWorkspaces"

    if not os.path.exists(outputDir): os.mkdir(outputDir)


    # tally included datasets, so we can print them out
    includedDataSets = []
    for dataSet in workspace.allData(): includedDataSets.append(dataSet.GetName())


    outputFileName = "ZX_Workspace_mZd_%iGeV.root"%( masspoint )


    outTFile = ROOT.TFile( os.path.join(outputDir,outputFileName) , "RECREATE")
    workspace.Write()
    outTFile.Close()

    print "workspace '%s' written to '%s'. Included datasets: %s" %(workspace.GetName(), os.path.join(outputDir,outputFileName), ", ".join(includedDataSets))

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


def translateLimits( rooStatsObject, nSigmas = 1 , getObservedAsymptotic = False):
    # we assume that there is always only one parameter of interest
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if isinstance( rooStatsObject , ROOT.RooStats.LikelihoodInterval ):
        limitObject = TDirTools.rooArgSetToList( rooStatsObject.GetBestFitParameters() )[0]
        
        bestEstimate = limitObject.getVal()
        lowLimit  = rooStatsObject.LowerLimit( limitObject )
        highLimit = rooStatsObject.UpperLimit( limitObject )

        suffix = "ProfileLikelihoodObserved"

    elif isinstance( rooStatsObject , ROOT.RooStats.HypoTestInverterResult ):
        limitObject = rooStatsObject

        if getObservedAsymptotic:

            bestEstimate = rooStatsObject.UpperLimit()

            lowLimit  = rooStatsObject.UpperLimit()
            highLimit = rooStatsObject.UpperLimit()

            suffix = "observedUpperLimitAsymptotic"

        else: 

            bestEstimate = limitObject.GetExpectedUpperLimit(0)

            lowLimit  = rooStatsObject.GetExpectedUpperLimit(-nSigmas)
            highLimit = rooStatsObject.GetExpectedUpperLimit(+nSigmas)

            # limitObject.UpperLimit() observed upper limit for HypoTestInverterResult

            suffix = "expectedUpperLimitAsymptotic"

    name = limitObject.GetName() +"_"+str(nSigmas) +"SigmaLimit" + "_" + suffix
    title = limitObject.GetTitle() +"_"+str(nSigmas) +"SigmaLimit" + "_" + suffix

    outputRooRealvar = ROOT.RooRealVar( name, title ,bestEstimate,lowLimit , highLimit)
    # get the limits via .getVal(), .getMin(), .getMax()

    return outputRooRealvar

        

def getFullTDirPath(masterDict, region, eventType, systVariation , flavor):

    histName = masterDict[region][eventType][systVariation][flavor].GetName()
    fullTDirPath = region+"/"+eventType+"/"+systVariation+"/"+flavor+"/"+histName

    return fullTDirPath

def setupHistofactoryData(TH1):

    dataObj = ROOT.RooStats.HistFactory.Data()
    dataObj.SetName("data")
    dataObj.SetHisto(TH1)

    return dataObj


def selectSignal( signalTag , physicsProcessList):

    def matchFunction(tag):

        rePattern = re.compile(tag)

        matchList = filter(rePattern.search, physicsProcessList) # Read Note below

        if not isinstance(matchList, list): matchList = [item for item in matchList]

        if len(matchList)>0: return matchList[0]
        else: return None


    signalSampleExact = matchFunction(signalTag)

    if signalSampleExact is None: signalSampleExact = matchFunction("signal")
    if signalSampleExact is None: signalSampleExact = matchFunction("ZZd")

    # selection via difflib
    #signalSampleExact = difflib.get_close_matches( signalSample  , masterDict[region].keys())[0]



    return signalSampleExact

def writeLimitsToCSV( limitDict ):

    import csv

    limitDictKeys = sorted(limitDict.keys())

    headerList = ["signalType"]; headerList.extend(limitDictKeys)
    csvMetaList = []

    for signalKey in  sorted(bestEstimateDict.keys()):

        csvList = [signalKey]
        for limitKey in limitDictKeys:       csvList.append( limitDict[limitKey][signalKey][0] )
        csvMetaList.append(csvList)


    with open('limits.csv', 'w') as file:
        writer = csv.writer(file)
        writer.writerow(headerList)
        for csvLine in csvMetaList: writer.writerow(csvLine)


    limit_exp, limit_obs = 0, 0
    with open ('limits.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for (k,v) in row.items():
                if k == 'bestEstimate':
                    limit_obs = float(v)
                if k == 'expectedLimit':
                    limit_exp = float(v)
    import json
    import numpy as np
    result = {}
    with open('output.json', 'w') as f:
        result['loss'] = limit_obs - limit_exp # let active learning searching for excess
        print(result)
        json.dump(result, f, indent=2)

    return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--inputFileName", type=str, default="preppedHistsV2_mc16ade_1GeVBins.root" ,
        help="name of the .root file that has the input histograms for the limist setting" )

    parser.add_argument("--outputDir", type=str, default=None ,
        help="directory of where to save the output. Default is the direcotry of the .py file" )

    parser.add_argument("--outputFileName", type=str, default=None ,
        help="name of the output file. We'll add .root if necessary" )

    parser.add_argument("--nSystematics", type=int, default=-1 ,
        help="number of systematics to process, setting '--nSystematics -1' processes them all " )

    parser.add_argument("--nIterations", type=int, default=1 ,
        help="number of iterations over all the masspoints " )

    parser.add_argument("--limitType", type=str, default="toys" , 
        choices=["toys","asymptotic","observed", "HypoTestInverter", "writeOutWorkspaces", "asimov", "p0Calculation"],
        help = "Determines what kind of limit setting we do. \
        'observed' provides limtis on the cross section, based on the data provided. \
        'toys' provides expected limits by sampleing histograms from the 'expected data' but requires many iterations and \
        'asymptotic' does so too, but in a well defined asymptotic way that only requires one iteration" )

    parser.add_argument("--flavor", type=str, default="All" , choices=["All", "4e", "2mu2e", "2l2e", "4mu", "2e2mu", "2l2mu"],
        help="name of the output file. We'll add .root if necessary" )

    parser.add_argument( "--skipStatAndTheoryError", default=False, action='store_true' , 
        help = "If this command line option is invoked, we will skip the inclusion of statistical and theory uncertainties" ) 

    parser.add_argument("--nMassPoints", type=int, nargs='*',
        help="list of mass points that we run over " )

    parser.add_argument( "--doPrePostFitImpacts", default=False, action='store_true' , 
        help = "If this command line option is invoked, we will do the calculation of the pre- and post-fit impacts of the nuisance parameters, when limits with the ProfileLikelihoodCalculator" ) 

    parser.add_argument( "--dataToOperateOn", type=str ,  default="expectedData" , 
        help = "Use this to specify the histogram that contains the data, or is interpreted to be containing the data, e.g. 'data' or 'expectedData' " ) 

    args = parser.parse_args()


    startTime = time.time()
    activateATLASPlotStyle()

    doNSystematics = args.nSystematics

    # RooFit command to suppress all the Info and Progress message is below
    # the message are ordered by the following enumeration defined in RooGlobalFunc.h
    # enum MsgLevel { DEBUG=0, INFO=1, PROGRESS=2, WARNING=3, ERROR=4, FATAL=5 } ;
    rooMsgServe = ROOT.RooMsgService.instance()                
    rooMsgServe.setGlobalKillBelow(ROOT.RooFit.WARNING)
    
    inputFileName = args.inputFileName 

    inputTFile = ROOT.TFile(inputFileName,"OPEN")
    masterDict = TDirTools.buildDictTreeFromTDir(inputTFile) # use this dict for an overview of what hists / channels / systematics / flavors are available

    limitType = args.limitType

    # deal with the output file

    if args.outputFileName is None: outputFileName = "limitOutput_"+limitType+".root"
    else:                           outputFileName = args.outputFileName

    if not outputFileName.endswith(".root"): outputFileName += ".root"

    if args.outputDir is not None:
        if not os.path.exists(args.outputDir): os.makedirs(args.outputDir)
        outputFileName = os.path.join(args.outputDir,outputFileName)


    #writeTFile = ROOT.TFile( outputFileName,  "RECREATE")# "UPDATE")


    region = "ZXSR"
    flavor = args.flavor

    if args.nMassPoints is None : massesToProcess =  range(15,56,1)#[30]#range(15,56,5)
    else:                         massesToProcess =  args.nMassPoints
    
    # setup some output datastructures
    overviewHist = ROOT.TH1D("ZX_limit_Overview","ZX_limit_Overview", len(massesToProcess), min(massesToProcess), max(massesToProcess) + 1 ) # construct the hist this way, so that we have a bin for each mass point

    observedLimitGraph    = graphHelper.createNamedTGraphAsymmErrors("observedLimitGraph")
    expectedLimitsGraph_1Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_1Sigma")
    expectedLimitsGraph_2Sigma = graphHelper.createNamedTGraphAsymmErrors("expectedLimits_2Sigma")
    nullHypoThesisPValueGraph = graphHelper.createNamedTGraphAsymmErrors("nullHypoThesisPValueGraph")

    bestEstimateDict   = collections.defaultdict(list)
    upperLimits1SigDict = collections.defaultdict(list)
    upperLimits2SigDict = collections.defaultdict(list)
    expectedLimitDict = collections.defaultdict(list)
    lowLimits1SigDict = collections.defaultdict(list)
    lowLimits2SigDict = collections.defaultdict(list)
    timingDict = collections.defaultdict(list)
    memoryDict = collections.defaultdict(list)

    pullParameterMetaDict = {}
    prePostFitImpactMetaDict = {}


    myHistSampler = sampleTH1FromTH1.histSampler()

    if limitType == "toys":   nIterations = args.nIterations
    else:                     nIterations = 1

    for limitIteration in xrange(nIterations):

        # setup data hist
        dataHistPath = getFullTDirPath(masterDict, region, args.dataToOperateOn , "Nominal",  flavor)
        #dataHistPath = getFullTDirPath(masterDict, region, "expectedData_signal55GeV" , "Nominal",  flavor)
        dataHist = inputTFile.Get( dataHistPath )
        if limitType == "toys" or limitType == "HypoTestInverter" :
            expectedDataHist = inputTFile.Get( dataHistPath )
            dataHist = myHistSampler.sampleFromTH1(expectedDataHist)
        elif limitType == "writeOutWorkspaces":                                                  pass
        elif limitType == "asimov" or limitType == "asymptotic" or limitType == "p0Calculation": pass # asimov dataset, data has been set to the expectation value from backgrounds
        elif limitType == "observed" :                                                           pass # either do asymptotic expected limits, or get real data limits
        else: raise ValueError("specific limittype '%s' has not been implemented" %limitType)

        dataObj = setupHistofactoryData(dataHist) # put things in a HistFactory.Data object to avoit some seg faults

        for massPoint in massesToProcess:

            massPointTime = time.time()

            templatePaths = {}

            # Prep signal sample locations
            signalSampleTag = "ZZd\D+%iGeV" %( massPoint )

            signalSample = selectSignal( signalSampleTag , masterDict[region].keys())



            templatePaths["Signal"]  = getFullTDirPath(masterDict, region, signalSample , "Nominal",  flavor) # region+"/ZZd, m_{Zd} = 35GeV/Nominal/"+flavor+"/ZXSR_ZZd, m_{Zd} = 35GeV_Nominal_All"

            templatePaths["ZZ"]      = getFullTDirPath(masterDict, region, "ZZ" , "Nominal",  flavor)
            templatePaths["H4l"]     = getFullTDirPath(masterDict, region, "H4l" , "Nominal",  flavor)
            templatePaths["reducibleDataDriven"]     = getFullTDirPath(masterDict, region, "reducibleDataDriven" , "Nominal",  flavor)
            templatePaths["VVV_Z+ll"]     = getFullTDirPath(masterDict, region, "VVV_Z+ll" , "Nominal",  flavor)

            templatePaths["Data"]    = dataObj#dataHist

            meas = prepMeasurement(templatePaths, region, flavor, inputFileName, inputTFile, doStatError = not args.skipStatAndTheoryError, doTheoreticalError = not args.skipStatAndTheoryError)

            chan = meas.GetChannel("signalRegion")

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            #One can also create a workspace for only a single channel of a model by supplying that channel:
            # see here for an example:  https://www.nikhef.nl/~vcroft/KaggleFit-Histfactory.html
            hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast(meas)
            #chan.CollectHistograms() #  see here why this is needed: https://root-forum.cern.ch/t/histfactory-issue-with-makesinglechannelmodel/34201
            workspace = hist2workspace.MakeSingleChannelModel(meas, chan)

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            likelihoodLimit = None
            likelihoodLimit_2Sig = None
            likelihoodLimitObserved = None
            nullHypoThesisPValue = None

            if limitType == "asymptotic":
                # from: https://roostatsworkbook.readthedocs.io/en/latest/docs-cls.html

                asymptoticResuls = expectedLimitsAsimov( workspace , drawLimitPlot = False)

                likelihoodLimit = translateLimits(asymptoticResuls, nSigmas = 1)
                likelihoodLimit_2Sig = translateLimits(asymptoticResuls, nSigmas = 2)

                likelihoodLimitObserved = translateLimits( asymptoticResuls, nSigmas = 1 , getObservedAsymptotic = True)

            elif limitType == "p0Calculation":

                nullHypoThesisPValue = p0SignifianceCalculation(workspace)

            elif limitType == "HypoTestInverter":

                toyHypoTestInverter( workspace , drawLimitPlot = False)

            elif limitType == "writeOutWorkspaces":

                writeOutWorkspaces( workspace, massPoint , args.outputDir)

                continue

            else :  # profile limits, for  observed, toys and  asimov limits

                # profile limit: profileLimit.getVal(), profileLimit.getErrorHi(), profileLimit.getErrorLo()
                interval, pullParamDict, prePostFitImpactDict = getProfileLikelihoodLimits(workspace , drawLikelihoodIntervalPlot = False)

                likelihoodLimitObserved = translateLimits( interval, nSigmas = 1 )
                likelihoodLimitObserved.Print()
                #likelihoodLimit_2Sig = translateLimits( interval, nSigmas = 2 )

                pullParameterMetaDict["pullParameters_%iGeV" %massPoint ] = pullParamDict
                prePostFitImpactMetaDict["prePostFitImpact_%iGeV" %massPoint ] = prePostFitImpactDict
                #import pdb; pdb.set_trace()


            graphHelper.fillTGraphWithRooRealVar(observedLimitGraph, massPoint, likelihoodLimitObserved)
            graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_1Sigma, massPoint, likelihoodLimit)
            graphHelper.fillTGraphWithRooRealVar(expectedLimitsGraph_2Sigma, massPoint, likelihoodLimit_2Sig)
            graphHelper.fillTGraphWithRooRealVar(nullHypoThesisPValueGraph, massPoint, nullHypoThesisPValue)



            if likelihoodLimitObserved is not None: bestEstimateDict[signalSample].append( likelihoodLimitObserved.getVal() )
            if likelihoodLimit         is not None: expectedLimitDict[signalSample].append(likelihoodLimit.getVal())
            if likelihoodLimit         is not None: upperLimits1SigDict[signalSample].append(likelihoodLimit.getMax())
            if likelihoodLimit_2Sig    is not None: upperLimits2SigDict[signalSample].append(likelihoodLimit_2Sig.getMax())
            if likelihoodLimit         is not None: lowLimits1SigDict[signalSample].append(likelihoodLimit.getMin())
            if likelihoodLimit_2Sig    is not None: lowLimits2SigDict[signalSample].append(likelihoodLimit_2Sig.getMin())

            reportMemUsage.reportMemUsage(startTime = startTime)
            timingDict["timePerMassPoint_Minutes"].append(  (time.time() - massPointTime)/60 )

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
           
            # let's try delete these objects here to stem the growing memory demand with increasing 'limitIteration' count
            del chan, meas


        ###############################################
        # end of "for massPoint in ... "
        ###############################################

        if limitType != "writeOutWorkspaces":

            reportMemUsage.reportMemUsage(startTime = startTime)

            writeTFile = ROOT.TFile( outputFileName,  "RECREATE")# "UPDATE")
            writeTFile.cd()
            if likelihoodLimitObserved is not None: bestEstimatesTTree   = fillTTreeWithDictOfList(bestEstimateDict, treeName = "bestEstimates_"+limitType)
            if likelihoodLimit         is not None: upperLimits1SigTTree = fillTTreeWithDictOfList(upperLimits1SigDict, treeName = "upperLimits1Sig_"+limitType)
            if likelihoodLimit_2Sig    is not None: upperLimits2SigTTree = fillTTreeWithDictOfList(upperLimits2SigDict, treeName = "upperLimits2Sig_"+limitType)

            if likelihoodLimit         is not None: lowLimits1SigTTree = fillTTreeWithDictOfList(lowLimits1SigDict, treeName = "lowLimits1Sig_"+limitType)
            if likelihoodLimit_2Sig    is not None: lowLimits2SigTTree = fillTTreeWithDictOfList(lowLimits2SigDict, treeName = "lowLimits2Sig_"+limitType)

            calculationTimeTTree = fillTTreeWithDictOfList(timingDict, treeName = "calclationTime")

            memoryDict["RAM_Used_MiB"].append(float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/1024 )
            memoryUsageTTree = fillTTreeWithDictOfList(memoryDict, treeName = "memoryUsage")

            #for pullDictName in pullParameterMetaDict: fillTTreeWithDictOfList( pullParameterMetaDict[pullDictName], treeName = pullDictName )

            # need to put pullTtree in a list to avoid gettim them deleted from the stack before writing out the 
            pullTTreeList = [ fillTTreeWithDictOfList( pullParameterMetaDict[pullDictName], treeName = pullDictName ) for pullDictName in pullParameterMetaDict ]
            fitImpactTTreeList = [ fillTTreeWithDictOfList( prePostFitImpactMetaDict[impactDictName], treeName = impactDictName ) for impactDictName in prePostFitImpactMetaDict if prePostFitImpactMetaDict[impactDictName] is not None]

            observedLimitGraph.Write()
            expectedLimitsGraph_1Sigma.Write()
            expectedLimitsGraph_2Sigma.Write()


            if limitType == "p0Calculation":
                nullHypoThesisPValueGraph.Write()

            
            writeTFile.Write()

            writeTFile.Close()

            #if limitType != "toys":
            #    import plotXSLimits
            #    graphOverviewCanvas = plotXSLimits.makeGraphOverview( graphHelper.getTGraphWithoutError( observedLimitGraph , ySetpoint = "yHigh"), 
            #                                     expectedLimitsGraph_1Sigma, expectedLimitsGraph_2Sigma , colorScheme = ROOT.kRed , writeTo = writeTFile)


    writeLimitsToCSV( {"lowLimit2Sigma" : lowLimits2SigDict, "lowLimit1Sigma" : lowLimits1SigDict, "bestEstimate" : bestEstimateDict, "expectedLimit": expectedLimitDict, "upperLimit1Sigma" : upperLimits1SigDict , "upperLimit2Sigma" : upperLimits2SigDict } )


    ###############################################
    # end of "for limitIteration in xrange(nIterations): "
    ###############################################



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




    reportMemUsage.reportMemUsage(startTime = startTime)

    del dataObj, templatePaths # delete this objects manually and explcitly to avoid a segmentation fault

    print("All Done!")
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

