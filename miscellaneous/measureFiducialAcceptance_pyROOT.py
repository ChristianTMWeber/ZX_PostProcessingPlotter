#   do the following first:
#   asetup AthAnalysis,21.2.94,here
#
#   https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/AthAnalysis#How_to_inspect_files_in_pyROOT
#   https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/SoftwareTutorialxAODAnalysisInCMake#Using_PyROOT
#
#   python truthPlots_pyROOT.py /direct/usatlas+u/chweber/usatlasdata/signalDAODs/mc16_13TeV.343234.MadGraphPythia8EvtGen_A14NNPDF23LO_HAHMggfZZd4l_mZd15.deriv.DAOD_HIGG2D1.e4551_e5984_a875_r9364_r9315_p3654/DAOD_HIGG2D1.16330910._000004.pool.root.1 --nEventsToProcess 100

import ROOT
import argparse # to parse command line options
import re


#def particleToLorenzVector(particle): return ROOT.Math.PxPyPzEVector(particle.px(), particle.py(), particle.pz() , particle.e())
def particleToLorenzVector(particle): return lorentzVectorWithPDGId(particle.px(), particle.py(), particle.pz() , particle.e(), particle.pdgId())


class lorentzVectorWithPDGId(ROOT.Math.PxPyPzEVector): 
    # I need a Lorentz vector that also stores the particle Id Number, so that I can keep track pf flavor and charge
    # let's make such an object, by inheriting from ROOT.Math.PxPyPzEVector

    m_pdgId = None

    def __init__(self,px,py,pz,E, pdgId=None):
        super(lorentzVectorWithPDGId,self).__init__(px,py,pz,E) # I believe super(...) makes it that I inherit all of the methods from 
        self.m_pdgId = pdgId

    def setPdgId(self,pdgId): self.m_pdgId = pdgId
    #def getPdgId(self,pdgId): return self.m_pdgId
    def pdgId(self): return self.m_pdgId

    def __add__(self, other): # redefine the addition operator '+'. I want to keep the pdgId under certain circumstances

        outputLorentzVec = lorentzVectorWithPDGId( self.px()+other.px(), self.py()+other.py(), self.pz()+other.pz(), self.e()+other.e())

        if self.m_pdgId == other.pdgId(): outputLorentzVec.setPdgId(self.m_pdgId)
        elif self.m_pdgId == 22 : outputLorentzVec.setPdgId(other.pdgId()) # pdgId 22 = photon
        elif other.pdgId() == 22: outputLorentzVec.setPdgId(self.m_pdgId)

        return outputLorentzVec


def getDeltaR(particle1, particle2): return ( (particle1.eta() - particle2.eta())**2 + (particle1.phi() - particle2.phi())**2)**0.5
  
def findLeptonToDecorateWithPhoton( photon, leptonList):

    deltaRList = []
    for lepton in leptonList: deltaRList.append( getDeltaR(photon, lepton) )

    minDeltaR = min(deltaRList)
    #print(minDeltaR)

    if minDeltaR <= 0.1:  return deltaRList.index(minDeltaR)
    else:                 return False


def decorateLeptons( photonList, leptonList):

    photonLeptonPairList = []

    for photon in photonList:         
        leptonIndex = findLeptonToDecorateWithPhoton( photon, leptonList)

        if leptonIndex : photonLeptonPairList.append( (leptonIndex , photon ))

    for leptonIndex , photon in photonLeptonPairList:
        leptonList[leptonIndex] = leptonList[leptonIndex] + photon

    return None

def selectBaselineLeptons(leptonList):

    baselineLeptons = []

    for lepton in leptonList:
        if abs(lepton.pdgId()) == 11 : # electron
            if lepton.pt() >= 7000 and abs(lepton.eta()) < 2.5: baselineLeptons.append(lepton)
        elif abs(lepton.pdgId()) == 13 :# muon
            if lepton.pt() >= 5000 and abs(lepton.eta()) < 2.7: baselineLeptons.append(lepton)

    return baselineLeptons

def getAllPairs( aList ):

    nElements = len(aList)

    for item1Counter in xrange(0,nElements-1):

        item1 = aList[item1Counter]
        for item2Counter in xrange(item1Counter+1,nElements):
            item2 = aList[item2Counter]

            yield item1, item2


def makeLeptonPairs(leptonList):

    leptonPairList = []

    for lepton1, lepton2 in getAllPairs( leptonList ):
        if lepton1.pdgId() +  lepton2.pdgId() == 0:  
            if lepton1 is lepton2: import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            if lepton1.pdgId() > 0: leptonPairList.append( (lepton1,lepton2) )            
            else :                  leptonPairList.append( (lepton2,lepton1) )            

    return leptonPairList


