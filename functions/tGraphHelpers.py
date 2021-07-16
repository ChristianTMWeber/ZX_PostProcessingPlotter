import ROOT

def getTGraphWithoutError( errorTGraph , ySetpoint = "median"):

    noErrorTGraph = ROOT.TGraph()

    xCopy =ROOT.Double() # use these for pass by reference
    yCopy = ROOT.Double() # use these for pass by reference

    #if   ySetpoint == "median":  getXY = lambda n : errorTGraph.GetPoint(n,xCopy,yCopy)
    #elif ySetpoint == "median":  getXY = lambda n : errorTGraph.GetPoint(n,xCopy,yCopy)

    for n in xrange(0,errorTGraph.GetN() ): 
        errorTGraph.GetPoint(n,xCopy,yCopy)
        if   ySetpoint == "yHigh": yCopy = ROOT.Double( yCopy + errorTGraph.GetErrorYhigh(n) )
        elif ySetpoint == "yLow":  yCopy = ROOT.Double( yCopy + errorTGraph.GetErrorYlow(n) )
        noErrorTGraph.SetPoint(n,xCopy,yCopy)

    return noErrorTGraph

def createNamedTGraph( objectName):
    graph = ROOT.TGraph()
    graph.SetName(objectName)
    return graph

def createNamedTGraphAsymmErrors( objectName):
    graph = ROOT.TGraphAsymmErrors()
    graph.SetName(objectName)
    return graph

def fillTGraphWithRooRealVar(graph, xFill, yFill):
    #                                                                                           bestEstimate
    def numberToRooRealVar(number): return ROOT.RooRealVar( "tempRooRealVar", "tempRooRealVar" , number     )

    if yFill is None: return graph
    elif not isinstance( yFill , ROOT.RooRealVar): yFill  = numberToRooRealVar(yFill)

    pointNr = graph.GetN()

    graph.SetPoint( pointNr, xFill, yFill.getVal() )

    if isinstance(graph,ROOT.TGraphAsymmErrors):

        yErrorHi = abs( yFill.getMax()-yFill.getVal() )
        yErrorLo = abs( -yFill.getMin() + yFill.getVal() )
        graph.SetPointError( pointNr, 0,0, yErrorLo , yErrorHi )

    return graph

def fillTGraphWithTuple(graph, xFill, yFill):

    # yFill = ( yLow , y, yHigh )
    # yLow <= y < =  yHigh
    # yLow and yHigh are the lower and upper limits on y

    assert len(yFill) == 3
    assert yFill[0] <= yFill[1] and yFill[1] <= yFill[2]

    yLow  = yFill[0] ;  y = yFill[1] ; yHigh = yFill[2]


    pointNr = graph.GetN()

    graph.SetPoint( pointNr, xFill, y )

    yErrorHi = abs( yHigh-y )
    yErrorLo = abs( -yLow + y )
    graph.SetPointError( pointNr, 0,0, yErrorLo , yErrorHi )

    return graph


def tGraphToList(TGraph , ySetpoint = "median"):

    xCopy =ROOT.Double() # use these for pass by reference
    yCopy = ROOT.Double() # use these for pass by reference
    yLowCopy = ROOT.Double() # use these for pass by reference
    yHighCopy = ROOT.Double() # use these for pass by reference

    xList = []
    yList = []
    yLowList = []
    yHighLowList = []

    for n in xrange(0,TGraph.GetN() ): 
        TGraph.GetPoint(n,xCopy,yCopy)
        if   ySetpoint == "yHigh": yCopy = ROOT.Double( yCopy + TGraph.GetErrorYhigh(n) )
        elif ySetpoint == "yLow":  yCopy = ROOT.Double( yCopy - TGraph.GetErrorYlow(n) )
        elif ySetpoint == "yLowAndYHigh":  
            yLowCopy = ROOT.Double( yCopy - TGraph.GetErrorYlow(n) )
            yHighCopy = ROOT.Double( yCopy + TGraph.GetErrorYhigh(n) )

        xList.append( float(xCopy))
        yList.append( float(yCopy))
        yLowList.append(float(yLowCopy))
        yHighLowList.append(float(yHighCopy))


    if ySetpoint == "yLowAndYHigh": return xList, yList, yLowList, yHighLowList
    else: return xList, yList

