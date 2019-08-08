import investigateM4lCut as m4lCut  # this is what we wanna test

import ROOT
import numpy as np


np.random.seed(0) # set seed


# test conversion between np.array and TH2
randArray = np.random.rand(7,7)

testTH2 = ROOT.TH2D("randArray","randArray", 7, 0,7,7,0,7)

m4lCut.fillTHWithNumpyArray(testTH2,randArray)

checkArray = m4lCut.convertTHtoNumpyArray(testTH2 )

assert np.all(checkArray == randArray)


# test construction of 'optimal significance mask'

mockSignal = np.zeros([7,7])
mockSignal[3, :] = 1
mockSignal[4, 2:-2] = 1

mockBackround = mockSignal.copy()

mask = m4lCut.constructOptimalSignificanceMask(mockSignal, mockBackround)

assert np.all(mask == mockSignal)

mockSignal2 = mockSignal.copy()
mockSignal2[1,3] = 1
mockSignal2[3,3]=2

mask2 = m4lCut.constructOptimalSignificanceMask(mockSignal2, mockBackround)

assert np.all(mask2 == mockSignal)


mockSignal2[4,1]=-1

mask3 = m4lCut.constructOptimalSignificanceMask(mockSignal2, mockBackround)
assert np.all(mask3 == mockSignal)

mockSignal2[4,5]=0.1
mockBackround[4,5]=1e4
mask4 = m4lCut.constructOptimalSignificanceMask(mockSignal2, mockBackround)

assert np.all(mask4 == mockSignal)

# check filling between TH1 and 1d array

mask1d = np.sign( mask.sum(axis=1) ) # these 1d 
maskTH1D = testTH2.ProjectionX(); m4lCut.fillTHWithNumpyArray(maskTH1D,mask1d)

assert np.all( mask1d == m4lCut.convertTHtoNumpyArray(maskTH1D) )

print("All good!")








#testTH2.Draw("COLZ")

#import pdb; pdb.set_trace() # import the debugger and instruct it to stop here