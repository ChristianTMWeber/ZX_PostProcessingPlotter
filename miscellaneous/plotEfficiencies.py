import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly


import re # regular expressions for pattern matching


# import sys and os.path to be able to import plotPostProcess from the parent directory
import sys 
import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper

import showZX_FiducialNumbers as fiducialNumbers
import plotPostProcess 
import limitSetting.limitFunctions.makeHistDict as makeHistDict # alternative option to fill the  masterHistDict
import limitSetting.limitFunctions.reportMemUsage as reportMemUsage # alternative option to fill the  masterHistDict



def gatherHists(fileLocation,altMasterHistDict):


    myDSIDHelper = plotPostProcess.DSIDHelper()
    #myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati

    DSIDsToConsider = myDSIDHelper.physicsProcessSignalByDSID.keys() # ZX and other signals, we are only interetested in ZX, but only .root file should only have ZX, so we are good

    systematicsTags = "" # this way we tag all the systematics

    mcCampaign = None

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    postProcessedData = ROOT.TFile(fileLocation,"READ"); # open the file with te data from the ZdZdPostProcessing

    histCounter = 0
    
    for path, baseHist in plotPostProcess.preselectTDirsForProcessing(postProcessedData, permittedDSIDs = DSIDsToConsider, systematicsTags = systematicsTags, systematicsVetoes = ["UncorrUncertaintyNP" ,"CorrUncertaintyNP" ,"PMG_"]):

        if plotPostProcess.irrelevantTObject(path, baseHist): continue # skip non-relevant histograms

        if "ZXSR" not in baseHist.GetName(): continue
        if "m34" not in baseHist.GetName(): continue

        makeHistDict.fillHistDict(path, baseHist , mcCampaign, myDSIDHelper, channelMap = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZXVR1" , "ZXVR2" : "ZXVR2", "ZXVR1a":"ZXVR1a" } , customMapping = myDSIDHelper.physicsProcessSignalByDSID, doScaling = False, masterHistDict = altMasterHistDict) 

        histCounter += 1
        if histCounter %100 == 0: 
            print str(histCounter) #+ " relevant hists processed. \t Memory usage: %s (MB)" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000)
            reportMemUsage.reportMemUsage()


        


    return altMasterHistDict


def produceRecoYieldsWithUncert(altMasterHistDict):

    recoYields = collections.defaultdict(lambda: collections.defaultdict(dict))

    for signal in sorted(altMasterHistDict["ZXSR"].keys()):
        for flavor in altMasterHistDict["ZXSR"][signal]["Nominal"].keys():

            nominalHist = altMasterHistDict["ZXSR"][signal]["Nominal"][flavor]

            nominalYield, statUncert = plotPostProcess.getHistIntegralWithUnertainty(nominalHist)

            for syst in altMasterHistDict["ZXSR"][signal].keys() : syst, altMasterHistDict["ZXSR"][signal][syst][flavor].Integral() - nominalYield

            upSysYield, downSysYield = plotPostProcess.make1UpAnd1DownSystVariationYields(  altMasterHistDict["ZXSR"][signal]  , flavor = flavor, nominalHist = nominalHist, includeStatUncertainty = False)

            recoYields[signal][flavor]["yield"]      = nominalYield
            recoYields[signal][flavor]["statUncert"] = statUncert
            recoYields[signal][flavor]["systUp"]     = upSysYield
            recoYields[signal][flavor]["systDown"]   = downSysYield

    return recoYields

def unifyDictKeys( inputDict ):

    for key in inputDict.keys(): 
        mass = re.search("\d+", key ).group()
        inputDict[int(mass)] = inputDict.pop(key)

    return None


def makeEfficiencyGraphs(recoYields, fiducialYieldHists):

    efficiencyGraphDict = collections.defaultdict(dict)

    for flavor in recoYields.values()[0].keys(): 

        efficiencyGraphStatError = ROOT.TGraphAsymmErrors()
        efficiencyGraphStatSyst = ROOT.TGraphAsymmErrors()
        efficiencyGraphNoUncert = ROOT.TGraph()

        efficiencyGraphDict[flavor.lower()]["stat"] = efficiencyGraphStatError
        efficiencyGraphDict[flavor.lower()]["syst"] = efficiencyGraphStatSyst
        efficiencyGraphDict[flavor.lower()]["noUncert"] = efficiencyGraphNoUncert

        graphPointCounter = 0

        for mass in sorted(recoYields.keys()): 

            fiducialYield = fiducialYieldHists[mass][flavor.lower()]

            efficiency  = recoYields[mass][flavor]['yield'] / fiducialYield
            statUncert  = recoYields[mass][flavor]['statUncert'] / fiducialYield
            systUp  = recoYields[mass][flavor]['systUp'] / fiducialYield
            systDown  = recoYields[mass][flavor]['systDown'] / fiducialYield


            efficiencyGraphStatError.SetPoint( graphPointCounter, mass, efficiency)
            efficiencyGraphStatError.SetPointError( graphPointCounter, 0,0, statUncert,  statUncert )

            efficiencyGraphStatSyst.SetPoint( graphPointCounter, mass, efficiency)
            efficiencyGraphStatSyst.SetPointError( graphPointCounter, 0,0, abs(systDown),  systUp )

            efficiencyGraphNoUncert.SetPoint( graphPointCounter, mass, efficiency)

            graphPointCounter += 1


    return efficiencyGraphDict

if __name__ == '__main__':

    #file = ROOT.TFile( "ZX_FiducialCombined_HiggsTagged.root","OPEN")
    #file = ROOT.TFile( "ZX_FiducialCombined.root","OPEN")
    file = ROOT.TFile( "ZX_Fiducial_mc16ade_HiggsWindow.root","OPEN")


    fiducialYieldHists = fiducialNumbers.castFiducialYieldHistsToDict("ZX_Fiducial_mc16ade_HiggsWindowV3.root")


    myDSIDHelper = plotPostProcess.DSIDHelper()
    #myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati

    DSIDsToConsider = myDSIDHelper.physicsProcessSignalByDSID.keys() # ZX and other signals, we are only interetested in ZX, but only .root file should only have ZX, so we are good
    systematicsTags = "" # this way we tag all the systematics
    mcCampaign = None

    postProcessedData = ROOT.TFile("../post_20210515_222830_mc16ade_ZX_Run2_SignalBackgroundDataFeb2020Unblinded_VRSyst.root","READ"); # open the file with te data from the ZdZdPostProcessing

    histCounter = 0
    
    for path, baseHist in plotPostProcess.preselectTDirsForProcessing(postProcessedData, permittedDSIDs = DSIDsToConsider, systematicsTags = systematicsTags, systematicsVetoes = ["UncorrUncertaintyNP" ,"CorrUncertaintyNP" ,"PMG_"],newOwnership = True):

        if plotPostProcess.irrelevantTObject(path, baseHist): continue # skip non-relevant histograms
        if "ZXSR" not in baseHist.GetName(): continue
        if "m34" not in baseHist.GetName(): continue

        altMasterHistDict = makeHistDict.fillHistDict(path, baseHist , mcCampaign, myDSIDHelper, channelMap = { "ZXSR" : "ZXSR" , "ZXVR1" : "ZXVR1" , "ZXVR2" : "ZXVR2", "ZXVR1a":"ZXVR1a" } ,  customMapping = myDSIDHelper.physicsProcessSignalByDSID, doScaling = False) 

        histCounter += 1
        if histCounter %100 == 0: 
            print str(histCounter) #+ " relevant hists processed. \t Memory usage: %s (MB)" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000)
            reportMemUsage.reportMemUsage()


    makeHistDict.add2l2eAnd2l2muHists(altMasterHistDict)

    recoYields = produceRecoYieldsWithUncert(altMasterHistDict)

    # change keys for releveant dicts

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    unifyDictKeys( recoYields )
    unifyDictKeys( fiducialYieldHists )


    efficiencyGraphDict = makeEfficiencyGraphs(recoYields, fiducialYieldHists)

    
    for flavor in efficiencyGraphDict.keys():
        for uncertType in efficiencyGraphDict[flavor].keys():
            efficiencyGraphDict[flavor][uncertType].GetYaxis().SetRangeUser( 0, 0.9)
            efficiencyGraphDict[flavor][uncertType].GetXaxis().SetTitle("m_{Z_{d}} [GeV]")


            efficiencyGraphDict[flavor][uncertType].GetYaxis().SetTitle("Efficiency [unitless]")
            efficiencyGraphDict[flavor][uncertType].GetYaxis().SetTitleSize(0.05)
            efficiencyGraphDict[flavor][uncertType].GetYaxis().SetTitleOffset(0.8)
            efficiencyGraphDict[flavor][uncertType].GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
            efficiencyGraphDict[flavor][uncertType].GetXaxis().SetTitleSize(0.05)
            efficiencyGraphDict[flavor][uncertType].GetXaxis().SetTitleOffset(0.85)

            if uncertType is not "noUncert":
                efficiencyGraphDict[flavor][uncertType].SetLineColorAlpha(1,0.) # In the legend the unceratinty logo has a black outline, in the figure it does not. This harmonizes it


    efficiencyGraphDict["2l2mu"]["stat"].SetFillColorAlpha(ROOT.kBlue, 0.2)
    efficiencyGraphDict["2l2mu"]["syst"].SetFillColorAlpha(ROOT.kBlue, 0.2)
    efficiencyGraphDict["2l2mu"]["noUncert"].SetLineColor(ROOT.kBlue)
    efficiencyGraphDict["2l2mu"]["noUncert"].SetFillColorAlpha(ROOT.kBlue, 0.2)
    efficiencyGraphDict["2l2mu"]["noUncert"].SetLineStyle(3)

    efficiencyGraphDict["2l2e"]["stat"].SetFillColorAlpha(ROOT.kRed, 0.2)
    efficiencyGraphDict["2l2e"]["syst"].SetFillColorAlpha(ROOT.kRed, 0.2)
    efficiencyGraphDict["2l2e"]["noUncert"].SetLineColor(ROOT.kRed)
    efficiencyGraphDict["2l2e"]["noUncert"].SetFillColorAlpha(ROOT.kRed, 0.2)
    efficiencyGraphDict["2l2e"]["noUncert"].SetLineStyle(2)

    efficiencyGraphDict["all"]["stat"].SetFillColorAlpha(ROOT.kBlack, 0.2)
    efficiencyGraphDict["all"]["syst"].SetFillColorAlpha(ROOT.kBlack, 0.2)
    efficiencyGraphDict["all"]["noUncert"].SetLineColor(ROOT.kBlack)
    efficiencyGraphDict["all"]["noUncert"].SetFillColorAlpha(ROOT.kBlack, 0.2)
    efficiencyGraphDict["all"]["noUncert"].SetLineStyle(1)

    graphList = []

    for flavor in efficiencyGraphDict:
        for uncertainty in efficiencyGraphDict[flavor]:
            efficiencyGraphDict[flavor][uncertainty].SetName( flavor + "_" + uncertainty );
            efficiencyGraphDict[flavor][uncertainty].SetTitle( flavor + "_" + uncertainty )
            graphList.append(efficiencyGraphDict[flavor][uncertainty])



    canvas = fiducialNumbers.prepCanvas("efficacy")
    legend = fiducialNumbers.setupTLegend()
    

    #efficiencyGraphDict["2l2mu"]["syst"].Draw("A3")
    efficiencyGraphDict["2l2mu"]["stat"].Draw("A3")
    efficiencyGraphDict["2l2mu"]["noUncert"].Draw("same")


    #efficiencyGraphDict["2l2e"]["syst"].Draw("3 same")
    efficiencyGraphDict["2l2e"]["stat"].Draw("3 same")
    efficiencyGraphDict["2l2e"]["noUncert"].Draw("same")


    #efficiencyGraphDict["all"]["syst"].Draw("3 same")
    efficiencyGraphDict["all"]["stat"].Draw("3 same")
    efficiencyGraphDict["all"]["noUncert"].Draw("same")

    legend.AddEntry( efficiencyGraphDict["2l2mu"]["noUncert"]   , "4#mu, 2e2#mu final states"  , "lf");
    legend.AddEntry( efficiencyGraphDict["all"]["noUncert"]   , "4#mu, 2e2#mu, 2#mu2e, 4e final states"  , "lf");
    legend.AddEntry( efficiencyGraphDict["2l2e"]["noUncert"]  , "2#mu2e, 4e final states"  , "lf");

    legend.Draw()
    atlasBlurb = fiducialNumbers.addATLASBlurp("") 

    canvas.Update()

    canvas.Print("efficiencyOverview.pdf")
    canvas.Print("efficiencyOverview.root")



    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

