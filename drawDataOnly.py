import ROOT

# take a file that we would usually use as input file to 'plotPostProcess.py', and plots the data alone
# this input file to 'plotPostProcess.py' is an output file from the 'ZdZdPostProcessing', 
# a programm from a different repository: https://gitlab.cern.ch/atlas-inst-uvic/physAnalysis/darkSector/ZdZdPostProcessing


def activateATLASPlotStyle():
    # runs the root macro that defines the ATLAS style, and checks that it is active
    # relies on a seperate style macro
    ROOT.gROOT.ProcessLine(".x atlasStyle.C")

    if "ATLAS" in ROOT.gStyle.GetName(): print("ROOT.gStyle: ATLAS style loaded!")
    else:                                warnings.warn("Did not load ATLAS style properly")

    return None


if __name__ == '__main__':


    activateATLASPlotStyle()


    dataTFile = ROOT.TFile("post_20190905_233618_ZX_Run2_BckgSignal_DataUnblinded.root","OPEN")

    SRHist = dataTFile.Get("0").Get("Nominal").Get("h_ZXSR_All_HWindow_m34")

    SRHist.Rebin(2)

    SRHist.GetYaxis().SetTitle("Events / " + str(SRHist.GetBinWidth(1) )+" GeV" )
    SRHist.GetYaxis().SetTitleSize(0.05)
    SRHist.GetYaxis().SetTitleOffset(1.1)
    SRHist.GetYaxis().CenterTitle()


    canvas = ROOT.TCanvas("data","data",1300/2,1300/2);

    SRHist.Draw()


    statsTexts = []

    statsTexts.append( "#font[72]{ATLAS} preliminary")
    statsTexts.append( "#sqrt{s} = 13 TeV, %.1f fb^{-1}" %( 139.0 ) ) 

    statsTexts.append( "Signal Region, 4#mu, 2e2#mu, 2#mu2e, 4e" ) 
    statsTexts.append( "  " ) 
    statsTexts.append( "Data Events" + ": %.2f" %( SRHist.Integral() ) )

    statsTPave=ROOT.TPaveText(0.55,0.55,0.9,0.87,"NBNDC"); statsTPave.SetFillStyle(0); statsTPave.SetBorderSize(0); # and
    for stats in statsTexts:   statsTPave.AddText(stats);


    statsTPave.Draw();

    canvas.Update()





    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here