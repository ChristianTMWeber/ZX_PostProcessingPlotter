import ROOT


TFile = ROOT.TFile("../post_20200907_224104__ZX_Run2_Oct_Signal_TTree.root", "OPEN")

physicsProcessSignal = {15: 343234,
                        20: 343235,
                        25: 343236,
                        30: 343237,
                        35: 343238,
                        40: 343239,
                        45: 343240,
                        50: 343241,
                        55: 343242}

#ROOT.gROOT.SetBatch(True)

TTree = TFile.Get("t_ZXTree")


#TTree.Draw(" llll_m12/1000 : llll_m34/1000" , " weight*(mc_channel_number == 343234 )" )


for mass in [15, 35, 55]:

    histName = "m12_vs_m34_mZd%i_GeV" %mass #

    binScaling = 10

    Zd_pT_Hist = ROOT.TH2F(histName , histName, 55 * binScaling ,10,65, 65 * binScaling , 50, 115)
    Zd_pT_Hist.GetXaxis().SetTitle("m_{34} (GeV)")
    Zd_pT_Hist.GetYaxis().SetTitle("m_{12} (GeV)")
    Zd_pT_Hist.SetStats( False) # remove stats box
    TTree.Draw(" llll_m12/1000 : llll_m34/1000 >> " + histName , " weight*(mc_channel_number == %i )" %physicsProcessSignal[mass] )

    # Zd_pT_Hist.GetXaxis().GetBinWidth(1)
    # Zd_pT_Hist.GetYaxis().GetBinWidth(1)


    canvas = ROOT.TCanvas(histName,histName, 1080, 1080 )
    canvas.SetLeftMargin(0.15)
    Zd_pT_Hist.Draw("COLZ")
    canvas.Update()

    canvas.Print(histName +".png")
    canvas.Print(histName +".pdf")



