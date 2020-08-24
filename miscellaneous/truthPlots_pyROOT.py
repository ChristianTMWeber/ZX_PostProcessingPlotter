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


def calculateInvariantMass(lep1, lep2):

    E  = lep1.e()  + lep2.e()
    px = lep1.px() + lep2.px()
    py = lep1.py() + lep2.py()
    pz = lep1.pz() + lep2.pz()

    invariantMass = (E**2 - px**2 - py**2 - pz**2)**.5

    return invariantMass




if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=str, help="name or path to the input files")

    parser.add_argument( "--outputName", type=str, default="tree.root" , help = "Pick the name of the output TFile." )
    parser.add_argument( "--tTreeName", type=str, default="Zd_TruthTree" , help = "Pick the name of the TTree" )
    parser.add_argument( "--nEventsToProcess", type=int, default=-1 , help = "Pick the name of the TTree" )

    args = parser.parse_args()

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

    Zd_pT   = array('f',[0]) ; TTree.Branch("Zd_pT"  ,  Zd_pT   , 'Zd_pT/f')
    Zd_m    = array('f',[0]) ; TTree.Branch("Zd_m"   ,  Zd_m    , 'Zd_m/f')
    Zd_eta  = array('f',[0]) ; TTree.Branch("Zd_eta" ,  Zd_eta  , 'Zd_eta/f')
    l1_pT   = array('f',[0]) ; TTree.Branch("l1_pT"  ,  l1_pT   , 'l1_pT/f')
    l1_eta  = array('f',[0]) ; TTree.Branch("l1_eta" ,  l1_eta  , 'l1_eta/f')
    l2_pT   = array('f',[0]) ; TTree.Branch("l2_pT"  ,  l2_pT   , 'l2_pT/f')
    l2_eta  = array('f',[0]) ; TTree.Branch("l2_eta" ,  l2_eta  , 'l2_eta/f')
    ll_mInv = array('f',[0]) ; TTree.Branch("ll_mInv",  ll_mInv , 'll_mInv/f')

    # PdgIds: http://pdg.lbl.gov/2010/download/rpp-2010-JPhys-G-37-075021.pdf
    #   25 = Higgs
    #   23 = Z-boson
    #   32 = Zd boson
    #   11 = electron
    #   13 = muon

    if args.nEventsToProcess < 0 : nEvents = evt.getEntries()
    else:                          nEvents = args.nEventsToProcess

    for n in range(0, nEvents): 

        evt.getEntry(n) #would call this method inside a loop if you want to loop over events .. argument is the entry number

        truthParticles = evt.retrieve("xAOD::TruthParticleContainer","TruthParticles")  

        # print out all (?) the information of the truth particles in the given event
        #for p in truthParticles: ROOT.AAH.printAuxElement(p)

        # print out pdgid of the truthParticles in the event
        for particle in truthParticles: 

            if particle.pdgId() != 32: continue

            Zd = particle
            assert Zd.nChildren() == 2

            lepton1 = particle.child(0)
            lepton2 = particle.child(1)


            Zd_pT[0]   = Zd.pt() / 1000 # convert to GeV
            Zd_m[0]    = Zd.m()
            Zd_eta[0]  = Zd.eta()
            l1_pT[0]   = lepton1.pt() / 1000 # convert to GeV
            l1_eta[0]  = lepton1.eta()
            l2_pT[0]   = lepton2.pt() / 1000 # convert to GeV
            l2_eta[0]  = lepton2.eta()
            ll_mInv[0] = calculateInvariantMass(lepton1, lepton2) / 1000 # convert to GeV

            TTree.Fill()

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    tFile.Write()
    tFile.Close()


    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here