def listToTGraph( xList, yList, yLowList = None, yHighList = None ):

    doErrors = True

    if yLowList is None and yHighList is None: 
        doErrors = False
    elif yLowList is None:  
        yLowList = []
        for x in xrange( len(yList) ): yLowList.append(  yList[x] + ( yList[x] - yHighList[x] ) )
    elif yHighList is None:  
        yHighList = []
        for x in xrange( len(yList) ): yHighList.append(  yList[x] + ( yList[x] - yLowList[x]) )

    if doErrors: tGraph = ROOT.TGraphAsymmErrors()
    else:        tGraph = ROOT.TGraph() 


    for x in xrange( len(yList) ): 
        tGraph.SetPoint( x, xList[x], yList[x])
        if doErrors: tGraph.SetPointError( x, 0,0, yList[x] - yLowList[x], yHighList[x] - yList[x] )

    return tGraph


def dictToTGraph(aDict):

    xList = sorted(aDict.keys())

    yList = [aDict[xVal] for xVal in xList ]

    return listToTGraph( xList, yList )

def histToTGraph(hist, skipFunction = False, errorFunction = None):

    tGraph = ROOT.TGraphAsymmErrors()

    graphPointCounter = 0

    for binNr in xrange(1,hist.GetNbinsX()+1): 

        x = hist.GetBinCenter(binNr)
        y = hist.GetBinContent(binNr)

        if errorFunction is None: 
            yErrorLow  = hist.GetBinError(binNr)
            yErrorHigh = hist.GetBinError(binNr)

        else: yErrorLow, yErrorHigh = errorFunction(x,y)

        if skipFunction:
            if skipFunction(x,y,yErrorLow,yErrorHigh): continue

        tGraph.SetPoint( graphPointCounter, x, y)
        tGraph.SetPointError( graphPointCounter, 0,0, yErrorLow,  yErrorHigh )
        graphPointCounter += 1


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return tGraph


