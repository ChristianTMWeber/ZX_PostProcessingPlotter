import ROOT
import math
import copy
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re

def getRooRealVarFromTree( branchName, relevantTTree ):
    return ROOT.RooRealVar(branchName,branchName, math.floor(relevantTTree.GetMinimum(branchName)), math.ceil(relevantTTree.GetMaximum(branchName)))


def getTTreeLocations():

    shapeSourceFiles = { "HeavyFlavor" : "post_20200228_203930__ZX_Run2_ZJetBFilter_May_Minitree.root", 
                         "ttBar"       : "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root",
                         "3l+X"        : "post_20200319_122149__ZX_Run2_Data_May_3lX_Minitree.root"      }
                         
    return shapeSourceFiles


def getZXTTree( shapeType, treeName = "t_ZXTree"):

    shapeSourceFiles = getTTreeLocations()

    fileName = shapeSourceFiles[shapeType]

    aTFile = ROOT.TFile(fileName, "OPEN")
    aTTree = aTFile.Get(treeName)

    ROOT.SetOwnership(aTFile, False)  # we change the ownership here to False in the attempt to prevent deletion
    ROOT.SetOwnership(aTTree, False)  # we change the ownership here to False in the attempt to prevent deletion

    return aTTree



def getShapeRooDataSetAndIndepVar(ZXTTree, finalState, m34 = None):

    ### Setup variables for RooDataSet etc.

    if m34 is None:
        m34 = getRooRealVarFromTree( "llll_m34", ZXTTree )
        m34.setMax(115000)
        m34.setMin(12000)

    m4l = getRooRealVarFromTree( "llll_m4l", ZXTTree )

    weight = getRooRealVarFromTree( "weight", ZXTTree )
    weight.setMin(0)

    decayChannel = getRooRealVarFromTree( "decayChannel", ZXTTree )

    # and put the into sets and lists, as needed by the different Root Methods beliw
    anArgSet = ROOT.RooArgSet(m34, weight, m4l, decayChannel)
    anArgList = ROOT.RooArgList(anArgSet)

    # decay channel 1 <-> 4mu
    #               2 <-> 2e2mu
    #               3 <-> 2mu2e
    #               4 <-> 4e

    if   finalState == "llmumu": decaySetting = "decayChannel <= 2"
    elif finalState == "llee"  : decaySetting = "decayChannel >= 3"

    aFormula = ROOT.RooFormulaVar("cuts"," llll_m4l > 115000 && llll_m4l < 130000 &&  " + decaySetting, anArgList) #  &&       


        #ZXTTree.GetMinimum("mc_channel_number") ZXTTree.GetMaximum("mc_channel_number")

    if ZXTTree.GetMaximum("mc_channel_number") < 1.: 
        print("Data Sample detected, omitting weights")
        aDataSet   = ROOT.RooDataSet("h4lData", "h4lData", ZXTTree, anArgSet, aFormula)
    else: aDataSet = ROOT.RooDataSet("h4lData", "h4lData", ZXTTree, anArgSet, aFormula, "weight")


    # m34 is here the independent variable
    return aDataSet, m34


def th1HistMevToGeV(inHist):
    # returns a TH1 whose x-axis scape has been reduced by a factor of 10^3

    nBins = inHist.GetNbinsX()

    minBin = inHist.GetBinLowEdge(1)/1000
    maxBin = inHist.GetBinLowEdge(nBins+1)/1000

    newName = inHist.GetName()+"_GeV"
    newTitle = inHist.GetTitle()+"_GeV"

    if   isinstance(inHist, ROOT.TH1D): outHist = ROOT.TH1D(newName, newTitle, nBins, minBin, maxBin)
    elif isinstance(inHist, ROOT.TH1D): outHist = ROOT.TH1F(newName, newTitle, nBins, minBin, maxBin)
    else:                               outHist = ROOT.TH1D(newName, newTitle, nBins, minBin, maxBin)


    for bin in xrange(0,nBins+2): outHist.SetBinContent(bin, inHist.GetBinContent(bin) )

    return outHist 



def addPDFs(pdf1, pdf2, pdf1Weight, addPDFName = "addPdf"):

    pdfWeight = ROOT.RooRealVar(addPDFName+"_weight", addPDFName+"_weight", pdf1Weight, 0.,1.)

    addPDF = ROOT.RooAddPdf(addPDFName, addPDFName, pdf1 ,   pdf2, pdfWeight )

    return addPDF


def makeRooKeysPDFs():

    ## llmumu shapes are from Z+HeavyFlavor and ttbar MC 
    ## llee   shapes are from Z+HeavyFlavor MC and 3l+X 

    #fileName = "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root"

    #  pdfDict[finalState][shapeType] = RooKeysPdf
    #   e.g. pdfDict[ "llmumu" ][ "HeavyFlavor" ] = RooKeysPdf
    pdfDict = collections.defaultdict(lambda: collections.defaultdict(dict))


    # we need a common independentVariable for all PDFs, so that we can add them etc. That's why we define it here
    m34 = ROOT.RooRealVar( "llll_m34", "llll_m34", 12000 , 115000 )

    shapeSourceFiles = getTTreeLocations()

    for finalState in [ "llee", "llmumu"]:

        for shapeType in shapeSourceFiles:

            aTTree = getZXTTree( shapeType )

            aDataSet, _ = getShapeRooDataSetAndIndepVar(aTTree, finalState, m34)

            pdfName = "PDF_"+shapeType+"_"+finalState

            #kest1 = ROOT.RooKeysPdf("kest1", "kest1", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            #kest2 = ROOT.RooKeysPdf("kest2", "kest2", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            kest3 = ROOT.RooKeysPdf(pdfName, pdfName, m34, aDataSet, ROOT.RooKeysPdf.MirrorBoth)#                        ROOT.RooKeysPdf.MirrorBoth)

            pdfDict[finalState][shapeType] = kest3

    return pdfDict, m34



