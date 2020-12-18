#   do the following first:
#   asetup AthAnalysis,21.2.94,here
#
#   https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/AthAnalysis#How_to_inspect_files_in_pyROOT
#   https://twiki.cern.ch/twiki/bin/viewauth/AtlasComputing/SoftwareTutorialxAODAnalysisInCMake#Using_PyROOT
#
#   python truthPlots_pyROOT.py /direct/usatlas+u/chweber/usatlasdata/signalDAODs/mc16_13TeV.343234.MadGraphPythia8EvtGen_A14NNPDF23LO_HAHMggfZZd4l_mZd15.deriv.DAOD_HIGG2D1.e4551_e5984_a875_r9364_r9315_p3654/DAOD_HIGG2D1.16330910._000004.pool.root.1 --nEventsToProcess 100

import ROOT
from array import array # to fill the TTree eventally
import argparse # to parse command line options
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import math


#def particleToLorenzVector(particle): return ROOT.Math.PxPyPzEVector(particle.px(), particle.py(), particle.pz() , particle.e())
def particleToLorenzVector(particle): return lorentzVectorWithPDGId(particle.px(), particle.py(), particle.pz() , particle.e(), particle.pdgId())


class lorentzVectorWithPDGId(ROOT.Math.PxPyPzEVector):

    m_pdgId = None

    def __init__(self,px,py,pz,E, pdgId=None):
        super(lorentzVectorWithPDGId,self).__init__(px,py,pz,E)
        self.m_pdgId = pdgId

    def setPdgId(self,pdgId): self.m_pdgId = pdgId
    #def getPdgId(self,pdgId): return self.m_pdgId
    def pdgId(self): return self.m_pdgId


    #def add(self, otherLorentzVector):
    #    tempLorentzVector = self+otherLorentzVector
    #    return tempLorentzVector

    def __add__(self, other):

        outputLorentzVec = lorentzVectorWithPDGId( self.px()+other.px(), self.py()+other.py(), self.pz()+other.pz(), self.e()+other.e())

        if self.m_pdgId == other.pdgId(): outputLorentzVec.setPdgId(self.m_pdgId)
        elif self.m_pdgId == 22 : outputLorentzVec.setPdgId(other.pdgId())
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
            if lepton1.pdgId() > 0: leptonPairList.append( (lepton1,lepton2) )            
            else :                  leptonPairList.append( (lepton2,lepton1) )            

    return leptonPairList


def quadruplets( leptonPairs):

    for pair1, pair2 in getAllPairs( leptonPairs ):
        yield pair1[0], pair1[1], pair2[0], pair2[1]           

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

        transverseMomenta = sorted([lep1.pt(), lep2.pt(), lep3.pt(), lep4.pt()], reverse = True)

        leptonPTOk = transverseMomenta[0] > 20000 and transverseMomenta[1] > 15000 and transverseMomenta[2] > 10000

        if not leptonPTOk: continue

        diLeptonMassesOK = checkDileptonMasses
        if not diLeptonMassesOK: continue

        pairwiseDeltaROK = [ getDeltaR(lepA, lepB) > 0.1  for lepA, lepB in  getAllPairs( [lep1, lep2, lep3, lep4] )]

        if not pairwiseDeltaROK: continue

        if abs(lep1.pdgId()) == abs(lep3.pdgId()): altPairingOK = (lep1+lep4).M() > 5000 and (lep2+lep3).M() > 5000
        else: altPairingOK = True

        if not altPairingOK: continue

        m4l = (lep1+lep2+lep3+lep4).M()
        withinHiggsMassWindow = m4l > 150000 and m4l < 130000

        if not withinHiggsMassWindow: continue

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





def calculateInvariantMass(lep1, lep2):

    E  = lep1.e()  + lep2.e()
    px = lep1.px() + lep2.px()
    py = lep1.py() + lep2.py()
    pz = lep1.pz() + lep2.pz()

    invariantMassSq = (E**2 - px**2 - py**2 - pz**2)
    invariantMass =  math.copysign( abs(invariantMassSq)**0.5, invariantMassSq)

    return invariantMass

def getEtaPtPdgId(truthParticle): return { "pT" : truthParticle.pt() / 1000 , "eta" : truthParticle.eta(), "pdgId" : truthParticle.pdgId()} 
# divide by 1000 to convert MeV to GeV


def propertiesOfVectorBosonAndDoughterLeptons( vectorBoson):

    outputDict = collections.defaultdict(dict)

    lepton1 = vectorBoson.child(0)
    lepton2 = vectorBoson.child(1)

    if lepton1 == None or lepton2 == None: return None

    outputDict["vBoson"]  = getEtaPtPdgId(vectorBoson) 
    outputDict["vBoson"]["m"] = vectorBoson.m() / 1000  # convert to GeV
    outputDict["vBoson"]["mInv"] = calculateInvariantMass(lepton1, lepton2) / 1000 # convert to GeV

    outputDict["lepton1"] = getEtaPtPdgId( lepton1 )
    outputDict["lepton2"] = getEtaPtPdgId( lepton2 )

    return outputDict


