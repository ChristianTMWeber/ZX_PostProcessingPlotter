#   Short script to create cleaned up cutflow tables, takes cutflow restults as input
#   Run as 
#   python cleanupCutflowTables.py cutflowOnly_post_20190905_233618_ZX_Run2_BckgSignal.root 

# python cleanupCutflowTables.py ../restricedFlavorCombinationRootFiles/post_20200605_171837__ZX_Run2_Bckg_May_4eOnly.root --titleTag 4eOnly --DSIDs 343238 --batch
# python cleanupCutflowTables.py ../restricedFlavorCombinationRootFiles/post_20200605_172229__ZX_Run2_Bckg_May_2Mu2eOnly.root --titleTag 2Mu2eOnly --DSIDs 343238 --batch
# python cleanupCutflowTables.py ../restricedFlavorCombinationRootFiles/post_20200605_172703__ZX_Run2_Bckg_May_2e2MuOnly.root --titleTag 2e2MuOnly --DSIDs 343238 --batch
# python cleanupCutflowTables.py ../restricedFlavorCombinationRootFiles/post_20200611_143715__ZX_Run2_Bckg_May_4MuOnly.root --titleTag 4MuOnly --DSIDs 343238 --batch
# python cleanupCutflowTables.py ../restricedFlavorCombinationRootFiles/post_20200611_112212__ZX_Run2_Bckg_May.root --titleTag NoFlavorRestriction --DSIDs 343238 --batch

import ROOT # to do all the ROOT stuff
import re
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import argparse # to parse command line options


# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.rootDictAndTDirTools as TDirTools

from  plotPostProcess import DSIDHelper

def getQuadType( histName ):

    quadrupletOptionsRE = "4e|2e2m|2m2e|4m"

    quadSearch = re.search(quadrupletOptionsRE, histName)

    if quadSearch: return quadSearch.group()
    else:          return quadSearch


