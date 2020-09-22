import ROOT


aTFile = ROOT.TFile("h4lMinitrees/mc16_13TeV.364108.Sherpa_221_NNPDF30NNLO_Zmumu_MAXHTPTV140_280_BFilter.root", "OPEN")

aTTree = aTFile.Get("tree_incl_all")




xVar = ROOT.RooRealVar("mZ2_unconstrained","mZ2_unconstrained", 0, 100)

xWeight = ROOT.RooRealVar("weight_corr","weight_corr", -100, 100)

anArgSet = ROOT.RooArgSet(xVar,xWeight)

aDataSet = ROOT.RooDataSet("h4lData", "h4lData", aTTree, anArgSet)

aDataSetWeighted = ROOT.RooDataSet("h4lData", "h4lData", aTTree, anArgSet, "" , "weight_corr")



kest1 = ROOT.RooKeysPdf("kest1", "kest1", xVar, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)

kest2 = ROOT.RooKeysPdf("kest1", "kest1", xVar, aDataSetWeighted) #, ROOT.RooKeysPdf.MirrorBoth)#                        ROOT.RooKeysPdf.MirrorBoth)


canv = ROOT.TCanvas()

xFrameHists = xVar.frame() # frame to plot my PDFs on
aDataSet.plotOn(xFrameHists)
aDataSetWeighted.plotOn(xFrameHists, ROOT.RooFit.LineColor(ROOT.kGreen+1))

kest1.plotOn(xFrameHists)
kest2.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kRed+1))


xFrameHists.Draw()
canv.Update()


# myTTree.Draw("llll_m34","weight*(llll_m4l>115000 && llll_m4l<130000)")

import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
