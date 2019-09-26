import ROOT
import numpy as np # to generate randum numbers 
import time # for measuring execution time


def reportMemUsage(startTime = None):
    import resource # print 'Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    import time # for measuring execution time
    import datetime # to convert seconds to hours:minutes:seconds

    displayString = "Memory usage: %s kB \t Runtime: " % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/8) 

    if startTime is not None: displayString += str(datetime.timedelta(seconds=( time.time()- startTime) ))
    
    print displayString

    return None

def setupIndependentVar(hist):
    nBins = hist.GetNbinsX()
    lowLimit  = hist.GetBinLowEdge(1)
    highLimit = hist.GetBinLowEdge(nBins+1)
    # independent variable for out RooFit objects (PDFs and rooDatahists [the RDHs] )  
    indepVar = ROOT.RooRealVar("indepVariable","indepVariable",  lowLimit , highLimit)
    return indepVar

def TH1ToRooHistPDF( inputTH1, indepVar = None):
    # convert a ROOT.TH1 to a RooDataHist (a RooFit data format)
    # better provide a RooRealVar that can serve as the independent variable in the RooDataHist and RooAbsPDF 
    if indepVar is None: indepVar = setupIndependentVar(hist) # prepare an indepdentend variable if none is given

    aRooDataHist = ROOT.RooDataHist( inputTH1.GetName()+"RDH", inputTH1.GetTitle()+"RDH", ROOT.RooArgList(indepVar), inputTH1,1)
    aRooAbsPdf   = ROOT.RooHistPdf(  inputTH1.GetName()+"PDF", inputTH1.GetTitle()+"PDF", ROOT.RooArgSet(indepVar) , aRooDataHist )
    return aRooAbsPdf, aRooDataHist # need to also keep RooDataHist for the morphing to work

def makeErrorHistogram( histToBeFilled, errorSourceHist):
    # sets the bin contents of the first histogram with the bin-errors of the second
    assert histToBeFilled.GetNbinsX() == errorSourceHist.GetNbinsX()
    for n in xrange(0, histToBeFilled.GetNbinsX() +2 ):  # start at 0 for the underflow, end at +2 to reach also the overflow
        histToBeFilled.SetBinContent(n, errorSourceHist.GetBinError(n) )
    return histToBeFilled

def fillBinErrorWithHist(histToBeFilled, sourceHist): 
    #fill binErrors of 'histToBeFilled' with binContents of 'sourceHist'
    assert histToBeFilled.GetNbinsX() == sourceHist.GetNbinsX()
    for n in xrange(0, histToBeFilled.GetNbinsX() +2 ): # start at 0 for the underflow, end at +2 to reach also the overflow
        histToBeFilled.SetBinError(n, sourceHist.GetBinContent(n) )
    return histToBeFilled

def drawSetOfHists( histList , drawOptions = [] , canvasName = None): 
    # draw all histograms in a list of histograms. 
    #Need to pass on the canvas so that it is still in scope once the function completes
    if isinstance(histList, ROOT.TH1 ): histList = [histList]
    if not isinstance(drawOptions, list ): drawOptions = [drawOptions]

    if canvasName is None: canvasName = histList[0].GetName()

    canvasPDF = ROOT.TCanvas( canvasName, canvasName ,1300/2,1300/2)
    for hist in histList: hist.Draw("SAME" + " ".join(drawOptions) )
    canvasPDF.Update()

    return canvasPDF

def getNewSetNorm( x1, x2, y1, y2, xNew ): 
    # let f(x_i)  = y_i
    # interpolate between x1 and x2 them linearly
    slope = float(y2-y1)/float(x2-x1) 
    yNew = slope * (xNew - x1)  + y1
    return yNew

def integralMorphWrapper( interpolateAt, indepVar, PDFLow, parameterLow, PDFHigh, prameterHigh, nBins):

    # scale the parameters values to the interval [0,1], RooIntegralMorph assumes it to be that way
    delta = float(prameterHigh - parameterLow)
    scaledInterpolateTo = float(interpolateAt - parameterLow)/delta
    
    # do the interpolation
    alpha = ROOT.RooRealVar("alpha", "alpha", scaledInterpolateTo,  0. , 1.) # alpha is here the interpolation paramter, we assume histA and histB represent at at alpha=0, and 1, respectively. At want to interpolate at 0 < scaledInterpolateTo < 1
    morphInt = ROOT.RooIntegralMorph('morph','morph',  PDFHigh, PDFLow , indepVar, alpha) # this is not the sequence of A and B hist I expected, but it gives the expected behavior

    return morphInt.createHistogram( indepVar.GetName(), nBins)

