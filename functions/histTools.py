import ROOT # to do all the ROOT stuff
#import numpy as np # good ol' numpy


# let's say we have a RootHistogramm (like TH1D), and we wanna know the smallest interval (A,B) 
# that contains a fraction f of the histogram.
# This function will return the that interval (A, B)
def getSmallestInterval(myRootHist,desiredWidth = 0.9):
    #if isinstance(myRootHist,ROOT.TH1)

    totalIntegral = myRootHist.Integral();

    nBins = myRootHist.GetNbinsX()

    binInterval = [1, nBins]

    # Let's bruteforce this
    # To determine the smallest intervall that contains a fraction of <desiredWidth> 
    # calculate all possible integrals that contain a fraction of <desiredWidth> of the total integral
    # and select the one where the integral limits are closes together

    for leftIntegralLimit in range(1,nBins): # iterate over the left integral limit
        localIntegral = 0;                   # reset each time the local integral when we start over with the right integral limit
        for rightIntegralLimit in range(leftIntegralLimit,nBins+1): 
            localIntegral = myRootHist.Integral(leftIntegralLimit,rightIntegralLimit); #calculate the integral in the limits
            if localIntegral >= desiredWidth*totalIntegral: 
                # if the integral approaches the desired fraction of the total integral, reset advacne the left integral limit
                # But beforehand check if the limits are closer togehter than our previous limits, and save them if that's the case
                if rightIntegralLimit - leftIntegralLimit < binInterval[1]-binInterval[0]:  binInterval = [leftIntegralLimit, rightIntegralLimit]
                continue

            
    # Get the x-axis values from the bin numbers, and return them
    return  [myRootHist.GetBinLowEdge(binInterval[0]), myRootHist.GetBinLowEdge(binInterval[1]) + myRootHist.GetBinWidth(binInterval[1])]