
import ROOT


def getZXMiniTree( fileName):

    TFile = ROOT.TFile(fileName,"OPEN")
    TTree = TFile.Get("t_ZXTree;1")

    return TTree, TFile # output TFile too, to keep it in scope

def setTH1LineStyleColorWidth(TH1Hist, style = ROOT.kSolid , color = ROOT.kBlack, width = 1):
    # line style reference: https://root.cern.ch/doc/master/classTAttLine.html

    TH1Hist.SetLineStyle( style )
    TH1Hist.SetLineColor( color )
    TH1Hist.SetLineWidth( width )

    return None

def setupTLegend():
    # set up a TLegend, still need to add the different entries
    xOffset = 0.2; yOffset = 0.7
    xWidth  = 0.7; ywidth = 0.2
    TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border
    return TLegend


if __name__ == '__main__':


    ZXTree_Standard , ZXTFile_Standard = getZXMiniTree("post_20210209_030726__ZX_Run2_Oct_UnblindedDataFeb2020_MiniTree_CountLeptons.root")
    ZXTree_PermutationVeto , ZXTFile_PermutationVeto = getZXMiniTree("post_20210209_032351__ZX_Run2_Oct_UnblindedDataFeb2020_PermutationVeto_MiniTree_CountLeptons.root")


    maxNumberOfLeptons = max( [ZXTree_Standard.GetMaximum("nLeptons"), ZXTree_PermutationVeto.GetMaximum("nLeptons")] ) + 1 # add one so that the maximum value does not fall into the overflow bin 

    nLeptonsHist_Standard = ROOT.TH1I("nLeptons","lepton event multiplicity", int(maxNumberOfLeptons-4),4 -0.5,maxNumberOfLeptons -0.5 )
    nLeptonsHist_Standard.GetYaxis().SetTitle("absolute frequency")
    nLeptonsHist_Standard.GetXaxis().SetTitle("number of leptons in event")
    nLeptonsHist_Standard.SetStats( False) # remove stats box


    nLeptonsHist_PermutationVeto = nLeptonsHist_Standard.Clone("nLeptonsPermutationVeto")

    ZX_m4lVar = "llll_m4l"
    ZX_signalRegionCuts = ["%s > 115000" %ZX_m4lVar, "%s < 130000" %ZX_m4lVar] 



    ZXTree_Standard.Draw("nLeptons >> "+ nLeptonsHist_Standard.GetName() ," && ".join(ZX_signalRegionCuts) )
    ZXTree_PermutationVeto.Draw("nLeptons >> "+ nLeptonsHist_PermutationVeto.GetName() ," && ".join(ZX_signalRegionCuts) )

    nLeptonsHist_PermutationVetoedEvents = nLeptonsHist_PermutationVeto.Clone("nLeptonsPermutationVetoedEvents")
    nLeptonsHist_PermutationVetoedEvents.Add(nLeptonsHist_Standard, nLeptonsHist_PermutationVeto, 1, -1)






    setTH1LineStyleColorWidth(nLeptonsHist_Standard               , ROOT.kSolid ,  ROOT.kBlack,  2)
    setTH1LineStyleColorWidth(nLeptonsHist_PermutationVeto        , ROOT.kDashed ,  ROOT.kBlue,   2)
    setTH1LineStyleColorWidth(nLeptonsHist_PermutationVetoedEvents, ROOT.kDotted ,  ROOT.kRed,    2)

    legend = setupTLegend()
    legend.AddEntry(nLeptonsHist_Standard                , "event in standard ZX signal region"               , "l");
    legend.AddEntry(nLeptonsHist_PermutationVeto         , "events in ZX signal region with permutation veto"  , "l");
    legend.AddEntry(nLeptonsHist_PermutationVetoedEvents , "only permutation vetoed events"    , "l");


    tCanvas = ROOT.TCanvas()

    nLeptonsHist_Standard.Draw()
    nLeptonsHist_PermutationVeto.Draw("SAME")
    nLeptonsHist_PermutationVetoedEvents.Draw("SAME")
    legend.Draw()

    tCanvas.Update()

    tCanvas.Print("leptonEventMultiplicity.png")
    tCanvas.Print("leptonEventMultiplicity.pdf")
    tCanvas.Print("leptonEventMultiplicity.root")

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    print( "All done !")
