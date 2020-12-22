import ROOT
import array

def getBinEdges( hist ):

    binEdgesList = []
    nBins = hist.GetNbinsX()
    for binNr in xrange(1,nBins+1):    
        binEdgesList.append(( hist.GetBinLowEdge(binNr), hist.GetBinLowEdge(binNr) + hist.GetBinWidth(binNr) ) )

    return binEdgesList

def getLowerBinEdges( hist ):

    binEdgesList = []
    nBins = hist.GetNbinsX()
    for binNr in xrange(1,nBins+1):    
        binEdgesList.append( hist.GetBinLowEdge(binNr) )

    return binEdgesList


def checkDesiredMergedHistsAreOK( desiredBinList ):

    for lowEdge, HighEdge in desiredBinList: assert lowEdge < HighEdge , "BinEdges within a bin are now monotonically increasing" 

    nDesiredBins = len(desiredBinList)

    for  leftBinIndex in xrange( 0, nDesiredBins -1):
        for rightBinIndex in xrange( leftBinIndex+1, nDesiredBins ): 

            leftBinHighEdge = desiredBinList[leftBinIndex][1]

            rightBinLowEdge = desiredBinList[rightBinIndex][0]

            assert  leftBinHighEdge <=  rightBinLowEdge , "Bin edges are overlapping"

    return None


def varibleSizeRebinHelper(hist, desiredBinList):
    # hist - a TH1
    # desiredBinList a list of tuples like [(1,2) , (5,8) ]

    def isWithinTargetBin(sourceLowEdge, desiredBinList):
        for lowEdge, highEdge in desiredBinList:
            if lowEdge < sourceLowEdge and sourceLowEdge < highEdge: return True
        return False

    checkDesiredMergedHistsAreOK( desiredBinList )

    originalBinEdges = getLowerBinEdges( hist )

    targetBinEdges = []

    for lowBinEdge in originalBinEdges:
        if not isWithinTargetBin(lowBinEdge,desiredBinList): targetBinEdges.append(lowBinEdge)

    targetBinEdgesArray = array.array( "d", targetBinEdges)      # can also use "d" here for doubles

    rebinnedHist = hist.Rebin(len(targetBinEdgesArray) -1, hist.GetName(), targetBinEdgesArray )

    return rebinnedHist




if __name__ == '__main__':


    testHist = ROOT.TH1F('testHist','testHist',8,0,8)

    for binNr in range(0,9) :  testHist.SetBinContent(binNr,1)


    testHistRebinned =  varibleSizeRebinHelper(testHist, [ (2,5)])





    file = ROOT.TFile("../post_20200915_171012_mc16ade_ZX_Run2_SignalBackgroundDataFeb2020Unblinded.root")

    file.Get("0").ls()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