def getReducibleTH1s():

    nBins = 100

    convertXAxisFromMeVToGeV = False

    # reducible background in final states, 115<m4l<130
    # 4mu: 2.29 +- 1.52% (stat.) +- 7.19% (syst.)
    # 4e: 2.54 +- 8.43% (stat.) +- 13% (syst.)
    # 2mu2e: 3.19 +- 5.97% (stat.) +- 14.8% (syst.)
    # 2e2mu: 2.57 +- 1.52% (stat.) +- 7.19% (syst.)
    # 4l: 10.6 +- 2.84% (stat.) +- 8.22% (syst.)

    # make sure that we use the same keys in llNorms and TH1Dict
    llNorms = { "llmumu" : 2.29+2.57 , "llee" : 2.54+3.19, "4l" : 10.6}
    TH1Dict = {}



    # get the all the pdfs
    pdfDict, m34 = makeRooKeysPDFs()
    #  pdfDict[finalState][shapeType] = RooKeysPdf
    #   e.g. pdfDict[ "llmumu" ][ "HeavyFlavor" ] = RooKeysPdf

    ## llmumu shapes are from Z+HeavyFlavor and ttbar MC 
    ## llee   shapes are from Z+HeavyFlavor MC and 3l+X 

    HFFractionFor_llmumu = 0.5
    HFFractionFor_llee   = 0.5

    # let's don't put the things below into a subfunction, so we don't have to be concerned with delted-due-out-of-scope issues

    llmumuheavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llmumu, 0.,1.)
    llmumuPDF = ROOT.RooAddPdf("llmumuPDF", "llmumuPDF", pdfDict["llmumu"]["HeavyFlavor"] ,   pdfDict["llmumu"]["ttBar" ], llmumuheavyFlavorWeight )

    lleeheavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llee, 0.,1.)
    lleePDF = ROOT.RooAddPdf("lleePDF", "lleePDF", pdfDict["llee"]["HeavyFlavor"] ,   pdfDict["llee"]["3l+X" ], lleeheavyFlavorWeight )


    TH1Dict["llmumu"] = llmumuPDF.createHistogram(m34.GetName(),nBins)
    TH1Dict["llee"] = lleePDF.createHistogram(m34.GetName(),nBins)

    for flavor in TH1Dict: TH1Dict[flavor].Scale( llNorms[flavor] )


    if convertXAxisFromMeVToGeV: 
        for flavor in TH1Dict: TH1Dict[flavor] = th1HistMevToGeV( TH1Dict[flavor] )


    newName = re.sub("llmumu", "4l", TH1Dict["llmumu"].GetName())
    newTitle = re.sub("llmumu", "4l", TH1Dict["llmumu"].GetTitle())


    

    
    TH1Dict["4l"] = TH1Dict["llmumu"].Clone(newName)
    TH1Dict["4l"].SetTitle(newTitle)
    TH1Dict["4l"].Add(TH1Dict["llee"])

    #for flavor in TH1Dict: TH1Dict[flavor].Integral()
    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    return None



if __name__ == '__main__':


    getReducibleTH1s()

    ### Plot the pdf together with the data for visualization

    # we need a common independentVariable for all PDFs, that's why out output it here
    pdfDict, m34 = makeRooKeysPDFs()

    nBins = 101

    shapeSourceFiles = getTTreeLocations()

    canvasDict = {}

    for finalState in [ "llee", "llmumu"]:

        canvasCounter = 0
        canv = ROOT.TCanvas( finalState+"_canvas", finalState+"_canvas", 900, 900)
        canv.Divide(2,2)
        canvasDict[finalState] = canv

        for shapeType in shapeSourceFiles:

            fileName = shapeSourceFiles[shapeType]



            aTTree = getZXTTree( shapeType )
            aDataSet, _ = getShapeRooDataSetAndIndepVar(aTTree,  finalState, m34)

            kest3 = pdfDict[finalState][shapeType]

            plotName = shapeType + ": " + finalState

            canvasCounter += 1
            canv.cd(canvasCounter)

            xFrameHists = m34.frame() # frame to plot my PDFs on
            xFrameHists.SetTitle(plotName)
            aDataSet.plotOn(xFrameHists)

            kest3.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kGreen+1),ROOT.RooFit.LineStyle(7))


            xFrameHists.Draw()
            canv.Update()


    canvasDict["llmumu"].cd(4)

    xFrameHists = m34.frame() # frame to plot my PDFs on

    for step in range(5,6): 

        weightSetting = float(step)/10

        heavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", weightSetting, 0.,1.)
        llmumuPDF = ROOT.RooAddPdf("llmumuPDF", "llmumuPDF", pdfDict["llmumu"]["HeavyFlavor"] ,   pdfDict["llmumu"]["ttBar" ], heavyFlavorWeight )

        
        llmumuPDF.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kAzure+step))


        xFrameHists.Draw()

        canvasDict["llmumu"].Update()


    testHist = llmumuPDF.createHistogram("llll_m34",nBins)

    testHist.Draw("same")

    canvasDict["llmumu"].Update()

    testHist.GetNbinsX()


    testHistMeV = th1HistMevToGeV(testHist)

    testCanv = ROOT.TCanvas()
    testCanv.cd()
    testHistMeV.Draw()
    testCanv.Update()

    # aTFile.Get()

    # aDataSetWeighted.sumEntries()
    # aTFile.Get("410472").Get("Nominal").Get("h_ZXSR_All_HWindow_m34").Integral()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
