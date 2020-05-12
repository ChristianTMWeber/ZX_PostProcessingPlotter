import ROOT
import math
import copy
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import os

#   Use getReducibleTH1s() to get a dict of shapes for the reducible estimates
#   
#   
#   
#   
#   
#   
#   




def getRooRealVarFromTree( branchName, relevantTTree ):
    return ROOT.RooRealVar(branchName,branchName, math.floor(relevantTTree.GetMinimum(branchName)), math.ceil(relevantTTree.GetMaximum(branchName)))


def getTTreeLocations():

    shapeSourceFiles = { "HeavyFlavor" : "post_20200228_203930__ZX_Run2_ZJetBFilter_May_Minitree.root", 
                         "ttBar"       : "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root",
                         #"ttBar"       : "post_20200505_152227__ZX_Run2_Bckg_May_InvertedD0cr_ttbar_minitree_TEST.root",
                         "3l+X"        : "post_20200319_122149__ZX_Run2_Data_May_3lX_Minitree.root"      }


    # we need to translate the file names to absolute paths, as the working dir is arbitrary when we execute this script as a module
    absPathToThisScript = os.path.realpath(__file__)
    absPathToDicretory = os.path.dirname(absPathToThisScript)
    for key in shapeSourceFiles: shapeSourceFiles[key] =  os.path.join(absPathToDicretory, shapeSourceFiles[key] )
                         
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
    weight.setMin(-1.1) # use this value to ignore one negative datapoint that trip the RooKeysPDF up

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


def makeRooKeysPDFs( m34Min = 12000, m34Max = 115000):

    ## llmumu shapes are from Z+HeavyFlavor and ttbar MC 
    ## llee   shapes are from Z+HeavyFlavor MC and 3l+X 

    #fileName = "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root"

    #  pdfDict[finalState][shapeType] = RooKeysPdf
    #   e.g. pdfDict[ "llmumu" ][ "HeavyFlavor" ] = RooKeysPdf
    pdfDict = collections.defaultdict(lambda: collections.defaultdict(dict))


    # we need a common independentVariable for all PDFs, so that we can add them etc. That's why we define it here
    m34 = ROOT.RooRealVar( "llll_m34", "llll_m34", m34Min , m34Max )

    shapeSourceFiles = getTTreeLocations()

    for finalState in [ "llee", "llmumu"]:

        for shapeType in shapeSourceFiles:

            aTTree = getZXTTree( shapeType )

            aDataSet, _ = getShapeRooDataSetAndIndepVar(aTTree, finalState, m34)

            pdfName = "PDF_"+shapeType+"_"+finalState

            #kest1 = ROOT.RooKeysPdf("kest1", "kest1", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            #kest2 = ROOT.RooKeysPdf("kest2", "kest2", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            kest3 = ROOT.RooKeysPdf(pdfName, pdfName, m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)

            pdfDict[finalState][shapeType] = kest3

    return pdfDict, m34


def addRelativeHistError(hist, relError, errorIsOnIntegral = False):
    for n in xrange(0,hist.GetNbinsX()+2): 
        hist.SetBinError(n, hist.GetBinContent(n) * relError )

    if errorIsOnIntegral: # hist errors are added in quadrature. 
        # If the error relates to the uncertainty in the integral of the yield, correct appropriately here

        lowerLimit = 0
        upperLimit = hist.GetNbinsX() +1

        integralUncertainty = ROOT.Double()

        integral = hist.IntegralAndError( lowerLimit , upperLimit, integralUncertainty)
        errorCorrectionFactor = relError/(integralUncertainty / integral)

        for n in xrange(0,hist.GetNbinsX()+2): 
            hist.SetBinError(n, hist.GetBinError(n) * errorCorrectionFactor )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


