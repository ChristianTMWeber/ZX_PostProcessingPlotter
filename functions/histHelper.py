# histHelper.py
# some functions that help me to deal with histograms

import ROOT # to do all the ROOT stuff

def mergeTHStackHists(myTHStack):
    # Take a THStack and merge all the histograms comprising it into a single new one
    # requires that all the thists hace identical binning

    ROOT.SetOwnership(myTHStack, False) # We need to set this, to aoid a segmentation fault: https://root-forum.cern.ch/t/crash-on-exit-with-thstack-draw-and-gethists/11221
    constituentHists =  myTHStack.GetHists() 

    mergedHist  = constituentHists[0].Clone( constituentHists.GetName() + "_merged")

    for hist in constituentHists:
        if hist != constituentHists[0]: mergedHist.Add(hist)

    return mergedHist

def getFirstAndLastNonEmptyBinInHist(hist, offset = 0, adjustXAxisRange = False):

    if isinstance(hist,ROOT.THStack):  hist = mergeTHStackHists(hist)

    nBins = hist.GetNbinsX()

    first =0 ;last=0

    for n in xrange(1,nBins+1): 
        if hist.GetBinContent(n) != 0: 
            first = n ; break
    for n in xrange(nBins+1,1,-1):
        if hist.GetBinContent(n) != 0: 
            last = n ; break

    #if adjustXAxisRange:

    if first is not 0: first -= offset
    if last  is not 0: last  += offset


    return (first, last)

def binNrByXValue(hist, xVal):  # tells me the bin number for the given x-axis value. Usefull for filling histograms, which have to be filled by bin numbr: hist.SetBinContent( binNumber, binContent)
    return hist.GetXaxis().FindBin(xVal)

def fillBin(hist, xVal, yVal, yError = None):
    binNr = hist.GetXaxis().FindBin(xVal)
    hist.SetBinContent(binNr, yVal )
    if yError is not None: hist.SetBinError(binNr, yError )
    return None

