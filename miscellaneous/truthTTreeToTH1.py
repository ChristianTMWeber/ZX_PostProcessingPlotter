import ROOT


TFile = ROOT.TFile("ZX_CombinedTruthTTree4.root", "OPEN")


ROOT.gROOT.SetBatch(True)

for mass in [15, 35, 55]:

    TTree = TFile.Get("truthTree_Zd_%i_GeV"%mass)


    Zd_pT_Hist = ROOT.TH1D("Zd_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
    Zd_pT_Hist.GetXaxis().SetTitle("Z_{d} pT (GeV)")
    TTree.Draw(" Zd_pT >> Zd_pT_Hist%i" %mass)


    Zd_eta_Hist = ROOT.TH1D("Zd_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
    Zd_eta_Hist.GetXaxis().SetTitle("Z_{d} #eta")
    TTree.Draw(" Zd_eta >> Zd_eta_Hist%i" %mass)


    Z_pT_Hist = ROOT.TH1D("Z_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
    Z_pT_Hist.GetXaxis().SetTitle("Z pT (GeV)")
    TTree.Draw(" Z_pT >> Z_pT_Hist%i" %mass)


    Z_eta_Hist = ROOT.TH1D("Z_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
    Z_eta_Hist.GetXaxis().SetTitle("Z #eta")
    TTree.Draw(" Z_eta >> Z_eta_Hist%i" %mass)




    ll12_eta_Hist = ROOT.TH1D("ll12_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
    ll12_eta_Hist.GetXaxis().SetTitle("l_{1}, l_{2}lepton #eta")
    TTree.Draw(" l1_eta >> ll12_eta_Hist%i" %mass)
    TTree.Draw(" l2_eta >> ll12_eta_Hist%i" %mass)


    ll12_pT_Hist = ROOT.TH1D("ll12_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll  pT distribution, m_{Zd} = %i GeV"%mass, 100,0,100)
    ll12_pT_Hist.GetXaxis().SetTitle("l_{1}, l_{2} lepton pT (GeV)")
    TTree.Draw(" l1_pT >> ll12_pT_Hist%i" %mass)
    TTree.Draw(" l2_pT >> ll12_pT_Hist%i" %mass)



    ll34_eta_Hist = ROOT.TH1D("ll34_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
    ll34_eta_Hist.GetXaxis().SetTitle("l_{3}, l_{4} lepton #eta")
    TTree.Draw(" l3_eta >> ll34_eta_Hist%i" %mass)
    TTree.Draw(" l4_eta >> ll34_eta_Hist%i" %mass)


    ll34_pT_Hist = ROOT.TH1D("ll34_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll  pT distribution, m_{Zd} = %i GeV"%mass, 100,0,100)
    ll34_pT_Hist.GetXaxis().SetTitle("l_{3}, l_{4} lepton pT (GeV)")
    TTree.Draw(" l3_pT >> ll34_pT_Hist%i" %mass)
    TTree.Draw(" l4_pT >> ll34_pT_Hist%i" %mass)





    ll12_invMass_Hist = ROOT.TH1D("ll12_invMass_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll , ll invariant mass distribution, m_{Zd} = %i GeV"%mass, 100, 50, 115)
    ll12_invMass_Hist.GetXaxis().SetTitle("m_{12} (GeV)")
    TTree.Draw(" ll12_mInv >> ll12_invMass_Hist%i" %mass)


    ll34_invMass_Hist = ROOT.TH1D("ll34_invMass_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll , ll invariant mass distribution, m_{Zd} = %i GeV"%mass, 100, mass-.5,mass+0.5)
    ll34_invMass_Hist.GetXaxis().SetTitle("m_{34} (GeV)")
    TTree.Draw(" ll34_mInv >> ll34_invMass_Hist%i" %mass)


    for hist in [ Zd_pT_Hist, Zd_eta_Hist, Z_pT_Hist, Z_eta_Hist, ll12_eta_Hist, ll12_pT_Hist, ll34_eta_Hist, ll34_pT_Hist, ll12_invMass_Hist, ll34_invMass_Hist]:

        canvasName = hist.GetName() + "_%GeV" %mass
        canvas = ROOT.TCanvas(canvasName,canvasName, 1920/2, 1090 )
        hist.Draw()
        canvas.Update()

        canvas.Print(canvasName +".png")
        canvas.Print(canvasName +".pdf")


#fillHist = ROOT.TH1D(weightVariation,weightVariation,200,0,100)








import pdb; pdb.set_trace() # import the debugger and instruct it to stop here