if __name__ == '__main__':

    import numpy as np 

    def setupTLegend():
        # set up a TLegend, still need to add the different entries
        xOffset = 0.6; yOffset = 0.7
        xWidth  = 0.3; ywidth = 0.2
        TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
        TLegend.SetFillColor(ROOT.kWhite)
        TLegend.SetLineColor(ROOT.kWhite)
        TLegend.SetNColumns(1);
        TLegend.SetFillStyle(0);  # make legend background transparent
        TLegend.SetBorderSize(0); # and remove its border without a border
        return TLegend

    expectedLimit1Sig = ROOT.TGraphAsymmErrors()
    expectedLimit2Sig = ROOT.TGraphAsymmErrors()
    extractedLimit = ROOT.TGraph()


    for x in xrange(0, 10): 
        
        n = expectedLimit1Sig.GetN()

        expectedLimit1Sig.SetPoint( n, x, np.cos(x) )
        expectedLimit1Sig.SetPointError( n, 0,0, .1, .2)
        expectedLimit2Sig.SetPoint( n, x, np.cos(x) )
        expectedLimit2Sig.SetPointError( n, 0,0, .3, .4)
        extractedLimit.SetPoint( n, x, np.cos(x)+0.1 )




    myGraphNoError= getTGraphWithoutError( expectedLimit1Sig )


    canv = ROOT.TCanvas("canvas", "canvas")

    colorScheme = ROOT.kRed



    expectedLimit2Sig.GetYaxis().SetTitle("95% CL on #sigma_{ZZ_{d}} [fb] ")
    expectedLimit2Sig.GetYaxis().SetTitleSize(0.06)
    expectedLimit2Sig.GetYaxis().SetTitleOffset(0.6)
    expectedLimit2Sig.GetYaxis().CenterTitle()

    expectedLimit2Sig.GetXaxis().SetTitle("m_{Z_{d}} [GeV]")
    expectedLimit2Sig.GetXaxis().SetTitleSize(0.05)
    expectedLimit2Sig.GetXaxis().SetTitleOffset(0.85)
    #expectedLimit2Sig.GetXaxis().CenterTitle()

    expectedLimit2Sig.SetFillColor(colorScheme-10)  # https://root.cern.ch/doc/master/classTAttFill.html
    #expectedLimit2Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit2Sig.Draw("A3") # use 'A' option only for first TGraph apparently

    #expectedLimit1Sig.SetFillColorAlpha(ROOT.kRed+1,0.5) # there are some issues with the transparency setting while running ROOT in a docker container realated to openGL. Let's abstain from using it for now
    expectedLimit1Sig.SetFillColor(colorScheme-9)
    #expectedLimit1Sig.SetFillStyle(3001)  # https://root.cern.ch/doc/master/classTAttFill.html
    expectedLimit1Sig.Draw("3 same")

    expectedLimitMedian = getTGraphWithoutError( expectedLimit1Sig )

    expectedLimitMedian.SetLineStyle(2) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    expectedLimitMedian.SetLineWidth(2)
    expectedLimitMedian.SetLineColor(colorScheme)
    expectedLimitMedian.Draw("same")

    extractedLimit.SetLineStyle(1) # https://root.cern.ch/doc/master/classTAttLine.html#L3
    extractedLimit.SetLineWidth(2)
    extractedLimit.SetLineColor(colorScheme)
    extractedLimit.Draw("same")

    expectedLimit2Sig.GetYaxis().Pop()

    #myGraph2.Draw("SAME")
    #myGraph.SetFillColor(ROOT.kRed)  
    #myGraph.Draw("E3") ;

    legend = setupTLegend()
    legend.AddEntry(extractedLimit , "observed Limit"  , "l");
    legend.AddEntry(expectedLimitMedian , "expected limit"  , "l");
    legend.AddEntry(expectedLimit1Sig , "#pm1#sigma expected limit"  , "f");
    legend.AddEntry(expectedLimit2Sig , "#pm2#sigma expected limit"  , "f");
    
    #testTFile = ROOT.TFile( "testTFile.root", "recreate")
    #extractedLimit.SetName("extractedLimit")
    #extractedLimit.Write()
    #testTFile.Close()
    

    legend.Draw()

    canv.Update() #"a3" also seems to work https://root.cern/doc/master/classTGraphPainter


    ##########################################
    #   test tGraphToList and listToTGraph      
    ##########################################


    exampleTGraph = ROOT.TGraphAsymmErrors()

    for x in xrange(-9, 10):
        
        n = exampleTGraph.GetN()

        exampleTGraph.SetPoint( n, x, x**2 )
        exampleTGraph.SetPointError( n, 0,0, 1, 2)


    xList , yList = tGraphToList(exampleTGraph , ySetpoint = "median")
    _ , yHighErrorList =tGraphToList(exampleTGraph , ySetpoint = "yHigh")
    _ , yLowError = tGraphToList(exampleTGraph , ySetpoint = "yLow")

    exampleTGraph.SetLineColor( ROOT.kBlue )
    #exampleTGraph.Draw() # use 'A' option only for first TGraph apparently

    reassembledTGraph =  listToTGraph( xList, yList, yLowList = yLowError, yHighList = yHighErrorList )
    reassembledTGraph.SetLineColor( ROOT.kRed )


    xList2 , yList2 = tGraphToList(reassembledTGraph , ySetpoint = "median")
    _ , yHighErrorList2 =tGraphToList(reassembledTGraph , ySetpoint = "yHigh")
    _ , yLowError2 = tGraphToList(reassembledTGraph , ySetpoint = "yLow")

    #canv2 = ROOT.TCanvas("canvas", "canvas")
    #exampleTGraph.Draw()
    #reassembledTGraph.Draw("same")
    #canv2.Update()

    assert xList == xList2
    assert yList == yList2
    assert yHighErrorList == yHighErrorList2
    assert yLowError == yLowError2




    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