def momentMorphWrapper( interpolateAt, indepVar, PDFList, parameterList, nBins):
    # we do have a set of PDFs, which we assume can be parameterizes by a continous variable mu
    # we parameterList[i] contains the value mu_i, so that  PDFList[i] is the pdf corresponding to mu_i = parameterList[i]
    # we interpolate at min(parameterList) < interpolateAt < max(parameterList)

    listOfMorphs = ROOT.RooArgList( "listOfMorphs" )
    for pdf in PDFList: listOfMorphs.add( pdf )  # RooHistPdf at mH=low

    nParameters = len(parameterList) 
    paramVec = ROOT.TVectorD( nParameters )
    for n in xrange(nParameters): paramVec[n] = parameterList[n]

    mu = ROOT.RooRealVar("mu", "mu", interpolateAt, min(parameterList), max(parameterList) )
    #ROOT.RooMomentMorph("morph", "morph", alpha, vList, hpdfList, paramVec, ROOT.RooMomentMorph.Linear);

    # indepVar should be the independent parameter of the input PDFs 
    # Linear and NonLinear should be equivalent for just two inputs
    morphMoment = ROOT.RooMomentMorph( "morph", "morph", mu , ROOT.RooArgList(indepVar), listOfMorphs, paramVec, ROOT.RooMomentMorph.Linear  )
    return morphMoment.createHistogram( indepVar.GetName(), nBins)


def sampleTH1FromTH1(sourceTH1):
    
    sampledTH1 = sourceTH1.Clone( sourceTH1.GetName() + "randomSample" )

    for n in xrange(0, sourceTH1.GetNbinsX() +2 ):  # start at 0 for the underflow, end at +2 to reach also the overflow

        mean = sourceTH1.GetBinContent(n) 
        stdDev = sourceTH1.GetBinError(n) 

        sampledTH1.SetBinContent(n, np.random.normal(mean, stdDev) )

    return sampledTH1

def TH1toArray(TH1):
    nBins = TH1.GetNbinsX()
    outArray = np.zeros(nBins)
    # we are skipping under- and overflow for now
    for n in xrange(1,nBins+1):  outArray[n-1] = TH1.GetBinContent(n) 

    return outArray


