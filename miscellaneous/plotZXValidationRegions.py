import ROOT
import numpy as np

import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess

import functions.tGraphHelpers as graphHelper


def m12UpperLimit( m4l ):

    if m4l < 130 : return 106.
    else :         return  97.2

def m12LowerLimit( m4l ):
    
    if m4l < 130 : return 50.
    else :         return 85.2


def m34UpperLimit( m4l ): return 115.


def m34LowerLimit( m4l ):
    
    if   m4l <= 100. : return 5.
    elif m4l <= 105. : return ((m4l - 100.)*1.4 + 5.)
    elif m4l <= 140. : return 12.
    elif m4l <= 190. : return ((m4l - 140.)*0.76 + 12.)
    else:              return 50.


def prepCanvas(canvasName = "VRVisualizationCanvas"):

    canvasWidth = 20.00025*10*2.6; canvasHeight = 20.320*10*2.6
    canvas = ROOT.TCanvas(canvasName,canvasName, int(canvasWidth),int(canvasHeight))

    canvas.SetLeftMargin(0.16)
    canvas.SetBottomMargin(0.12)

    return canvas


def setupTLegend( nColumns = 2, boundaries = (0.15,0.70,0.55,0.95)):
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

def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x ../atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None

def makeTGraphs():
    m4lVR1 = range(50, 115); m4lVR1.append(114.99999999999)
    m4lSR  = range(115, 130); m4lSR.append(129.99999999999)
    m4lVR2 = range(130, 170+1)

    m4lList = []

    for eachList in [m4lVR1,m4lSR,m4lVR2]:  m4lList.extend(eachList)

    m12HighList = [m12UpperLimit( m4l ) for m4l in m4lList]
    m12LowList  = [m12LowerLimit( m4l ) for m4l in m4lList]


    m34HighList = [m34UpperLimit( m4l ) for m4l in m4lList]
    m34LowList  = [m34LowerLimit( m4l ) for m4l in m4lList]

    m12HighGraph = graphHelper.listToTGraph(m4lList, m12HighList)
    m12LowGraph  = graphHelper.listToTGraph(m4lList, m12LowList)

    m34HighGraph = graphHelper.listToTGraph(m4lList, m34HighList)
    m34LowGraph  = graphHelper.listToTGraph(m4lList, m34LowList)

    VR1Graph = graphHelper.listToTGraph(m4lVR1, [(m34LowerLimit(m4l)+ m34UpperLimit(m4l))/2 for m4l in m4lVR1], [m34LowerLimit(m4l) for m4l in m4lVR1], [m34UpperLimit(m4l) for m4l in m4lVR1]) 
    VR2Graph = graphHelper.listToTGraph(m4lVR2, [(m34LowerLimit(m4l)+ m34UpperLimit(m4l))/2 for m4l in m4lVR2], [m34LowerLimit(m4l) for m4l in m4lVR2], [m34UpperLimit(m4l) for m4l in m4lVR2]) 
    SRGraph = graphHelper.listToTGraph(m4lSR, [(m34LowerLimit(m4l)+ m34UpperLimit(m4l))/2 for m4l in m4lSR], [m34LowerLimit(m4l) for m4l in m4lSR], [m34UpperLimit(m4l) for m4l in m4lSR]) 


    VR1GraphM12 = graphHelper.listToTGraph(m4lVR1, [(m12LowerLimit(m4l)+ m12UpperLimit(m4l))/2 for m4l in m4lVR1], [m12LowerLimit(m4l) for m4l in m4lVR1], [m12UpperLimit(m4l) for m4l in m4lVR1]) 
    VR2GraphM12 = graphHelper.listToTGraph(m4lVR2, [(m12LowerLimit(m4l)+ m12UpperLimit(m4l))/2 for m4l in m4lVR2], [m12LowerLimit(m4l) for m4l in m4lVR2], [m12UpperLimit(m4l) for m4l in m4lVR2]) 
    SRGraphM12  = graphHelper.listToTGraph(m4lSR, [(m12LowerLimit(m4l)+ m12UpperLimit(m4l))/2 for m4l in m4lSR], [m12LowerLimit(m4l) for m4l in m4lSR], [m12UpperLimit(m4l) for m4l in m4lSR]) 


    for graph in m12HighGraph, m12LowGraph, m34HighGraph, m34LowGraph, VR1Graph, VR2Graph, SRGraph:
        graph.GetXaxis().SetRangeUser( min(m4lList), max(m4lList))
        graph.GetYaxis().SetRangeUser( 0, 150)
        graph.SetLineWidth(2)
        graph.GetXaxis().SetTitle("m_{4l}")


        yAxisTitleSize = 0.055
        graph.GetYaxis().SetTitleSize(yAxisTitleSize)
        graph.GetYaxis().SetTitleOffset(0)
        graph.GetXaxis().SetTitleOffset(1.0)
        graph.GetXaxis().SetTitleSize(0.055)


    for graph in [m12HighGraph, m12LowGraph]: graph.SetLineStyle(2)


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return m12HighGraph, m12LowGraph, m34HighGraph, m34LowGraph, VR1Graph, VR2Graph, SRGraph, VR1GraphM12, VR2GraphM12, SRGraphM12



