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

    for n in range(0, nEvents): 

        evt.getEntry(n) #would call this method inside a loop if you want to loop over events .. argument is the entry number

        truthParticles = evt.retrieve("xAOD::TruthParticleContainer","TruthParticles")  

        # print out all (?) the information of the truth particles in the given event
        #for p in truthParticles: ROOT.AAH.printAuxElement(p)

        for particle in truthParticles: particle.pdgId()

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


    tFile.Write()
    tFile.Close()


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here