def getOrderedZAndZdFromHiggs(higgsBoson):
    # first output is regular Z-boson, second output is Zd - dark Z boson

    # pdgId 23 = Z-boson
    # pdgId 32 = Zd boson

    vectorBoson1 = higgsBoson.child(0)
    vectorBoson2 = higgsBoson.child(1)

    if vectorBoson1.pdgId() == 23:  
        ZBoson  = vectorBoson1 ;  ZdBoson = vectorBoson2
    else: 
        ZBoson  = vectorBoson2 ;  ZdBoson = vectorBoson1

    return ZBoson , ZdBoson


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument( "--outputName", type=str, default="tree.root" , help = "Pick the name of the output TFile." )
    parser.add_argument( "--tTreeName", type=str, default="Zd_TruthTree" , help = "Pick the name of the TTree" )
    parser.add_argument( "--nEventsToProcess", type=int, default=-1 , help = "Pick the name of the TTree" )

    args = parser.parse_args()

    print( args.input ) # print the event for debug purposes when running on condor
    print( args.outputName )
    print( args.tTreeName)

    #AAA  = lorentzVectorWithPDGId(0,0,0,1)
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    evt = ROOT.POOL.TEvent(ROOT.POOL.TEvent.kClassAccess) #argument is optional, but ClassAccess is faster than the default POOLAccess

    evt.readFrom(args.input)

    tFile = ROOT.TFile(args.outputName, 'recreate')   # https://wiki.physik.uzh.ch/cms/root:pyroot_ttree
    TTree = ROOT.TTree(args.tTreeName, args.outputName)

    # create 1 dimensional float arrays as fill variables, in this way the float
    # array serves as a pointer which can be passed to the branch
    #px  = array('f',[0])
    #phi = array('f',[0])

    # create the branches and assign the fill-variables to them as doubles (D)
    #tree.Branch("px",  px , 'normal/f')
    #tree.Branch("phi", phi, 'uniform/f')

    Z_pT      = array('f',[0]) ; TTree.Branch("Z_pT"  ,    Z_pT   , 'Z_pT/F')
    Z_eta     = array('f',[0]) ; TTree.Branch("Z_eta" ,    Z_eta  , 'Z_eta/F')
    Z_pdgId   = array('i',[0]) ; TTree.Branch("Z_pdgId",   Z_pdgId  , 'Z_pdgId/I')
    Z_m       = array('f',[0]) ; TTree.Branch("Z_m"   ,    Z_m    , 'Z_m/F')
    ll12_mInv = array('f',[0]) ; TTree.Branch("ll12_mInv", ll12_mInv , 'll12_mInv/F')
    l1_pT     = array('f',[0]) ; TTree.Branch("l1_pT"  ,   l1_pT   , 'l1_pT/F')
    l1_eta    = array('f',[0]) ; TTree.Branch("l1_eta" ,   l1_eta  , 'l1_eta/F')
    l1_pdgId  = array('i',[0]) ; TTree.Branch("l1_pdgId",  l1_pdgId, 'l1_pdgId/I')
    l2_pT     = array('f',[0]) ; TTree.Branch("l2_pT"  ,   l2_pT   , 'l2_pT/F')
    l2_eta    = array('f',[0]) ; TTree.Branch("l2_eta" ,   l2_eta  , 'l2_eta/F')
    l2_pdgId  = array('i',[0]) ; TTree.Branch("l2_pdgId",  l2_pdgId, 'l2_pdgId/I')

    Zd_pT     = array('f',[0]) ; TTree.Branch("Zd_pT"   ,  Zd_pT    , 'Zd_pT/F')
    Zd_eta    = array('f',[0]) ; TTree.Branch("Zd_eta"  ,  Zd_eta   , 'Zd_eta/F')
    Zd_pdgId  = array('i',[0]) ; TTree.Branch("Zd_pdgId",  Zd_pdgId , 'Zd_pdgId/I')
    Zd_m      = array('f',[0]) ; TTree.Branch("Zd_m"    ,  Zd_m     , 'Zd_m/F')
    ll34_mInv = array('f',[0]) ; TTree.Branch("ll34_mInv", ll34_mInv , 'll34_mInv/F')
    l3_pT     = array('f',[0]) ; TTree.Branch("l3_pT"  ,   l3_pT   , 'l3_pT/F')
    l3_eta    = array('f',[0]) ; TTree.Branch("l3_eta" ,   l3_eta  , 'l3_eta/F')
    l3_pdgId  = array('i',[0]) ; TTree.Branch("l3_pdgId",  l3_pdgId, 'l3_pdgId/I')
    l4_pT     = array('f',[0]) ; TTree.Branch("l4_pT"  ,   l4_pT   , 'l4_pT/F')
    l4_eta    = array('f',[0]) ; TTree.Branch("l4_eta" ,   l4_eta  , 'l4_eta/F')
    l4_pdgId  = array('i',[0]) ; TTree.Branch("l4_pdgId",  l4_pdgId, 'l4_pdgId/I')
    


    # PdgIds: http://pdg.lbl.gov/2010/download/rpp-2010-JPhys-G-37-075021.pdf
    #   25 = Higgs
    #   23 = Z-boson
    #   32 = Zd boson
    #   11 = electron
    #   13 = muon

    if args.nEventsToProcess < 0 : nEvents = evt.getEntries()
    else:                          nEvents = args.nEventsToProcess

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    leptonParents = set()

    for n in range(0, nEvents): 

        evt.getEntry(n) #would call this method inside a loop if you want to loop over events .. argument is the entry number

        truthParticles = evt.retrieve("xAOD::TruthParticleContainer","TruthParticles")  

        # print out all (?) the information of the truth particles in the given event
        #for p in truthParticles: ROOT.AAH.printAuxElement(p)

        #leptonsPDGIDs = [ particle.pdgId() for particle in truthParticles if (abs(particle.pdgId()) == 11 or abs(particle.pdgId()) == 13) and not particle.child(0)]

        leptons = [ particle for particle in truthParticles if (abs(particle.pdgId()) == 11 or abs(particle.pdgId()) == 13) and not particle.child(0)] # look for not particle.child(0) to find final state leptons

        photons = [ particle for particle in truthParticles if (abs(particle.pdgId()) == 22 and not particle.child(0)) ]


        leptons4Vec = [ particleToLorenzVector(lep) for lep in leptons ] # we now have a list of ROOT.Math.PxPyPzEVector
        photons4Vec = [ particleToLorenzVector(photon) for photon in photons ] # we now have a list of ROOT.Math.PxPyPzEVector

        #leptonParents.update(set(leptonsPDGIDs))

        decorateLeptons( photons4Vec, leptons4Vec)

        baselineLeptons = selectBaselineLeptons(leptons4Vec)

        if len(baselineLeptons) < 4: continue # need at least 4 leptons to from a quadruplet

        leptonPairs = makeLeptonPairs(baselineLeptons)

        quadruplet = quadrupletSelection( leptonPairs)

        if not quadruplet: continue


        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        # print out pdgid of the truthParticles in the event
        for particle in truthParticles: 

            if particle.pdgId() != 32: continue
            # we found the Zd if particle.pdgId() == 32

            higgs = particle.parent()

            if higgs == None: break # sometimes the truth associations between the truthHiggs and its vector children seem to be broken. Just skip the event in this case.

            ZBoson, darkZBoson = getOrderedZAndZdFromHiggs(higgs)

            ZProperties = propertiesOfVectorBosonAndDoughterLeptons( ZBoson)
            darkZProperties = propertiesOfVectorBosonAndDoughterLeptons( darkZBoson)

            if ZProperties == None or darkZProperties == None: break # sometimes the truth associations break, then we discard the event


            Z_pT[0]       = ZProperties["vBoson"]["pT"]
            Z_eta[0]      = ZProperties["vBoson"]["eta"]
            Z_pdgId[0]    = ZProperties["vBoson"]["pdgId"]
            Z_m[0]        = ZProperties["vBoson"]["m"]
            ll12_mInv[0]  = ZProperties["vBoson"]["mInv"]
            l1_pT[0]      = ZProperties["lepton1"]["pT"]
            l1_eta[0]     = ZProperties["lepton1"]["eta"]
            l1_pdgId[0]   = ZProperties["lepton1"]["pdgId"]
            l2_pT[0]      = ZProperties["lepton2"]["pT"]
            l2_eta[0]     = ZProperties["lepton2"]["eta"]
            l2_pdgId[0]   = ZProperties["lepton2"]["pdgId"]
            
            Zd_pT[0]      = darkZProperties["vBoson"]["pT"]
            Zd_eta[0]     = darkZProperties["vBoson"]["eta"]
            Zd_pdgId[0]   = darkZProperties["vBoson"]["pdgId"]
            Zd_m[0]       = darkZProperties["vBoson"]["m"]
            ll34_mInv[0]  = darkZProperties["vBoson"]["mInv"]
            l3_pT[0]      = darkZProperties["lepton1"]["pT"]
            l3_eta[0]     = darkZProperties["lepton1"]["eta"]
            l3_pdgId[0]   = darkZProperties["lepton1"]["pdgId"]
            l4_pT[0]      = darkZProperties["lepton2"]["pT"]
            l4_eta[0]     = darkZProperties["lepton2"]["eta"]
            l4_pdgId[0]   = darkZProperties["lepton2"]["pdgId"]

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


            TTree.Fill()

            break # once we found the Z and Zd no need to go over the other truthParticles, better go on with the next event

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    tFile.Write()
    tFile.Close()


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here