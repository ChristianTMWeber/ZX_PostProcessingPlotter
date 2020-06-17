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




if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input file")

    parser.add_argument("--titleTag", type=str, default="", help="tag to add to the histogral title")

    parser.add_argument( "--batch", default=False, action='store_true' , 
    help = "If run with '--batch' we will activate root batch mode and suppress all interactive graphics." ) 

    parser.add_argument( "--DSIDs", default=None, nargs='*', type=int,
    help = "List of DSIDs to parse, if not specified, loop over DSIDs in signalDSIDDict" ) 

    args = parser.parse_args()


    ROOT.gROOT.SetBatch( args.batch )


    signalDSIDDict = { 343234 : "m_{Zd} = 15GeV" ,   343235 : "m_{Zd} = 20GeV" ,
                       343236 : "m_{Zd} = 25GeV" ,   343237 : "m_{Zd} = 30GeV" ,
                       343238 : "m_{Zd} = 35GeV" ,   343239 : "m_{Zd} = 40GeV" ,
                       343240 : "m_{Zd} = 45GeV" ,   343241 : "m_{Zd} = 50GeV" ,
                       343242 : "m_{Zd} = 55GeV" }


    if args.DSIDs is None: DSIDs = signalDSIDDict.keys()
    else:                  DSIDs = args.DSIDs

    cutFlowTFile = ROOT.TFile(args.input,"OPEN")

    signalDSIDStrings = [str(DSID) for DSID in signalDSIDDict]
    signalDSID_REString = "|".join(signalDSIDStrings)


    quadrupletOptionsRE = "4e|2e2m|2m2e|4m"


    histDict = collections.defaultdict(list)
    outputHists = []


    for path, myTObject  in TDirTools.generateTDirPathAndContentsRecursive(cutFlowTFile, newOwnership = None):  

        objName = myTObject.GetName()

        reSearchObj = re.search(signalDSID_REString, objName)


        if reSearchObj : 

            #if re.search(signalDSID_REString, objName)

            if "hraw_" in objName: continue

            if re.search(quadrupletOptionsRE, objName): histDict[reSearchObj.group()].append(myTObject)



    namesAndContentDict = {}

    for DSID in DSIDs:

        histList = histDict[str(DSID)]

        hist = histList[0]

        quadType = re.search(quadrupletOptionsRE, hist.GetName()).group()

        nBins = hist.GetNbinsX()

        for binNr in range(1,5+1):     namesAndContentDict[re.sub(quadType, "", hist.GetXaxis().GetBinLabel(binNr)) ] = hist.GetBinContent(binNr)
        for binNr in range(6,nBins+1):
            binLabel = hist.GetXaxis().GetBinLabel(binNr)

            if "ZXVR" in binLabel: continue

            if quadType in binLabel: namesAndContentDict[re.sub(quadType, "", binLabel) ] = hist.GetBinContent(binNr)


        for hist in histList[1:]:
            quadType = re.search(quadrupletOptionsRE, hist.GetName()).group()
            for binNr in range(6,nBins+1):
                binLabel = hist.GetXaxis().GetBinLabel(binNr)
                if "ZXVR" in binLabel: continue

                if quadType in binLabel: 

                    namesAndContentDict[re.sub(quadType, "", binLabel) ] += hist.GetBinContent(binNr)

        # make new plot

        nNewBins = len(namesAndContentDict)

        th1Title = "cutflow yield for "+signalDSIDDict[int(DSID)] +" sample, " + args.titleTag

        newHist = ROOT.TH1D(str(DSID), th1Title, nNewBins, 0, nNewBins)

        counter = 0

        refHist = histList[0]
        quadType = re.search(quadrupletOptionsRE, refHist.GetName()).group()

        for binNr in range(1,refHist.GetNbinsX()+1):
            binLabel = refHist.GetXaxis().GetBinLabel(binNr)
            if "ZXVR" in binLabel: continue

            binLabel_NoQuadMarker = re.sub(quadType, "", binLabel)

            
            if binLabel_NoQuadMarker in namesAndContentDict:
                counter +=1

                newHist.SetBinContent(counter, namesAndContentDict[binLabel_NoQuadMarker])

                binLabel_NoQuadMarker = re.sub("ElectronID", "LeptonID", binLabel_NoQuadMarker) # replace "ElectronID" with "LeptonID"
                newHist.GetXaxis().SetBinLabel(counter, binLabel_NoQuadMarker)


        newHist.GetYaxis().SetRangeUser( min(namesAndContentDict.values()) * 0.9, max( namesAndContentDict.values())*1.1  )
        newHist.GetYaxis().SetTitle("yield after cut")

        newHist.GetYaxis().SetTitleSize(newHist.GetYaxis().GetTitleSize() *1.5)
        newHist.GetYaxis().SetTitleOffset(0.75)

        newHist.SetStats( False) # remove stats box

        #for hist in histList[1:]: 
        #    for binNr in range(6,18+1):     namesAndContentDict[re.sub(quadType, "", hist.GetXaxis().GetBinLabel(binNr)) ] += hist.GetBinContent(binNr)

            
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

