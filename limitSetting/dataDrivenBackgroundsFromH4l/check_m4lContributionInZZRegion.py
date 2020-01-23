import ROOT

shapeFile = ROOT.TFile("allShapes.root","OPEN")

shape2l2e = shapeFile.Get("h_m4l_2l2e")
shape2l2mu = shapeFile.Get("h_m4l_2l2mu")

contribution2l2e = shape2l2e.Integral(shape2l2e.GetXaxis().FindBin(0),shape2l2e.GetXaxis().FindBin(115))

contribution2l2mu = shape2l2mu.Integral(shape2l2mu.GetXaxis().FindBin(0),shape2l2mu.GetXaxis().FindBin(115))

totalContribution = ( contribution2l2e + contribution2l2mu) * 139


frullRange_AllChannels = shape2l2e.Clone("frullRange_AllChannels")
frullRange_AllChannels.Add(shape2l2mu)
frullRange_AllChannels.Scale(139.)
#frullRange_AllChannels.Rebin(6)


firstBinNr = frullRange_AllChannels.GetXaxis().FindBin(0)
lastBinNr = frullRange_AllChannels.GetXaxis().FindBin(115)


ZZVRRange_AllChannels = ROOT.TH1D("ZZVR_all_m4l","ZZVR_all_m4l", lastBinNr + 19 , 0 , 115 + 10 )

for x in xrange(lastBinNr+1): 
	ZZVRRange_AllChannels.SetBinContent(x, frullRange_AllChannels.GetBinContent(x) )
	ZZVRRange_AllChannels.SetBinError(x, frullRange_AllChannels.GetBinContent(x) * (0.0284+0.0822) )


#ZZVRRange_AllChannels.Rebin(6)

canvBoth = ROOT.TCanvas("frullRange_AllChannels_and_ZZVRRange_AllChannels","frullRange_AllChannels_and_ZZVRRange_AllChannels")

frullRange_AllChannels.Draw()
ZZVRRange_AllChannels.Draw("same")

canvBoth.Update()



canvSubset = ROOT.TCanvas("ZZVRRange_AllChannels","ZZVRRange_AllChannels")

ZZVRRange_AllChannels.Draw()

canvSubset.Update()


outputTFile = ROOT.TFile("dataDrivenReducible_ZZ_VR_m4l.root","RECREATE")

ZZVRRange_AllChannels.Write()

outputTFile.Close()


import pdb; pdb.set_trace() # import the debugger and instruct it to stop here