def getReducibleTH1s(TH1Template = None , convertXAxisFromMeVToGeV = False):





    HFFractionFor_llmumu = (14.23+4.53)/(14.23+4.53+7.38) #taken from the H4l event selection support note
    HFFractionFor_llee   = (12.1)/(12.1+4.18+14.79) 

    # reducible background in final states, 115<m4l<130
    # 4mu: 2.29 +- 1.52% (stat.) +- 7.19% (syst.)
    # 4e: 2.54 +- 8.43% (stat.) +- 13% (syst.)
    # 2mu2e: 3.19 +- 5.97% (stat.) +- 14.8% (syst.)
    # 2e2mu: 2.57 +- 1.52% (stat.) +- 7.19% (syst.)
    # 4l: 10.6 +- 2.84% (stat.) +- 8.22% (syst.)

    # make sure that we use the same keys in llNorms and TH1Dict
    llNorms = { "llmumu" : 2.29+2.57 , "llee" : 2.54+3.19, "all" : 10.6}

    # adjust norms to mc16a luminosities
    #for key in llNorms: llNorms[key]= llNorms[key] * 36.3/139

    # add stat error only. Add syst error to limitSetting.py instead
    statErrorDict = { "llmumu" : (2.29*0.0152 + 2.57*0.0152)/(2.29+2.57) , 
                      "llee"   : (2.54*0.0843 + 3.19*0.0597)/(2.54+3.19), 
                      "all"     : 0.0284}


    TH1Dict = {}

    

    m34Min = 12000; m34Max = 115000;

    
    if convertXAxisFromMeVToGeV : GeVScaleFactor = 1e3
    else:                         GeVScaleFactor = 1.



    if TH1Template is None:
        nBins = 100
        # get the all the pdfs
        pdfDict, m34 = makeRooKeysPDFs()
    #  pdfDict[finalState][shapeType] = RooKeysPdf
    #   e.g. pdfDict[ "llmumu" ][ "HeavyFlavor" ] = RooKeysPdf

        

    else: 

        lowBin = TH1Template.GetXaxis().FindBin( m34Min/GeVScaleFactor)    

        highBin = TH1Template.GetXaxis().FindBin(m34Max/GeVScaleFactor)  

        # m34 min and max change the limits of the relevant independent variable and implicitly the limits of the TH1 that will be created from the inheriting PDF
        # thus change it so that the bin edges will match with the TH1Template
        m34Min = (TH1Template.GetBinLowEdge(lowBin)     ) * GeVScaleFactor
        m34Max = (TH1Template.GetBinLowEdge(highBin+1)  ) * GeVScaleFactor

        nBins = highBin-lowBin+1

        #testHist = ROOT.TH1D("TEST", "m_{34} [GeV]", nBins, m34Min, m34Max)

        pdfDict, m34 = makeRooKeysPDFs( m34Min = m34Min, m34Max = m34Max)




    ## llmumu shapes are from Z+HeavyFlavor and ttbar MC 
    ## llee   shapes are from Z+HeavyFlavor MC and 3l+X 


    # let's don't put the things below into a subfunction, so we don't have to be concerned with delted-due-out-of-scope issues

    llmumuheavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llmumu, 0.,1.)
    llmumuPDF = ROOT.RooAddPdf("llmumuPDF", "llmumuPDF", pdfDict["llmumu"]["HeavyFlavor"] ,   pdfDict["llmumu"]["ttBar" ], llmumuheavyFlavorWeight )

    lleeheavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llee, 0.,1.)
    lleePDF = ROOT.RooAddPdf("lleePDF", "lleePDF", pdfDict["llee"]["HeavyFlavor"] ,   pdfDict["llee"]["3l+X" ], lleeheavyFlavorWeight )


    TH1Dict["llmumu"] = llmumuPDF.createHistogram(m34.GetName(),nBins)
    TH1Dict["llee"] = lleePDF.createHistogram(m34.GetName(),nBins)

    


    for flavor in TH1Dict: TH1Dict[flavor].Scale( llNorms[flavor] ) # normalize the m34 distribution to the correct event count


    if convertXAxisFromMeVToGeV: 
        for flavor in TH1Dict: TH1Dict[flavor] = th1HistMevToGeV( TH1Dict[flavor] )


    # if a TH1Template was provided we wanna make sure that we output a histogram with the same binning
    # in that case, the TH1s in the TH1Dict contain a subset of the bins in the template
    # i.e. same binwidth, same bin edges, but possible for not the same range
    # here we effective extend the range, such that he binning is identical

    if TH1Template is not None:
        for flavor in TH1Dict: 

            tempHist = TH1Template.Clone( TH1Dict[flavor].GetName() )
            tempHist.Reset("ICESM")
            tempHist.SetTitle( TH1Dict[flavor].GetTitle() )

            for binNr in xrange(1, TH1Dict[flavor].GetNbinsX() +1) :  
                tempHist.SetBinContent(binNr + lowBin -1, TH1Dict[flavor].GetBinContent(binNr) )

            TH1Dict[flavor] = tempHist


# Setup the llmumu + llee, e.g. the 

    newName = re.sub("llmumu", "all", TH1Dict["llmumu"].GetName())
    newTitle = re.sub("llmumu", "all", TH1Dict["llmumu"].GetTitle())
    
    TH1Dict["all"] = TH1Dict["llmumu"].Clone(newName)
    TH1Dict["all"].SetTitle(newTitle)
    TH1Dict["all"].Add(TH1Dict["llee"])

    for finalState in TH1Dict: addRelativeHistError( TH1Dict[finalState]  ,  statErrorDict[finalState] , errorIsOnIntegral = True )

    #for flavor in TH1Dict: TH1Dict[flavor].Integral()
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return TH1Dict



if __name__ == '__main__':


    #testHist = ROOT.TH1D("TEST", "TEST", 200, 10000,150000 )

    testHist = ROOT.TH1D("TEST", "m_{34} [GeV]", 50, 0, 150)




    TH1Dict = getReducibleTH1s(TH1Template = testHist , convertXAxisFromMeVToGeV = True )

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


        canvasDict[finalState].cd(4)

        xFrameHists = m34.frame() # frame to plot my PDFs on

        

        weightSetting = 0.5;

        


        if finalState == "llmumu":
            HFFractionFor_llmumu = (14.23+4.53)/(14.23+4.53+7.38) #taken from the H4l event selection support note
            heavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llmumu, 0.,1.)
            llPDF = ROOT.RooAddPdf(finalState, finalState, pdfDict[finalState]["HeavyFlavor"] ,   pdfDict[finalState]["ttBar" ], heavyFlavorWeight )
        elif finalState == "llee" :
            HFFractionFor_llee   = (12.1)/(12.1+4.18+14.79) 
            heavyFlavorWeight = ROOT.RooRealVar("HeavyFlavorWeight", "HeavyFlavorWeight", HFFractionFor_llee, 0.,1.)
            llPDF = ROOT.RooAddPdf(finalState, finalState, pdfDict[finalState]["HeavyFlavor"] ,   pdfDict["llee"]["3l+X" ], heavyFlavorWeight )
        
        llPDF.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kAzure+1))


        xFrameHists.Draw()




        histFromPDF = TH1Dict[finalState]

        histFromPDF.Scale( 1./histFromPDF.Integral() )

        histFromPDF.Draw("same")

        canvasDict[finalState].Update()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


