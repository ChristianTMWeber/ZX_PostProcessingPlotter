import ROOT # to do all the ROOT stuff
import numpy as np # good ol' numpy


def histToNPArray(hist):

    outArray = np.zeros( hist.GetNbinsX() )

    for x in xrange(1,hist.GetNbinsX()+1): # we are ignoring the over and underflow here. Otherweise we would do xrange(0,hist.GetNbinsX()+2)
        outArray[x-1] = hist.GetBinContent(x)

    return outArray


def histErrorToNPArray(hist):

    outArray = np.zeros( hist.GetNbinsX() )

    for x in xrange(1,hist.GetNbinsX()+1): # we are ignoring the over and underflow here. Otherweise we would do xrange(0,hist.GetNbinsX()+2)
        outArray[x-1] = hist.GetBinError(x)

    return outArray

def listOfTH1ToNumpyMatrix(listOfTh1):

    listOfNumpyArrays = [ histToNPArray(hist) for hist in listOfTh1 ]
    histMatrix = np.array(listOfNumpyArrays) # histMatrix[ histNumber , binNr]

    return histMatrix