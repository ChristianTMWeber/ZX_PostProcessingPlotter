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


def createNamedTGraphAsymmErrors( objectName):
    graph = ROOT.TGraphAsymmErrors()
    graph.SetName(objectName)
    return graph

def fillTGraphWithRooRealVar(graph, xFill, yFill):

    if yFill is None: return graph

    pointNr = graph.GetN()

    graph.SetPoint( pointNr, xFill, yFill.getVal() )

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


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
