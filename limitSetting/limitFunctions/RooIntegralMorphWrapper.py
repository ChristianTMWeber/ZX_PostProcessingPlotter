import ROOT
import numpy as np # to generate randum numbers 
import time # for measuring execution time
import bisect # to find locations in lists


import reportMemUsage


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
    if indepVar is None: indepVar = setupIndependentVar(inputTH1) # prepare an indepdentend variable if none is given

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


def getNewSetNorm( parameterList, listOfNorms, interpolateAt ): 

    def listToStdVector(inputList): # the ROOT.Math.Interpolator requires std.vectors as input parameters, let's furnish them
        stdVector = ROOT.std.vector('double')()
        for listElement in inputList : stdVector.push_back( float(listElement) )
        return stdVector

    xVector = listToStdVector(parameterList)
    yVector = listToStdVector(listOfNorms)

    nData = len(parameterList)

    # interpolation options, see https://root.cern/doc/master/group__Interpolation.html#ga4bce69f94d30b54fbf33940ba11d6630
    # kLINEAR, kPOLYNOMIAL, kCSPLINE, kCSPLINE_PERIODIC, kAKIMA, kAKIMA_PERIODIC

    if nData < 3: interpolator = ROOT.Math.Interpolator(nData, ROOT.Math.Interpolation.kLINEAR) # interpolation options: 
    else:         interpolator = ROOT.Math.Interpolator(nData, ROOT.Math.Interpolation.kCSPLINE) # interpolation options: 
    interpolator.SetData(xVector,yVector)

    return     interpolator.Eval(interpolateAt)

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
    # Linear, NonLinear, NonLinearPosFractions, NonLinearLinFractions,  SineLinear

    return morphMoment.createHistogram( indepVar.GetName(), nBins)


def sampleTH1FromTH1(sourceTH1):
    
    sampledTH1 = sourceTH1.Clone( sourceTH1.GetName() + "randomSample" )

    for n in xrange(0, sourceTH1.GetNbinsX() +2 ):  # start at 0 for the underflow, end at +2 to reach also the overflow

        mean = sourceTH1.GetBinContent(n) 
        stdDev = sourceTH1.GetBinError(n) 

        sampledTH1.SetBinContent(n, np.random.normal(mean, stdDev) )

    return sampledTH1

def getIndexOfNearestNeigborsInList(aList, valueOfInterest):

    assert aList == sorted(aList)

    lowNeighborIndex = bisect.bisect_left(aList,valueOfInterest) -1
    highNeighborIndex = bisect.bisect_right(aList,valueOfInterest)

    return lowNeighborIndex, highNeighborIndex

def TH1toArray(TH1):
    nBins = TH1.GetNbinsX()
    outArray = np.zeros(nBins)
    # we are skipping under- and overflow for now
    for n in xrange(1,nBins+1):  outArray[n-1] = TH1.GetBinContent(n) 

    return outArray

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