def quadruplets( leptonPairs):

    ZBosonMass = 91187.6 # MeV
    quadrupletList = []

    for pair1, pair2 in getAllPairs( leptonPairs ):
        if (pair1[0] is pair2[0]) or (pair1[1] is pair2[1]): continue # can't reuse a lepton to make a quadruplet. Use 'is' to check against memory location


        massPair1 = (pair1[0] + pair1[1]).M()
        massPair2 = (pair2[0] + pair2[1]).M()

        # first two leptons should be the ones whoese invariant mass is closer to the Z-boson mass
        if abs(massPair1-ZBosonMass) <= abs(massPair2-ZBosonMass): quadrupletList.append( (pair1[0], pair1[1], pair2[0], pair2[1]) ) 
        else:                                                      quadrupletList.append( (pair2[0], pair2[1], pair1[0], pair1[1]) )


    # Sort the quadruplets
    # We put the most important sorting parameter last

    sortByM34Lambda = lambda x,refMass = ZBosonMass:abs((x[2]+x[3]).M()-refMass)
    quadrupletList.sort( key = sortByM34Lambda , reverse=False) # 

    sortByM12Lambda = lambda x,refMass = ZBosonMass:abs((x[0]+x[1]).M()-refMass)
    quadrupletList.sort( key = sortByM12Lambda , reverse=False) # 


    quadrupletList.sort( key = lambda x:x[0].pdgId() , reverse=True) # i.e. we
    quadrupletList.sort( key = lambda x:x[2].pdgId() , reverse=True) # i.e. we


    ## lines for inspecting the sorted quadruplets
    #if len(quadrupletList) > 3 : import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    #for quadruplet in quadrupletList: print( quadruplet[0].pdgId(), quadruplet[1].pdgId(), quadruplet[2].pdgId(), quadruplet[3].pdgId() )
    #for quadruplet in quadrupletList: print( abs((quadruplet[0]+quadruplet[1]).M()-ZBosonMass), abs((quadruplet[2]+quadruplet[3]).M()-ZBosonMass) )


    return quadrupletList




#def quadruplets( leptonPairs):
#
#    nPairs = len(leptonPairs)
#
#    for pair1Counter in xrange(0,nPairs-1):
#
#        lep1, lep2 = leptonPairs[pair1Counter]
#        for pair2Counter in xrange(pair1Counter+1,nPairs):
#            lep3, lep4 = leptonPairs[pair2Counter]
#
#            yield lep1, lep2, lep3, lep4

def quadrupletSelection( leptonPairList):

    for lep1, lep2, lep3, lep4 in quadruplets( leptonPairList):

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        transverseMomenta = sorted([lep1.pt(), lep2.pt(), lep3.pt(), lep4.pt()], reverse = True)

        leptonPTOk = transverseMomenta[0] > 20000 and transverseMomenta[1] > 15000 and transverseMomenta[2] > 10000

        if not leptonPTOk: continue

        diLeptonMassesOK = checkDileptonMasses(lep1, lep2, lep3, lep4)
        if not diLeptonMassesOK: continue

        pairwiseDeltaROK = [ getDeltaR(lepA, lepB) > 0.1  for lepA, lepB in  getAllPairs( [lep1, lep2, lep3, lep4] )]

        if not all(pairwiseDeltaROK): continue

        if abs(lep1.pdgId()) == abs(lep3.pdgId()): altPairingOK = (lep1+lep4).M() > 5000 and (lep2+lep3).M() > 5000
        else: altPairingOK = True

        if not altPairingOK: continue

        m4l = (lep1+lep2+lep3+lep4).M()
        withinHiggsMassWindow = m4l > 115000 and m4l < 130000

        if not withinHiggsMassWindow: continue


        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        # all cuts passed, return quadruplet
        return lep1, lep2, lep3, lep4
    
    return False # did not find a good quadruplet

def checkDileptonMasses(lep1, lep2, lep3, lep4):

    def leadingPairCheck( mZ1 ):    return mZ1 > 50000 and mZ1 < 106000 # MeV
    def subLeadingPairCheck( mZ2 ): return mZ2 > 12000 and mZ2 < 115000 # MeV

    m12 = (lep1 + lep2).M()
    m34 = (lep3 + lep4).M()

    ZBosonMass = 91187.6 # MeV

    if abs(m12-ZBosonMass) <= abs(m34-ZBosonMass): diLeptonMassesOK = leadingPairCheck( m12 ) and subLeadingPairCheck(m34)
    else:                                          diLeptonMassesOK = leadingPairCheck( m34 ) and subLeadingPairCheck(m12)

    return diLeptonMassesOK


def makeOutputHistogram( nEventsInFiducialRegionDict, histName = "outputHist"):

    nOutPuts = len( nEventsInFiducialRegionDict) 

    outputHist = ROOT.TH1I(histName,histName, nOutPuts, 0 , nOutPuts)

    binCounter = 0
    for eventType in sorted(nEventsInFiducialRegionDict.keys()) :         
        binCounter +=1  ;         
        outputHist.GetXaxis().SetBinLabel(binCounter, eventType) ;        
        outputHist.SetBinContent(binCounter,nEventsInFiducialRegionDict[eventType])

    return outputHist


