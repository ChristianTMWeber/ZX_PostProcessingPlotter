import ROOT

import  makeReducibleShapes



reducibleFile = ROOT.TFile("../limitSetting/preppedHistsV2_mc16ade_1GeVBins_unblinded.root" , "OPEN")
h4lReducibleHist = reducibleFile.Get("ZXSR").Get("reducibleDataDriven").Get("Nominal").Get("All").Get("h_m34_All")

reducibleTFile = ROOT.TFile("../limitSetting/dataDrivenBackgroundsFromH4l/allShapes.root", "OPEN")


histName_2l2e  = "h_m34_2l2e"
histName_2l2mu = "h_m34_2l2mu"

hist2l2eImproperBins = reducibleTFile.Get( histName_2l2e )

hist2l2muImproperBins = reducibleTFile.Get( histName_2l2mu )


h4lReducibleHist = hist2l2eImproperBins.Clone()

for binNr in xrange(1, h4lReducibleHist.GetNbinsX()  +1):  h4lReducibleHist.AddBinContent(binNr, hist2l2muImproperBins.GetBinContent(binNr))

#h4lReducibleHist.Add(hist2l2eImproperBins)

h4lReducibleHist.Scale( 10.6 / h4lReducibleHist.Integral() )






th1Dict = makeReducibleShapes.getReducibleTH1s(TH1Template = None , convertXAxisFromMeVToGeV = True)


myReducibleHist = th1Dict["all"]




myReducibleWithH4lBinning =  h4lReducibleHist.Clone()
myReducibleWithH4lBinning.Reset("ICESM")

for sourceBin in xrange(1 , myReducibleHist.GetNbinsX()  +1 ):

    sourceMass = myReducibleHist.GetBinLowEdge(sourceBin)

    sinkBin =    h4lReducibleHist.GetXaxis().FindBin( sourceMass)

    myReducibleWithH4lBinning.AddBinContent(sinkBin, myReducibleHist.GetBinContent(sourceBin) )


myReducibleWithH4lBinning.SetLineColor(ROOT.kRed )


canv = ROOT.TCanvas()

myReducibleWithH4lBinning.Draw()
h4lReducibleHist.Draw("same")

canv.Update()



import pdb; pdb.set_trace() # import the debugger and instruct it to stop here