if __name__ == '__main__':

    # Setup command line options

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input file")

    parser.add_argument("--titleTag", type=str, default="", help="tag to add to the histogral title")

    parser.add_argument( "--batch", default=False, action='store_true' , 
    help = "If run with '--batch' we will activate root batch mode and suppress all interactive graphics." ) 

    parser.add_argument("-d", "--metaData", type=str, default="../metadata/md_bkg_datasets_mc16e_All.txt" ,
    help="location of the metadata file for the given mc campaign. If not provided, we will use a default location" )

    parser.add_argument("-c", "--mcCampaign", type=str, choices=["mc16a","mc16d","mc16e","mc16ade"], default="mc16ade",
        help="name of the mc campaign, i.e. mc16a or mc16d, need to provide exactly 1 mc-campaign tag for each input file, \
        make sure that sequence of mc-campaign tags matches the sequence of 'input' strings")

    parser.add_argument( "--scaleToCrossSection", default=False, action='store_true' , 
    help = "If run with '--scaleToCrossSection' we will scale the yield in the cutflow table to the propper cross section,\
            so that the yield in the final bin, corresponds to the signal region yield." ) 

    #parser.add_argument( "--DSIDs", default=None, nargs='*', type=int,
    #help = "List of DSIDs to parse, if not specified, loop over DSIDs in signalDSIDDict" ) 

    args = parser.parse_args()


    ROOT.gROOT.SetBatch( args.batch ) # enact batch mode, if so dictated by commmand line option


    cutFlowTFile = ROOT.TFile(args.input,"OPEN")
    cutflowTDir = cutFlowTFile.Get("Cutflow")


    myDSIDHelper = DSIDHelper()
    myDSIDHelper.importMetaData(args.metaData) # since the DSID helper administrates the meta data for the MC samples we must provide it with the meta data locati
    myDSIDHelper.fillSumOfEventWeightsDict(cutFlowTFile)


    histDict = collections.defaultdict(list) # prepare storage of cutflow histrams in dict of lists like histDict[ "123456" ] = [hist1,hist2]
    outputHists = []

    # gather the cutflow histograms
    for path, myTObject  in TDirTools.generateTDirPathAndContentsRecursive(cutflowTDir, newOwnership = None):  

        objName = myTObject.GetName()

        if "hraw_" in objName: continue
        if not getQuadType( objName ): continue # we only want the 4e, 2e2mu, 2mu2e and 4mu hists, and we skip the the one for 'all' for now

        DSIDmatch = re.search("\d+", objName)

        if DSIDmatch :

            DSID = DSIDmatch.group()
            histDict[DSID].append(myTObject)


    

    for DSID in histDict:

        binNamesAndContentDict = {} # build a mapping between bin labels and the associated bin content

        histList = histDict[DSID]


        # gather information about the first 5 bins, that are common among all the quadruplet flavor types
        hist = histList[0] # pick an arbitrary histogram to 
        quadType = getQuadType( hist.GetName() )
        nBins = hist.GetNbinsX()
        for binNr in range(1,5+1):     binNamesAndContentDict[re.sub(quadType, "", hist.GetXaxis().GetBinLabel(binNr)) ] = hist.GetBinContent(binNr)

        # get information about the remaining bins by adding the contents of all histograms up
        for hist in histList:
            quadType = getQuadType( hist.GetName() )
            for binNr in range(6,nBins+1):
                binLabel = hist.GetXaxis().GetBinLabel(binNr)

                if "ZXVR" in binLabel: continue
                if quadType not in binLabel: continue

                binLabelNoQuadType = re.sub(quadType, "", binLabel)

                if binLabelNoQuadType not in binNamesAndContentDict: binNamesAndContentDict[binLabelNoQuadType] = 0

                binNamesAndContentDict[binLabelNoQuadType] += hist.GetBinContent(binNr)

        


        # make new plot

        nNewBins = len(binNamesAndContentDict)

        th1Title = "cutflow yield for "+ DSID +" sample, " + args.titleTag
        #th1Title = "cutflow yield for "+signalDSIDDict[int(DSID)] +" sample, " + args.titleTag

        newHist = ROOT.TH1D(str(DSID), th1Title, nNewBins, 0, nNewBins)

        counter = 0

        refHist = histList[0]
        quadType = getQuadType( refHist.GetName() )

        for binNr in range(1,refHist.GetNbinsX()+1):
            binLabel = refHist.GetXaxis().GetBinLabel(binNr)
            if "ZXVR" in binLabel: continue

            binLabel_NoQuadMarker = re.sub(quadType, "", binLabel)

            if binLabel_NoQuadMarker in binNamesAndContentDict:
                counter +=1

                newHist.SetBinContent(counter, binNamesAndContentDict[binLabel_NoQuadMarker])

                binLabel_NoQuadMarker = re.sub("ElectronID", "LeptonID", binLabel_NoQuadMarker) # replace "ElectronID" with "LeptonID"
                newHist.GetXaxis().SetBinLabel(counter, binLabel_NoQuadMarker)


        newHist.GetYaxis().SetRangeUser( min(binNamesAndContentDict.values()) * 0.9, max( binNamesAndContentDict.values())*1.1  )
        newHist.GetYaxis().SetTitle("yield after cut")
        if args.scaleToCrossSection: newHist.GetYaxis().SetTitle("yield after cut [events]")

        newHist.GetYaxis().SetTitleSize(newHist.GetYaxis().GetTitleSize() *1.5)
        newHist.GetYaxis().SetTitleOffset(0.75)

        newHist.SetStats( False) # remove stats box

        if args.scaleToCrossSection: newHist.Scale( myDSIDHelper.getMCScale( DSID, mcTag = args.mcCampaign) )

        #for hist in histList[1:]: 
        #    for binNr in range(6,18+1):     binNamesAndContentDict[re.sub(quadType, "", hist.GetXaxis().GetBinLabel(binNr)) ] += hist.GetBinContent(binNr)

            
        outputHists.append(newHist)

        canvas = ROOT.TCanvas("canvas"+str(DSID),"canvas"+str(DSID), 1920, 1080)
        canvas.SetBottomMargin(.15)
        newHist.Draw("TEXT HIST")
        canvas.Update()

        fileEndings = [".png", ".pdf"]
        for fileEnding in fileEndings: canvas.Print(str(DSID)+"_"+ args.titleTag +fileEnding)
        canvas.Close()

    print("All done!")

    #filenameUpToSystematic = re.search("(?:(?!(1down|1up)).)*", myTObject.GetName()).group() # systematics

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