def getInterpolatedHistogram(histAndParamList, interpolateAt = 0.5, errorInterpolation = False , morphType = "momentMorph", nSimulationRounds = 100):
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

    for hist, parameter in histAndParamList: # make sure that the first element of the tuple is the TH1
        assert isinstance(hist,ROOT.TH1) and isinstance(parameter, (int, long, float))

    # RooFit command to suppress all the Info and Progress message is below
    # the message are ordered by the following enumeration defined in RooGlobalFunc.h
    # enum MsgLevel { DEBUG=0, INFO=1, PROGRESS=2, WARNING=3, ERROR=4, FATAL=5 } ;
    rooMsgServe = ROOT.RooMsgService.instance()                
    rooMsgServe.setGlobalKillBelow(ROOT.RooFit.PROGRESS)

    # independent variable for out RooFit objects (PDFs and rooDatahists [the RDHs] )  
    x = setupIndependentVar(histAndParamList[0][0])  # creates independ variable with the limits of the input histogram

    pdfList       = [] 
    parameterList = []
    dataHistList  = []

    listOfNorms = []

    # sort the list of tuples, by the value of the second tuple element, i.e. the parameter. This is important for the ROOT.Math.Interpolator that we might use later
    histAndParamList.sort(key = lambda x: x[1] ) 

    for hist, parameter in histAndParamList:     # and now that it is sorted, make RooPDFs out of the TH1s and put them and related objects into lists
        PDF, dataHist = TH1ToRooHistPDF( hist, x)
        pdfList.append(PDF)
        dataHistList.append(dataHist)
        parameterList.append(parameter)
        listOfNorms.append(hist.Integral())


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    leftIndex, rightIndex = getIndexOfNearestNeigborsInList(parameterList, interpolateAt) # get indices of next neighbor parameters, pdfs, etc

    referenceHist = histAndParamList[leftIndex][0]

    assert (parameterList[leftIndex] < interpolateAt) and (interpolateAt < parameterList[rightIndex])

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if   morphType == "momentMorph":    morphedHist = momentMorphWrapper( interpolateAt, x, pdfList, parameterList, referenceHist.GetNbinsX())
    elif morphType == "integralMorph":  morphedHist = integralMorphWrapper( interpolateAt, x, pdfList[leftIndex], parameterList[leftIndex], pdfList[rightIndex], parameterList[rightIndex], referenceHist.GetNbinsX())
    else: raise Exception( "Invalid choice of 'morphType'. Valid choices are 'integralMorph', and 'momentMorph'")

    # normalize histogram

    newSetNorm = getNewSetNorm( parameterList, listOfNorms, interpolateAt )
    normMorph = morphedHist.Integral()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    morphedHist.Scale( newSetNorm/normMorph )
    morphedHist.SetName( referenceHist.GetName() + ("interpAt%2.2f") %(float(interpolateAt)) )
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

        binValueArray =  np.zeros( (nSimulationRounds, referenceHist.GetNbinsX()) )

        for simNr in xrange(nSimulationRounds):

            #sampledHistsAndParam = [ (sampleTH1FromTH1(hist),param) for hist, param in histAndParamList ]
            sampledHistsAndParam = [ (sampleTH1FromTH1(histAndParamList[leftIndex][0]),histAndParamList[leftIndex][1]) ]
            sampledHistsAndParam.append((sampleTH1FromTH1(histAndParamList[rightIndex][0]),histAndParamList[rightIndex][1])) 

            sampleMorphed = getInterpolatedHistogram(sampledHistsAndParam, interpolateAt, errorInterpolation = False, morphType = morphType)

            binValueArray[simNr,:] = TH1toArray(sampleMorphed)
            sampleMorphed.Delete() # delete the histogram to eliminate warnings about replacing an existing object 

        binStandardDevs = np.std( binValueArray, axis = 0 )

        for n in xrange( referenceHist.GetNbinsX() ): morphedHist.SetBinError(n+1, binStandardDevs[n] )

    elif errorInterpolation == "morph1SigmaHists": # We'll morph the errors too
        # by calculing histA+histA_Error and histB+histB_Error
        # interpolint these, and take the difference to the original interpolates hist as error

        def make1signaHist( hist): # for each bin we have BinContent + Bin Error of hist
            hist1Sigma = hist.Clone(hist.GetName()+"1sigma")
            makeErrorHistogram( hist1Sigma, hist)
            hist1Sigma.Add(hist)
            return hist1Sigma

        #histA1sigma = make1signaHist( histA)
        #histB1sigma = make1signaHist( histB)

        oneSigmaHistsAndParam = [ (make1signaHist(hist),param) for hist, param in histAndParamList ]

        # let's morph these errorHists, and remember: the bin contents of the 'morphedErrors' hist, are the bin erros of 'morphedHist' that we are looking for 
        morphedErrors = getInterpolatedHistogram(oneSigmaHistsAndParam, interpolateAt, errorInterpolation = False, morphType = morphType)

        morphedErrors.Add(morphedHist,-1) # subtraction: morphedErrors-morphedHist
        # transfer the bin errors from 'morphedErrors' to 'morphedHist' 
        for n in xrange(0, morphedHist.GetNbinsX() +2 ): # start at 0 for the underflow, end at +2 to reach also the overflow
            morphedHist.SetBinError(n, morphedErrors.GetBinContent(n) )


    elif errorInterpolation == "morphErrorsToo": # We'll morph the errors too
        # by making 'errorHists' whose bin content is the bin errors of the 'regular hists'
        # Then we morpth the 'errorHists' regularly, and eventually we transfer the erros to the morphedHist

        # prepare the 'errorHists'
        prepErrorHist = lambda x : makeErrorHistogram( x.Clone(x.GetName()+"Error"), x)

        errorHistsAndParam = [ (prepErrorHist(hist),param) for hist, param in histAndParamList ]

        # let's morph these errorHists, and remember: the bin contents of the 'morphedErrors' hist, are the bin erros of 'morphedHist' that we are looking for 
        morphedErrors = getInterpolatedHistogram(errorHistsAndParam, interpolateAt, errorInterpolation = False, morphType = morphType)
        # transfer the bin errors from 'morphedErrors' to 'morphedHist' 
        for n in xrange(0, morphedHist.GetNbinsX() +2 ): # start at 0 for the underflow, end at +2 to reach also the overflow
            morphedHist.SetBinError(n, morphedErrors.GetBinContent(n) )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return morphedHist



