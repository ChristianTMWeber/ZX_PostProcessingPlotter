import ROOT

import os
import re
import csv
import collections

def gatherIntputROOTFiles(inputDir, relevantInputFileReTag = ".*\.flat\.TTree\.root\.1"):

    outputList = []

    inputDirAbs = os.path.abspath(inputDir)

    for (root,dirs,files) in os.walk(inputDirAbs): 
        for file in files:

            if not re.search(relevantInputFileReTag,file): continue

            outputList.append( os.path.join(root,file) )

    return outputList


def getPhysicsParameterMapping(inputFile):

    outputDict = collections.defaultdict(dict)


    with open(inputFile, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:

            # last set of digits in the spreadsheet are off by 4 w.r.t. to actual file names
            # let's correct that here

            job_split = row["job"].split("_")
            job_split[2] = "%03d" %(int(job_split[2])-4)
            job_corrected = "_".join(job_split)

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            outputDict[job_corrected]["ZdMassGeV"] = row["myparamMZD"]
            outputDict[job_corrected]["epsilon"]   = row["myparamEPSILON"]

    return outputDict


def matchFilesToPhysicsParameters(physicsDict,inputFileList):

    inputFileDict = collections.defaultdict(list)

    physicsKeySearchString = "(" + ")|(".join(physicsDict.keys()) + ")"

    for file in inputFileList:

        matchedPhysicsKey = re.search(physicsKeySearchString,file).group()

        mZd = physicsDict[matchedPhysicsKey]['ZdMassGeV']
        epsilon = physicsDict[matchedPhysicsKey]['epsilon']

        inputFileDict[ (mZd,epsilon)].append(file)

    return inputFileDict


def divide_chunks(l, n):
     
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def defineHistProperties():


    histPropertyDict = collections.defaultdict(dict)

    # histPropertyDict[kinematic][<properties>]
    histPropertyDict["pT"]["nBins"]   = 200
    histPropertyDict["pT"]["lowBin"]  = 0
    histPropertyDict["pT"]["highBin"] = 200
    histPropertyDict["pT"]["units"]   = "(GeV)"


    histPropertyDict["eta"]["nBins"]   = 81
    histPropertyDict["eta"]["lowBin"]  = -8
    histPropertyDict["eta"]["highBin"] = +8
    histPropertyDict["eta"]["units"]   = ""

    histPropertyDict["mInv"]["nBins"]   = 100
    histPropertyDict["mInv"]["lowBin"]  = 0
    histPropertyDict["mInv"]["highBin"] = 115
    histPropertyDict["mInv"]["units"]   = "(GeV)"


    physicsObjectDict = collections.defaultdict(list)

    physicsObjectDict["Zd"] = ["pT","eta"]
    physicsObjectDict["Z"] = ["pT","eta"]
    physicsObjectDict["l1"] = ["pT","eta"]
    physicsObjectDict["l2"] = ["pT","eta"]
    physicsObjectDict["l3"] = ["pT","eta"]
    physicsObjectDict["l4"] = ["pT","eta"]

    physicsObjectDict["ll12"] = ["mInv"]
    physicsObjectDict["ll34"] = ["mInv"]


    return histPropertyDict, physicsObjectDict


def getTPads():

    ZZd_pT_pad  = ROOT.TPad("histPad", "histPad", 0, 2./3, 0.5, 1);
    ZZd_eta_pad = ROOT.TPad("histPad", "histPad", 0.5, 2./3, 1, 1);

    l_pT_pad    = ROOT.TPad("histPad", "histPad", 0, 1./3, 0.5, 2./3);
    l_eta_pad   = ROOT.TPad("histPad", "histPad", 0.5, 1./3, 1, 2./3);

    ll_mInv_pad    = ROOT.TPad("histPad", "histPad", 0, 0, 1, 1./3);

    TPadDict = {}

    TPadDict[("Zd","pT")] = ZZd_pT_pad
    TPadDict[("Z" ,"pT")] = ZZd_pT_pad
    TPadDict[("Zd","eta")] = ZZd_eta_pad
    TPadDict[("Z" ,"eta")] = ZZd_eta_pad


    TPadDict[("l1","pT")] = l_pT_pad
    TPadDict[("l2","pT")] = l_pT_pad
    TPadDict[("l3","pT")] = l_pT_pad
    TPadDict[("l4","pT")] = l_pT_pad

    TPadDict[("l1","eta")] = l_eta_pad
    TPadDict[("l2","eta")] = l_eta_pad
    TPadDict[("l3","eta")] = l_eta_pad
    TPadDict[("l4","eta")] = l_eta_pad

    TPadDict[("ll12","mInv")] = ll_mInv_pad
    TPadDict[("ll34","mInv")] = ll_mInv_pad


    for pad in TPadDict.values(): ROOT.SetOwnership(pad, False) # Do this

    return TPadDict

def getZdEpsilonString(mZd,epsilon):

    mZdFixPrec     = "%2.2f"%float(mZd)
    epsilonSciNota = "%1.2e" %float(epsilon)

    return mZdFixPrec, epsilonSciNota


def defineHist(mZd,epsilon, histPropertyDict, physicsObjectDict ):

    mZdFixPrec, epsilonSciNota = getZdEpsilonString(mZd,epsilon)


    histDict = collections.defaultdict(dict)


    kinematicsReplacements = {}

    kinematicsReplacements["mInv"] = "m_{ll}"


    for physicsObjs in physicsObjectDict:
        for kinematic in physicsObjectDict[physicsObjs]:

            histName = "%s_%s_test_mZd%s_epsilon%s" %(physicsObjs, kinematic,mZdFixPrec,epsilonSciNota)
            histTitle = "m_{Z_{d}} = %s, #varepsilon = %s, %s distribution" %(mZdFixPrec,epsilonSciNota, kinematic)

            histProperties = histPropertyDict[kinematic]

            lowBin  = histProperties["lowBin"]
            highBin = histProperties["highBin"]

            hist = ROOT.TH1F(histName,histTitle,histProperties["nBins"], lowBin,  highBin)
            hist.SetStats( False) # remove stats box


            #hist.AddDirectory(ROOT.kFALSE) # prevent histograms from being added to the current directory, see https://root.cern/manual/object_ownership/

            kinematicLabel = kinematicsReplacements.get(kinematic,kinematic)

            hist.GetXaxis().SetTitle("%s %s" %(kinematicLabel,histProperties["units"]) )
            

            #                % draw command
            histDict[histName]["hist"] = hist
            histDict[histName]["drawCommand"] = "%s_%s >> %s" % (physicsObjs,kinematic ,histName)
            histDict[histName]["legendStr"] = "m_{Z_{d}} = %s, #varepsilon = %s" %(mZdFixPrec, epsilonSciNota)

            histDict[histName]["physKinSet"] =  (physicsObjs,kinematic)

            #ROOT.SetOwnership(hist,True)

    #Zd_pT_Hist = ROOT.TH1D("Zd_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
    #Zd_pT_Hist.GetXaxis().SetTitle("Z_{d} pT (GeV)")

    return histDict


def getTChain( listOfFiles, TTreeName):

    myTChain = ROOT.TChain(TTreeName)

    for file in listOfFiles: myTChain.Add(file)


    #ROOT.gROOT.cd()



    #TFile = ROOT.TFile("/workdir/Downloads/evntTTree/user.zhangr.sqlp_ZZ32_000_inner_work_evgen.1_EVNT.pool.root.1/DAOD_TRUTH1.user.zhangr.31074559._000001.flat.TTree.root.1","OPEN")
    #TTree = TFile.Get("truthTree_Zd")
    #canv = ROOT.TCanvas()
    #hist = ROOT.TH1F("ABCD","ABC",100, 0, 100)
    #TTree.Draw("Zd_pT >> ABCD")
    #canv.Update()
    #mass =1
    #Zd_pT_Hist = ROOT.TH1D("Zd_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
    #Zd_pT_Hist.GetXaxis().SetTitle("Z_{d} pT (GeV)")
    #myTChain.Draw(" Zd_pT >> Zd_pT_Hist%i" %mass)
    #myTChain.Draw(" Zd_pT >> hHist")
    #hist = ROOT.TH1D("test","test",100, 0,700)
    #myTChain.Draw("l2_pT >> test")
    ##hist.Print("Print.pdf")
    #canv = ROOT.TCanvas()
    #hist.Draw()
    #canv.Update()
    #canv.Print("Print.pdf")

    return myTChain


def setupTLegend( nColumns = 1, boundaries = (0.15,0.70,0.55,0.95)):
    # set up a TLegend, still need to add the different entries
    # boundaries = (lowLimit X, lowLimit Y, highLimit X, highLimit Y)

    TLegend = ROOT.TLegend(boundaries[0],boundaries[1],boundaries[2],boundaries[3])
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(nColumns);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border

    ROOT.gStyle.SetLegendTextSize(0.038)

    return TLegend


def printRootCanvasPDF(myRootCanvas, isLastCanvas, fileName, tableOfContents = None):
    if fileName is None:  fileName = myRootCanvas.GetTitle() + ".pdf"

    # it is not the last histogram in the TFile
    if not isLastCanvas: fileName += "("
    # close the pdf if it is the last histogram
    else:                fileName += ")"
    # see for alternatives to these brackets here: https://root.cern.ch/doc/master/classTPad.html#abae9540f673ff88149c238e8bb2a6da6


    if tableOfContents is None: myRootCanvas.Print(fileName)
    else: myRootCanvas.Print(fileName, "Title:" + tableOfContents)

    return None





if __name__ == '__main__':


    TFile = ROOT.TFile("/workdir/Downloads/evntTTree/user.zhangr.sqlp_ZZ32_000_inner_work_evgen.1_EVNT.pool.root.1/DAOD_TRUTH1.user.zhangr.31074559._000001.flat.TTree.root.1","OPEN")
    TTree = TFile.Get("truthTree_Zd")


    #ROOT.gROOT.cd()
    #canv = ROOT.TCanvas()
    #hist = ROOT.TH1F("ABCD","ABCD",100, 0, 100)
    #TTree.Draw("Zd_pT >> ABCD")
    #canv.Update()
    #print(hist.Integral())
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    physicsDict = getPhysicsParameterMapping("allresults.csv")


    #inputTTreeDir =  "/gpfs/mnt/atlasgpfs01/usatlas/data/chweber/ReanaActiveLearningProject/generatedZXSamples/evnt"

    inputTTreeDir =  "/workdir/Downloads/evntTTree"

    inputFileList = gatherIntputROOTFiles(inputTTreeDir, relevantInputFileReTag = ".*\.flat\.TTree\.root\.1")


    physicsAndIntputFileDict = matchFilesToPhysicsParameters(physicsDict,inputFileList)

    massAndEpsilonList = list(physicsAndIntputFileDict.keys())

    massAndEpsilonList.sort( key = lambda x: x[1] , reverse = False)

    massAndEpsilonList.sort( key = lambda x: x[0] , reverse = False)




    massAndEpsilonListBatches = [chunk for chunk in divide_chunks(massAndEpsilonList, 3)]




    #TFile = ROOT.TFile("ZX_CombinedTruthTTree4.root", "OPEN")


    ROOT.gROOT.SetBatch(True)



    histPropertyDict, physicsObjectDict = defineHistProperties()

    canvasList = []
    canvasDict = collections.defaultdict(dict)
    legendList = []

    counter = 0

    for Zd_epsilon_batch in massAndEpsilonListBatches:

        histDict = {}

        for Zd, epsilon in Zd_epsilon_batch:


            Zd_epsilonSet = getZdEpsilonString(Zd,epsilon)


            # define hists

            histDict[ (Zd,epsilon)] = defineHist(Zd,epsilon, histPropertyDict, physicsObjectDict )

            currentHistSet = histDict[ (Zd,epsilon)]
            setOfFiles = physicsAndIntputFileDict[ (Zd,epsilon)]
            TChain = getTChain( setOfFiles, "truthTree_Zd")





            for histName in currentHistSet: # get hists from the TChain

                hist = currentHistSet[histName]["hist"]

                drawCommand = currentHistSet[histName]["drawCommand"]

                TChain.Draw(drawCommand,"mcEventWeight")



            canvasName = "_".join(Zd_epsilonSet)+"_canv"

            canvas = ROOT.TCanvas(canvasName,canvasName, 1600,1600)


            TPadDict = getTPads()

            # map TPads to list of maximum Y-values in the histogrmas associated with it
            maxYValueMap = collections.defaultdict(list)

            for histName in currentHistSet: # find the maximum y-value per histogram

                hist = currentHistSet[histName]["hist"]

                TPad = TPadDict[currentHistSet[histName]["physKinSet"]]

                maxYValueMap[TPad].append(hist.GetMaximum())



            TPadCountDict = {}
            TPadLegendDict = {}


            for histName in currentHistSet: # plot all the hists on the TCanvas

                hist = currentHistSet[histName]["hist"]

                currentTPad = TPadDict[currentHistSet[histName]["physKinSet"]]

                TPadCount = TPadCountDict.get(currentTPad,0)
                TPadCountDict[currentTPad] = TPadCount+1

                maxYVal = max(  maxYValueMap[currentTPad] )

                hist.GetYaxis().SetRangeUser(0, maxYVal * 1.1)

                hist.SetLineColor(TPadCount+1)
                hist.SetLineStyle(TPadCount+1)
                hist.SetLineWidth(2)

                canvas.cd()

                currentTPad.cd()

                hist.Draw("HIST same")




                legend = TPadLegendDict.get(currentTPad, setupTLegend( nColumns = 1, boundaries = (0.7,0.60,1.,0.85)))
                if currentTPad not in TPadLegendDict: TPadLegendDict[currentTPad] = legend

                physicsObject = currentHistSet[histName]["physKinSet"][0]

                legend.AddEntry( hist , physicsObject , "l" )


                
                canvas.cd()
                currentTPad.Draw()
                canvas.Update()

            for TPad in TPadLegendDict: # draw legends

                TPad.cd()

                legend = TPadLegendDict[TPad]

                legend.Draw()

            canvas.cd()
            canvas.Update()


            filePrefix = "mZd %s, epsilon %s" %(Zd_epsilonSet)


            canvas.Print("ReanaZXTruthSignals/%s.pdf" %filePrefix)
            canvas.Print("ReanaZXTruthSignals/%s.jpg" %filePrefix)


            canvasDict[canvas]["legendStr"] = currentHistSet[histName]["legendStr"]

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here




    #counter = 0
    #for canvas in canvasList:
    #    counter +=1
    #    printRootCanvasPDF(canvas, isLastCanvas = canvas==canvasList[-1] , 
    #    fileName = "ReanaZXTruthSignals.pdf", tableOfContents = str(counter) + " - " + canvasDict[canvas]["legendStr"] ) # write to .PDF




    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here