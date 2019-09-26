import ROOT # to do all the ROOT stuff
import os
import struct

class histSampler:

    def __init__(self, seed = None ):


        if seed is None: # get the seed randomly form the us
            byteSeed = os.urandom(4) # get for bytes (32 bits) of randomness from the os
            seed = struct.unpack("<L",byteSeed )[0] # convert the 4 bytes into a long (L) with little endian ancoding (<)

        self.rootRandomGen = ROOT.TRandomMixMax(seed)

        return None

    def sampleFromTH1(self, hist ):

        histSample = hist.Clone( hist.GetName() +"Sample" )
        histSample.Reset()

        histSample.SetBinErrorOption( ROOT.TH1.kNormal )       

        for n in xrange(0, hist.GetNbinsX() +2 ):  # start at 0 for the underflow, end at +2 to reach also the overflow
            poisMean = hist.GetBinContent(n)
            histSample.SetBinContent(n, self.rootRandomGen.Poisson(poisMean) )
   
        return histSample



if __name__ == '__main__':

    ######################################################################
    # prepare PDFs that we will turn into TH1s. We will use those TH1s to test the sampling
    ######################################################################
    x = ROOT.RooRealVar("indepVariable","indepVariable",  -10. ,10.)

    # gaussian PDF, 
    mean1  = ROOT.RooRealVar("mean1" , "mean of gaussian" , 0, -10. , 10. )
    sigma1 = ROOT.RooRealVar("sigma1", "width of gaussian", 1. , -10. , 10. )
    gaussianPDF1 = ROOT.RooGaussian("Gaussian1", "Gaussian1", x, mean1, sigma1) 


    myHistSampler = histSampler()


    nBins = 20
    histA = gaussianPDF1.createHistogram("indepVariable",nBins)


    histA.Scale(10)

    histASample = myHistSampler.sampleFromTH1(histA)

    nIterations = 1000

    for n in xrange(1,nIterations):
        histASample.Add( myHistSampler.sampleFromTH1(histA) )

    histASample.SetBinErrorOption( ROOT.TH1.kPoisson)    

    histASample.Scale( 1./nIterations )

    canv = ROOT.TCanvas("canv", "canv")

    histA.SetLineColor(ROOT.kRed)
    histA.Draw("HIST")

    histASample.Draw("SAME")

    canv.Update()

    print( histASample.GetBinError(10) )




    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