if __name__ == '__main__':

    import numpy as np

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.1; yOffset = 0.7
        xWidth  = 0.4; ywidth = 0.2
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend


    def makeParametrizedGaussians( listOfGausMeans , sigmaFunction = lambda m: 1 , normFunction = lambda n: 1 ):

        outputHistDict = {}


        x = ROOT.RooRealVar("indepVariable","indepVariable",  -20. ,20.)
        nBins = 200

        for gaussMean in listOfGausMeans:

            # make gaussian PDF

            mean1  = ROOT.RooRealVar("mean1" , "mean of gaussian" , gaussMean )#, -10. , 10. )
            sigma1 = ROOT.RooRealVar("sigma1", "width of gaussian", sigmaFunction(gaussMean) )#, -10. , 10. )
            gaussianPDF1 = ROOT.RooGaussian("Gaussian%f" %gaussMean, "Gaussian%f" %gaussMean, x, mean1, sigma1) 

            # make histogram, and scale it
            histA = gaussianPDF1.createHistogram("indepVariable",nBins)

            histA.Scale( normFunction(gaussMean) )

            histA.SetLineColor(ROOT.kBlue)

            outputHistDict[gaussMean] = histA


            #### How I could add errors to the hist ###


            histAClone = histA.Clone(histA.GetName()+"Clone")
            histAClone.Scale(0.1)

            fillBinErrorWithHist(histA, histAClone) #fill binErrors
            
            #constPDF = ROOT.RooPolynomial("RooPolynomial", "RooPolynomial", x, ROOT.RooArgList()) 
            #histConst = constPDF.createHistogram("indepVariable",nBins)
            #fillBinErrorWithHist(histA, histConst) #fill binErrors

            #for hist in [histA, histB]: fillBinErrorWithHist(hist, histConst) #fill binErrors

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


        return outputHistDict


    ######################################################################
    # prepare TH1s to test the morphing.
    ######################################################################

    #histDict = makeParametrizedGaussians( [-5,0,5], sigmaFunction = lambda s: float(s)/100 + 1, normFunction = lambda n: 100 - n**2)
    histDict = makeParametrizedGaussians( range(-5,6,5), sigmaFunction = lambda s: float(s)/10 + 1, normFunction = lambda n: 1 )

    # getInterpolatedHistogram expects a list of tuples that is like [ (hist1, parameterAtWhichHist1WasRealized), ...]
    histAndParameters = []
    for key in histDict: histAndParameters.append((histDict[key], key))


    interpolateAtList = np.arange( min(histDict.keys()), max(histDict.keys())-1,2)+1


    ##########################
    # Do the morphing
    ##########################
    morphedHistList = []

    startTime = time.time()
    for interpolateAt in interpolateAtList: 
        #                             errorInterpolation options:        simulateErrors      morph1SigmaHists        morphErrorsToo
        #morphedHist = getInterpolatedHistogram(histA, histB, mean1.getVal(), mean2.getVal(), n , errorInterpolation = "morph1SigmaHists", morphType = "momentMorph", nSimulationRounds = 100)
        morphedHist = getInterpolatedHistogram(histAndParameters, interpolateAt , errorInterpolation = "morph1SigmaHists", morphType = "momentMorph", nSimulationRounds = 100)
        morphedHist.SetLineColor(ROOT.kGreen)
        morphedHistList.append(morphedHist)
        reportMemUsage.reportMemUsage(startTime = startTime)

    ##########################
    # Plot the results of the morphing to investigate them
    ##########################

    morphedHistList.extend( histDict.values() )
    
    legend = setupTLegend()

    aCanvas1 = drawSetOfHists( morphedHistList , drawOptions = ["HIST"], canvasName = "Morphed Hist plot" )
    #for hist in morphedHistList:   legend.AddEntry(hist)
    legend.AddEntry(morphedHistList[0],"Morphed Hists"); legend.AddEntry(morphedHistList[-1],"Input Hists")
    legend.Draw(); # do legend things
    aCanvas1.Update()


    aCanvas2 = drawSetOfHists( morphedHistList , drawOptions = ["E1"], canvasName = "Morphed Hist plot, E1" )
    legend.Draw(); # do legend things
    aCanvas2.Update()


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    # try moment morph

    #RooMomentMorph morph("morph", "morph", alpha, vList, hpdfList, paramVec, RooMomentMorph::Linear);



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