def getDecayFlavorOfZd(truthParticles):

    #                                                                               Zd            pseudoscalar a 
    ZdCandicates = [ particle for particle in truthParticles if particle.pdgId() == 32 or particle.pdgId() == 36 ] 
    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    if len(ZdCandicates) > 0 : return( abs(ZdCandicates[0].child(0).pdgId()) )
    #else:  import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument( "--outputName", type=str, default="tree.root" , help = "Pick the name of the output TFile." )
    parser.add_argument( "--outputHistName", type=str, default=None , help = "Pick the name of the TTree" )
    parser.add_argument( "--nEventsToProcess", type=int, default=-1 , help = "Pick the name of the TTree" )

    args = parser.parse_args()

    print( args.input ) # print the event for debug purposes when running on condor
    print( args.outputName )
    print( args.outputHistName)

    #AAA  = lorentzVectorWithPDGId(0,0,0,1)
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    if args.outputHistName is None : 
        reMatchObject = re.search( "mZd\d\d", args.input)
        if reMatchObject: outputHistName = reMatchObject.group()
        else: outputHistName = "fiducialEventNumbers"
    else: outputHistName = args.outputHistName

    evt = ROOT.POOL.TEvent(ROOT.POOL.TEvent.kClassAccess) #argument is optional, but ClassAccess is faster than the default POOLAccess

    evt.readFrom(args.input)



    # PdgIds: http://pdg.lbl.gov/2010/download/rpp-2010-JPhys-G-37-075021.pdf
    #   25 = Higgs (For Za samples it is 35)
    #   23 = Z-boson
    #   32 = Zd boson
    #   36 = pseudosclar a
    #   11 = electron
    #   13 = muon

    if args.nEventsToProcess < 0 : nEvents = evt.getEntries()
    else:                          nEvents = args.nEventsToProcess

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    leptonParents = set()

    nEventsInFiducialRegionDict = {"all" : 0, "4e" : 0 , "2e2mu" : 0, "2mu2e" : 0, "4mu" : 0 , # split by signal region flavor
                                   "ZdTruthFlavor_2l2mu" : 0 , "ZdTruthFlavor_2l2e" : 0} 

    for eventCounter in range(0, nEvents): 

        evt.getEntry(eventCounter) #would call this method inside a loop if you want to loop over events .. argument is the entry number

        truthParticles = evt.retrieve("xAOD::TruthParticleContainer","TruthParticles")  


        ZdDecayFalvor = getDecayFlavorOfZd(truthParticles)

        if   ZdDecayFalvor == 11: nEventsInFiducialRegionDict["ZdTruthFlavor_2l2e"]  += 1
        elif ZdDecayFalvor == 13: nEventsInFiducialRegionDict["ZdTruthFlavor_2l2mu"] += 1

        leptons = [ particle for particle in truthParticles if (abs(particle.pdgId()) == 11 or abs(particle.pdgId()) == 13) and not particle.child(0)] # look for not particle.child(0) to find final state leptons


        photons = [ particle for particle in truthParticles if (abs(particle.pdgId()) == 22 and not particle.child(0)) ]


        leptons4Vec = [ particleToLorenzVector(lep) for lep in leptons ] # we now have a list of ROOT.Math.PxPyPzEVector
        photons4Vec = [ particleToLorenzVector(photon) for photon in photons ] # we now have a list of ROOT.Math.PxPyPzEVector

        #leptonParents.update(set(leptonsPDGIDs))

        decorateLeptons( photons4Vec, leptons4Vec)

        baselineLeptons = selectBaselineLeptons(leptons4Vec)

        if len(baselineLeptons) < 4: continue # need at least 4 leptons to from a quadruplet

        leptonPairs = makeLeptonPairs(baselineLeptons)

        fiducialRegionQuadruplet = quadrupletSelection( leptonPairs)

        if fiducialRegionQuadruplet:

            lep1PDGId = fiducialRegionQuadruplet[0].pdgId()
            lep2PDGId = fiducialRegionQuadruplet[1].pdgId()
            lep3PDGId = fiducialRegionQuadruplet[2].pdgId()
            lep4PDGId = fiducialRegionQuadruplet[3].pdgId()

            nEventsInFiducialRegionDict["all"] += 1

            if   abs(lep1PDGId) == 11 and abs(lep3PDGId) == 11 : nEventsInFiducialRegionDict["4e"]    +=1
            elif abs(lep1PDGId) == 13 and abs(lep3PDGId) == 11 : nEventsInFiducialRegionDict["2mu2e"] +=1
            elif abs(lep1PDGId) == 11 and abs(lep3PDGId) == 13 : nEventsInFiducialRegionDict["2e2mu"] +=1
            elif abs(lep1PDGId) == 13 and abs(lep3PDGId) == 13 : nEventsInFiducialRegionDict["4mu"]   +=1


    
    tFile = ROOT.TFile(args.outputName, 'recreate')   # https://wiki.physik.uzh.ch/cms/root:pyroot_ttree

    nEventsInFiducialRegionDict["eventsProcessed"] = eventCounter

        

    makeOutputHistogram = makeOutputHistogram( nEventsInFiducialRegionDict, outputHistName)

    #makeOutputHistogram.Write()


    tFile.Write()
    tFile.Close()


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here