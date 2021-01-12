import ROOT


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    xOffset = 0.5; yOffset = 0.7
    xWidth  = 0.5; ywidth = 0.2
    TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border
    return TLegend

if __name__ == '__main__':

    TFile = ROOT.TFile("post_20210111_185403__ZX_Run2_345060Background_MiniTreeLeptonPT.root","OPEN")

    TTree = TFile.Get("t_ZXTree")


    ptVsScaleFactorHistUP = ROOT.TH2F( "ScaleFactorHistUP", " pT - ID scale factor correlation", 500, 0,500,  600  , 0.7, 1.3)
    ptVsScaleFactorHistUP.SetStats( False)
    ptVsScaleFactorHistUP.GetXaxis().SetTitle("pT1+pT2+pT3+pT4 (GeV)")
    ptVsScaleFactorHistUP.GetYaxis().SetTitle("scaleFactor ratio (unitless)")
    ptVsScaleFactorHistUP.SetFillColor(ROOT.kBlack)

    #ptVsScaleFactorHistUP.GetYaxis().SetRangeUser(0.7,1.3)


    ptVsScaleFactorHistDown = ROOT.TH2F( "ScaleFactorHistDOWN", "", 500, 0,500,  600  , 0.7, 1.3)
    ptVsScaleFactorHistDown.SetStats( False)
    ptVsScaleFactorHistDown.GetXaxis().SetTitle("pT1+pT2+pT3+pT4 (GeV)")
    ptVsScaleFactorHistDown.GetYaxis().SetTitle("scaleFactor ratio (unitless)")
    ptVsScaleFactorHistDown.SetMarkerColor(ROOT.kBlue)
    ptVsScaleFactorHistDown.SetFillColor(ROOT.kBlue)

    TTree.Draw(" llll_scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up / llll_scaleFactor : (pt1+pt2+pt3+pt4 )/ 1000  >> " + ptVsScaleFactorHistUP.GetName())
    TTree.Draw(" llll_scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1down / llll_scaleFactor : (pt1+pt2+pt3+pt4 )/ 1000 >>" + ptVsScaleFactorHistDown.GetName())
    

    legend1 = setupTLegend()
    legend1.AddEntry(ptVsScaleFactorHistUP , "scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up / scaleFactorNominal" , "pf");
    legend1.AddEntry(ptVsScaleFactorHistDown , "scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1down / scaleFactorNominal" , "pf");


    canvas = ROOT.TCanvas("scaleFactorCanvas","scaleFactorCanvas" ,1920/2,1080/2)
    ptVsScaleFactorHistUP.Draw()
    ptVsScaleFactorHistDown.Draw("same")
    legend1.Draw()
    canvas.Update()
    

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    lepton1pTHist = ROOT.TH1F("lepton1pTHist","lepton pT distribution", 100, 0,100)  ; lepton1pTHist.SetLineWidth(2) ; lepton1pTHist.SetStats( False) # remove stats box
    lepton1pTHist.GetXaxis().SetTitle("lepton pT (GeV)")
    lepton2pTHist = lepton1pTHist.Clone("lepton2pTHist" ) ; lepton2pTHist.SetLineColor( ROOT.kRed )   ; lepton2pTHist.SetLineWidth(1) #lepton2pTHist.SetLineStyle( ROOT.kDashDotted  )
    lepton3pTHist = lepton1pTHist.Clone("lepton3pTHist" ) ; lepton3pTHist.SetLineColor( ROOT.kGreen+1 )  ; lepton3pTHist.SetLineWidth(3) ; lepton3pTHist.SetLineStyle( ROOT.kDashed )
    lepton4pTHist = lepton1pTHist.Clone("lepton4pTHist" ) ; lepton4pTHist.SetLineColor( ROOT.kBlue ) ; lepton4pTHist.SetLineWidth(1) ;# lepton4pTHist.SetLineStyle( ROOT.kDashed )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    TTree.Draw(" pt1 /1000  >> " + lepton1pTHist.GetName(),  "weight" )
    TTree.Draw(" pt2 /1000  >> " + lepton2pTHist.GetName(),  "weight" )
    TTree.Draw(" pt3 /1000  >> " + lepton3pTHist.GetName(),  "weight" )
    TTree.Draw(" pt4 /1000  >> " + lepton4pTHist.GetName(),  "weight" )



    leptonpTHistMaxima = [lepton1pTHist.GetMaximum(),lepton2pTHist.GetMaximum(),lepton3pTHist.GetMaximum(),lepton4pTHist.GetMaximum()]

    lepton1pTHist.GetYaxis().SetRangeUser(0, max(leptonpTHistMaxima) * 1.1)
    

    legend2 = setupTLegend()

    legend2.AddEntry(lepton1pTHist , "lepton 1 pT" , "l");
    legend2.AddEntry(lepton2pTHist , "lepton 2 pT" , "l");
    legend2.AddEntry(lepton3pTHist , "lepton 3 pT" , "l");
    legend2.AddEntry(lepton4pTHist , "lepton 4 pT" , "l");


    canvas2 = ROOT.TCanvas("lepton pT canvas","lepton pT canvas" ,1920/2,1080/2)

    lepton1pTHist.Draw("HIST")
    lepton2pTHist.Draw("HIST same")
    lepton3pTHist.Draw("HIST same")
    lepton4pTHist.Draw("HIST same")

    legend2.Draw()

    canvas2.Update()

    #TTree.Draw(" pt1+pt2+pt3+pt4 : llll_scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up ")
    #TTree.Draw("llll_scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up : llll_scaleFactorEL_EFF_ID_TOTAL_1NPCOR_PLUS_UNCOR__1up")

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here