def getInterpolatedHistogram(histA, histB,  paramA = 0 , paramB = 1, interpolateAt = 0.5, errorInterpolation = False , morphType = "momentMorph", nSimulationRounds = 100):
    # Assumine we have two histograms histA and histB that represent slices of a 2d histogram
    # along some axis Y, I.e. histA == hist( Y_A), histB == hist( Y_B)
    # we assume here Y_A < Y_B
    # This funtion aims to provide hist( y ) for Y_A < y < Y_B by interpolating between 
    # 
    # Create a histogram that is the interpolation of the TH1 histograms histA and histB
    #
    #
    # We will use RooIntegralMorph Class, see here: https://root.cern.ch/doc/master/classRooIntegralMorph.html
    # From that description there note:
    # "From a technical point of view class RooIntegralMorph is a p.d.f that takes two input p.d.fs
    #  f1(x,p) an f2(x,q) and an interpolation parameter to make a p.d.f fbar(x,p,q,alpha). 
    #  The shapes f1 and f2 are always taken to be end the end-points of the parameter alpha, 
    #  regardless of what the those numeric values are."

    # check input values
    assert (paramA < interpolateAt) and (interpolateAt < paramB)

    # RooFit command to suppress all the Info and Progress message is below
    # the message are ordered by the following enumeration defined in RooGlobalFunc.h
    # enum MsgLevel { DEBUG=0, INFO=1, PROGRESS=2, WARNING=3, ERROR=4, FATAL=5 } ;
    rooMsgServe = ROOT.RooMsgService.instance()                
    rooMsgServe.setGlobalKillBelow(ROOT.RooFit.PROGRESS)

    # independent variable for out RooFit objects (PDFs and rooDatahists [the RDHs] )  
    x = setupIndependentVar(histA)  # creates independ variable with the limits of the input histogram

    histA_PDF, histA_RDH = TH1ToRooHistPDF( histA, x)
    histB_PDF, histB_RDH = TH1ToRooHistPDF( histB, x)

    # scale the parameters values to the interval [0,1], RooIntegralMorph assumes it to be that way
    delta = float(paramB - paramA)
    scaledInterpolateTo = float(interpolateAt - paramA)/delta
    
    # do the interpolation
    alpha = ROOT.RooRealVar("alpha", "alpha", scaledInterpolateTo,  0. , 1.) # alpha is here the interpolation paramter, we assume histA and histB represent at at alpha=0, and 1, respectively. At want to interpolate at 0 < scaledInterpolateTo < 1
    #morphInt = ROOT.RooIntegralMorph('morph','morph',  histB_PDF, histA_PDF , x, alpha) # this is not the sequence of A and B hist I expected, but it gives the expected behavior

    if   morphType == "momentMorph":    morphedHist = momentMorphWrapper( interpolateAt, x, [histA_PDF, histB_PDF], [paramA, paramB], histA.GetNbinsX())
    elif morphType == "integralMorph":  morphedHist = integralMorphWrapper( interpolateAt, x, histA_PDF, paramA, histB_PDF, paramB, histA.GetNbinsX())
    else: raise Exception( "Invalid choice of 'morphType'. Valid choices are 'integralMorph', and 'momentMorph'")

    # normalize histogram

    newSetNorm = getNewSetNorm( paramA, paramB, histA.Integral(), histB.Integral(), interpolateAt )
    normMorph = morphedHist.Integral()

    morphedHist.Scale( newSetNorm/normMorph )
    morphedHist.SetName( histA.GetName() + ("interpAt%2.2f") %(float(interpolateAt)) )
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    #canv = ROOT.TCanvas()
    #morphedHist.Draw("HIST")
    #histA.Draw("Same")
    #canv.Update()

    ################################### 
    # interpolate errors as well 
    ################################### 

    if errorInterpolation == "simulateErrors":  # We'll morph the errors too
        # by sampling hists from histA and histB, 
        # interpolating these samples multiple times
        # and calculating a binwise standard deviation, that we take to be the error of the morphed histogram

        binValueArray =  np.zeros( (nSimulationRounds, histA.GetNbinsX()) )

        for simNr in xrange(nSimulationRounds):

            sampleA = sampleTH1FromTH1(histA) 
            sampleB = sampleTH1FromTH1(histB) 

            sampleMorphed = getInterpolatedHistogram(sampleA, sampleB,  paramA , paramB, interpolateAt, errorInterpolation = False, morphType = morphType)

            binValueArray[simNr,:] = TH1toArray(sampleMorphed)
            sampleMorphed.Delete() # delete the histogram to eliminate warnings about replacing an existing object 

        binStandardDevs = np.std( binValueArray, axis = 0 )

        for n in xrange( histA.GetNbinsX() ): morphedHist.SetBinError(n+1, binStandardDevs[n] )

    elif errorInterpolation == "morph1SigmaHists": # We'll morph the errors too
        # by calculing histA+histA_Error and histB+histB_Error
        # interpolint these, and take the difference to the original interpolates hist as error

        def make1signaHist( hist): # for each bin we have BinContent + Bin Error of hist
            hist1Sigma = hist.Clone(hist.GetName()+"1sigma")
            makeErrorHistogram( hist1Sigma, hist)
            hist1Sigma.Add(hist)
            return hist1Sigma

        histA1sigma = make1signaHist( histA)
        histB1sigma = make1signaHist( histB)

        # let's morph these errorHists, and remember: the bin contents of the 'morphedErrors' hist, are the bin erros of 'morphedHist' that we are looking for 
        morphedErrors = getInterpolatedHistogram(histA1sigma, histB1sigma,  paramA , paramB, interpolateAt, errorInterpolation = False, morphType = morphType)

        morphedErrors.Add(morphedHist,-1) # subtraction: morphedErrors-morphedHist
        # transfer the bin errors from 'morphedErrors' to 'morphedHist' 
        for n in xrange(0, morphedHist.GetNbinsX() +2 ): # start at 0 for the underflow, end at +2 to reach also the overflow
            morphedHist.SetBinError(n, morphedErrors.GetBinContent(n) )


    elif errorInterpolation == "morphErrorsToo": # We'll morph the errors too
        # by making 'errorHists' whose bin content is the bin errors of the 'regular hists'
        # Then we morpth the 'errorHists' regularly, and eventually we transfer the erros to the morphedHist

        # prepare the 'errorHists'
        prepErrorHist = lambda x : makeErrorHistogram( x.Clone(x.GetName()+"Error"), x)
        errorHistA = prepErrorHist(histA)
        errorHistB = prepErrorHist(histB)

        # let's morph these errorHists, and remember: the bin contents of the 'morphedErrors' hist, are the bin erros of 'morphedHist' that we are looking for 
        morphedErrors = getInterpolatedHistogram(errorHistA, errorHistB,  paramA , paramB, interpolateAt, errorInterpolation = False, morphType = morphType)
        # transfer the bin errors from 'morphedErrors' to 'morphedHist' 
        for n in xrange(0, morphedHist.GetNbinsX() +2 ): # start at 0 for the underflow, end at +2 to reach also the overflow
            morphedHist.SetBinError(n, morphedErrors.GetBinContent(n) )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return morphedHist