if __name__ == '__main__':

    #activateATLASPlotStyle()


    alternatePlot = True


    ### make TGraphs


    m12HighGraph, m12LowGraph, m34HighGraph, m34LowGraph, VR1Graph, VR2Graph, SRGraph, VR1GraphM12, VR2GraphM12, SRGraphM12 = makeTGraphs()


    VR1Color = ROOT.kRed
    VR2Color = ROOT.kGreen 
    SRColor = ROOT.kBlue 


    VR1Graph.SetFillColorAlpha(VR1Color ,0.1)
    VR2Graph.SetFillColorAlpha(VR2Color  ,0.1)
    SRGraph.SetFillColorAlpha( SRColor ,0.1)

    VR1GraphM12.SetFillColor(VR1Color)
    VR2GraphM12.SetFillColor(VR2Color)
    SRGraphM12.SetFillColor( SRColor)

    VR1GraphM12.SetFillStyle(3013)
    VR2GraphM12.SetFillStyle(3013)
    SRGraphM12.SetFillStyle(3013)

    legend = setupTLegend(nColumns = 3, boundaries = (0.2, 0.8 ,0.9,0.9) )

    if alternatePlot: legend = setupTLegend(nColumns = 3, boundaries = (0.2, 0.75 ,0.9,0.9) )

    legend.AddEntry(VR1Graph , "ZX VR c" , "f");
    legend.AddEntry(SRGraph  , "ZX SR" , "f");
    legend.AddEntry(VR2Graph , "ZX VR d" , "f");

    if alternatePlot:
        legend.AddEntry(m12HighGraph , "m_{12} bounds" , "l");
        legend.AddEntry(m34HighGraph , "m_{34} bounds" , "l");


    regionsMultiGraph = ROOT.TMultiGraph()
    for graph in [VR1Graph, VR2Graph, SRGraph]: 
        graph.GetXaxis().SetRangeUser( 50, 170)
        regionsMultiGraph.Add(graph)



    regionsMultiGraphM12 = ROOT.TMultiGraph()
    for graph in [VR1GraphM12, VR2GraphM12, SRGraphM12]: regionsMultiGraphM12.Add(graph)

    limitsMultiGraph = ROOT.TMultiGraph()
    for graph in [m12HighGraph, m12LowGraph, m34HighGraph, m34LowGraph]: limitsMultiGraph.Add(graph)

    regionsMultiGraph.GetXaxis().SetTitle("m_{4l} [GeV]")
    regionsMultiGraph.GetYaxis().SetTitle("m_{ll'} [GeV]")




    regionsMultiGraph.GetYaxis().SetRangeUser( 0, 150)
    

    canvas = prepCanvas()

    #VR1Graph.Draw("A3")

    regionsMultiGraph.Draw("A3")
    regionsMultiGraphM12.Draw("3")
    limitsMultiGraph.Draw()

    #SRGraph.Draw("3 same")

    latexText = ROOT.TLatex()
    #latexText.SetTextAlign(10)


    if not alternatePlot:

        textScale = 0.75

        latexText.DrawLatex( 90 ,m12UpperLimit( 90 ) -6,"#scale[%f]{#color[1]{#bf{m_{12} upper limit}}}" %(textScale) )
        latexText.DrawLatex( 90 ,m12LowerLimit( 90 ) -6,"#scale[%f]{#color[1]{#bf{m_{12} lower limit}}}" %(textScale) )

        latexText.DrawLatex(60,m34UpperLimit( 60 ) +3,"#scale[%f]{#color[1]{#bf{m_{34} upper limit}}}" %(textScale) )
        latexText.DrawLatex(60,m34LowerLimit( 60 ) +3,"#scale[%f]{#color[1]{#bf{m_{34} lower limit}}}" %(textScale) )

    legend.Draw()

    canvas.Update()

    ROOT.gPad.RedrawAxis("G") # to make sure that the Axis ticks are above the histograms


    if alternatePlot : 
        canvas.Print("validationRegionPlot_b.pdf")
        canvas.Print("validationRegionPlot_b.root")
    else :             
        canvas.Print("validationRegionPlot_a.pdf")
        canvas.Print("validationRegionPlot_a.root")
    


    #####   canvas2   #####


    canvas2 = prepCanvas( canvasName = "VRVisualizationM34" )

    #VR1Graph.Draw("A3")

    regionsMultiGraph.Draw("A3")
    regionsMultiGraph.GetYaxis().SetTitle("m_{34} [GeV]")

    limitsMultiGraph2 = ROOT.TMultiGraph()
    for graph in [ m34HighGraph, m34LowGraph]: limitsMultiGraph2.Add(graph)
    limitsMultiGraph2.Draw()


    #regionsMultiGraphM12.Draw("3")
    #limitsMultiGraph.Draw()

    #SRGraph.Draw("3 same")


    legend2 = setupTLegend(nColumns = 3, boundaries = (0.2, 0.8 ,0.9,0.9) )
    #if alternatePlot: legend = setupTLegend(nColumns = 3, boundaries = (0.2, 0.75 ,0.9,0.9) )
    legend2.AddEntry(VR1Graph , "ZX VR c" , "f");
    legend2.AddEntry(SRGraph  , "ZX SR" , "f");
    legend2.AddEntry(VR2Graph , "ZX VR d" , "f");
    legend2.Draw()

    canvas2.Update()

    canvas2.Print("validationRegionPlot_M34.pdf")
    canvas2.Print("validationRegionPlot_M34.root")



    #####   canvas3   #####


    canvas3 = prepCanvas( canvasName = "VRVisualizationM12" )

    #VR1Graph.Draw("A3")

    VR1GraphM12.SetFillStyle(1001)  ; VR1GraphM12.SetFillColorAlpha(VR1Color ,0.1)
    VR2GraphM12.SetFillStyle(1001)  ; VR2GraphM12.SetFillColorAlpha(VR2Color  ,0.1)
    SRGraphM12.SetFillStyle(1001)  ; SRGraphM12.SetFillColorAlpha( SRColor ,0.1)

    regionsMultiGraphM12.Draw("A3")

    regionsMultiGraphM12.GetYaxis().SetTitle("m_{12} [GeV]")
    regionsMultiGraphM12.GetYaxis().SetTitle("m_{12} [GeV]")
    regionsMultiGraphM12.GetXaxis().SetTitle("m_{4l} [GeV]")
    regionsMultiGraphM12.GetYaxis().SetRangeUser( 0, 150)
    regionsMultiGraphM12.GetXaxis().SetRangeUser( 50, 170)

    limitsMultiGraph3 = ROOT.TMultiGraph()
    for graph in [ m12HighGraph, m12LowGraph]: 
        graph.SetLineStyle(1)
        limitsMultiGraph3.Add(graph)
    limitsMultiGraph3.Draw()
    #regionsMultiGraphM12.Draw("3")
    #limitsMultiGraph.Draw()

    #SRGraph.Draw("3 same")


    legend3 = setupTLegend(nColumns = 3, boundaries = (0.2, 0.8 ,0.9,0.9) )
    #if alternatePlot: legend = setupTLegend(nColumns = 3, boundaries = (0.2, 0.75 ,0.9,0.9) )
    legend3.AddEntry(VR1Graph , "ZX VR c" , "f");
    legend3.AddEntry(SRGraph  , "ZX SR" , "f");
    legend3.AddEntry(VR2Graph , "ZX VR d" , "f");
    legend3.Draw()

    canvas3.Update()

    canvas3.Print("validationRegionPlot_M12.pdf")
    canvas3.Print("validationRegionPlot_M12.root")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