if __name__ == '__main__':

    import numpy as np

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.1; yOffset = 0.4
        xWidth  = 0.4; ywidth = 0.5
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    ######################################################################
    # prepare PDFs that we will turn into TH1s. We will use those TH1s to test the morphing.
    ######################################################################
    x = ROOT.RooRealVar("indepVariable","indepVariable",  -10. ,10.)

    # gaussian PDF, 
    mean1  = ROOT.RooRealVar("mean1" , "mean of gaussian" , -5 , -10. , 10. )
    sigma1 = ROOT.RooRealVar("sigma1", "width of gaussian", 1. , -10. , 10. )
    gaussianPDF1 = ROOT.RooGaussian("Gaussian1", "Gaussian1", x, mean1, sigma1) 

    #
    mean2  = ROOT.RooRealVar("mean2" , "mean of gaussian" , +5., -10. , 10. )
    sigma2 = ROOT.RooRealVar("sigma2", "width of gaussian", 1. , -10. , 10. )
    gaussianPDF2 = ROOT.RooGaussian("Gaussian2", "Gaussian2", x, mean2, sigma2) 

    constPDF = ROOT.RooPolynomial("RooPolynomial", "RooPolynomial", x, ROOT.RooArgList()) 

    nBins = 20
    histA = gaussianPDF1.createHistogram("indepVariable",nBins)
    histB = gaussianPDF2.createHistogram("indepVariable",nBins)
    #histConst = gaussianPDFSuperWide.createHistogram("indepVariable",nBins)
    histConst = constPDF.createHistogram("indepVariable",nBins)

    histAClone = histA.Clone(histA.GetName()+"Clone")
    histBClone = histB.Clone(histB.GetName()+"Clone")

    histAClone.Scale(0.1)
    histBClone.Scale(0.1)





    fillBinErrorWithHist(histA, histAClone) #fill binErrors
    fillBinErrorWithHist(histB, histBClone) #fill binErrors

    #for hist in [histA, histB]: fillBinErrorWithHist(hist, histConst) #fill binErrors

    histA.Scale(3)
    histB.Scale(1)

    ##########################
    # Do the morphing
    ##########################
    morphedHistList = []

    startTime = time.time()
    for n in np.arange(mean1.getVal(), mean2.getVal(),2)+1: 
        #                             errorInterpolation options:        simulateErrors      morph1SigmaHists        morphErrorsToo
        morphedHist = getInterpolatedHistogram(histA, histB, mean1.getVal(), mean2.getVal(), n , errorInterpolation = "morph1SigmaHists", morphType = "momentMorph", nSimulationRounds = 100)
        morphedHist.SetLineColor(ROOT.kGreen)
        morphedHistList.append(morphedHist)
        reportMemUsage(startTime = startTime)

    #myFile = ROOT.TFile("morphData.root","OPEN")
    #histA = myFile.Get("30Gev")
    #histB = myFile.Get("35Gev")
    #morphedHist = getInterpolatedHistogram(histA, histB )

    ##########################
    # Plot the results of the morphing to investigate them
    ##########################

    histA.SetLineColor(ROOT.kBlue)
    histB.SetLineColor(ROOT.kRed)

    morphedHistList.extend([histA, histB])

    
    legend = setupTLegend()

    aCanvas1 = drawSetOfHists( morphedHistList , drawOptions = ["HIST"], canvasName = "Morphed Hist plot" )
    for hist in morphedHistList:   legend.AddEntry(hist)
    legend.Draw(); # do legend things
    aCanvas1.Update()


    aCanvas2 = drawSetOfHists( morphedHistList , drawOptions = ["E1"], canvasName = "Morphed Hist plot, E1" )
    legend.Draw(); # do legend things
    aCanvas2.Update()


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    # try moment morph

    #RooMomentMorph morph("morph", "morph", alpha, vList, hpdfList, paramVec, RooMomentMorph::Linear);



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



