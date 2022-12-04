import ROOT

import os
import re
import csv
import collections

def gatherIntputROOTFiles(inputDir, relevantInputFileReTag = ".*\.flat\.TTree\.root\.1"):

    outputList = []

    inputDirAbs = os.path.abspath(inputDir)

    for (root,dirs,files) in os.walk(inputDirAbs): 
        for file in files:

            if not re.search(relevantInputFileReTag,file): continue

            outputList.append( os.path.join(root,file) )

    return outputList


def getPhysicsParameterMapping(inputFile):

    outputDict = collections.defaultdict(dict)


    with open(inputFile, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:

            # last set of digits in the spreadsheet are off by 4 w.r.t. to actual file names
            # let's correct that here

            job_split = row["job"].split("_")
            job_split[2] = "%03d" %(int(job_split[2])-4)
            job_corrected = "_".join(job_split)

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            outputDict[job_corrected]["ZdMassGeV"] = row["myparamMZD"]
            outputDict[job_corrected]["epsilon"]   = row["myparamEPSILON"]

    return outputDict


def matchFilesToPhysicsParameters(physicsDict,inputFileList):

    inputFileDict = collections.defaultdict(list)

    physicsKeySearchString = "(" + ")|(".join(physicsDict.keys()) + ")"

    for file in inputFileList:

        matchedPhysicsKey = re.search(physicsKeySearchString,file).group()

        mZd = physicsDict[matchedPhysicsKey]['ZdMassGeV']
        epsilon = physicsDict[matchedPhysicsKey]['epsilon']

        inputFileDict[ (mZd,epsilon)].append(file)

    return inputFileDict


def divide_chunks(l, n):
     
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def defineHistProperties():


    histPropertyDict = collections.defaultdict(dict)

    # histPropertyDict[kinematic][<properties>]
    histPropertyDict["pT"]["nBins"]   = 200
    histPropertyDict["pT"]["lowBin"]  = 0
    histPropertyDict["pT"]["highBin"] = 200
    histPropertyDict["pT"]["units"]   = "(GeV)"


    histPropertyDict["eta"]["nBins"]   = 81
    histPropertyDict["eta"]["lowBin"]  = -8
    histPropertyDict["eta"]["highBin"] = +8
    histPropertyDict["eta"]["units"]   = ""

    histPropertyDict["mInv"]["nBins"]   = 100
    histPropertyDict["mInv"]["lowBin"]  = 50
    histPropertyDict["mInv"]["highBin"] = 115
    histPropertyDict["mInv"]["units"]   = "(GeV)"


    physicsObjectDict = collections.defaultdict(list)

    physicsObjectDict["Zd"] = ["pT","eta"]
    physicsObjectDict["Z"] = ["pT","eta"]
    physicsObjectDict["l1"] = ["pT","eta"]
    physicsObjectDict["l2"] = ["pT","eta"]
    physicsObjectDict["l3"] = ["pT","eta"]
    physicsObjectDict["l4"] = ["pT","eta"]

    physicsObjectDict["ll12"] = ["mInv"]
    physicsObjectDict["ll34"] = ["mInv"]


    return histPropertyDict, physicsObjectDict



def defineHist(mZd,epsilon, histPropertyDict, physicsObjectDict ):

    mZdFixPrec     = "%2.2f"%float(mZd)
    epsilonSciNota = "%1.2e" %float(epsilon)


    histDict = collections.defaultdict(dict)


    for physicsObjs in physicsObjectDict:
        for kinematic in physicsObjectDict[physicsObjs]:

            histName = "%s_%s_test_mZd%s_epsilon%s" %(physicsObjs, kinematic,mZdFixPrec,epsilonSciNota)
            histTitle = "truth H #rightarrow ZZ_{d} #rightarrow 4l %s distribution" %(kinematic)

            histProperties = histPropertyDict[kinematic]

            hist = ROOT.TH1F(histName,histTitle,histProperties["nBins"], histProperties["lowBin"],  histProperties["highBin"])


            hist.AddDirectory(ROOT.kFALSE) # prevent histograms from being added to the current directory, see https://root.cern/manual/object_ownership/

            hist.GetXaxis().SetTitle("%s %s %s" %(physicsObjs,kinematic,histProperties["units"]) )
            

            #                % draw command
            histDict[histName]["hist"] = hist
            histDict[histName]["drawCommand"] = "%s_%s >> %s" % (physicsObjs,kinematic ,histName)
            histDict[histName]["legendStr"] = "m_{Z_{d}} = %s, #varepsilon = %s" %(mZdFixPrec, epsilonSciNota)

            #ROOT.SetOwnership(hist,True)

    #Zd_pT_Hist = ROOT.TH1D("Zd_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
    #Zd_pT_Hist.GetXaxis().SetTitle("Z_{d} pT (GeV)")

    return histDict


def getTChain( listOfFiles, TTreeName):

    myTChain = ROOT.TChain(TTreeName)

    for file in listOfFiles: myTChain.Add(file)




    hist = ROOT.TH1F("test","test",100, 1,-1)
    myTChain.Draw("l2_pT >> test")
    #hist.Print("Print.pdf")
    canv = ROOT.TCanvas()
    hist.Draw()
    canv.Update()
    canv.Print("Print.pdf")




    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    return None


if __name__ == '__main__':


    physicsDict = getPhysicsParameterMapping("allresults.csv")


    inputTTreeDir =  "/gpfs/mnt/atlasgpfs01/usatlas/data/chweber/ReanaActiveLearningProject/generatedZXSamples/evnt"

    inputFileList = gatherIntputROOTFiles(inputTTreeDir, relevantInputFileReTag = ".*\.flat\.TTree\.root\.1")


    physicsAndIntputFileDict = matchFilesToPhysicsParameters(physicsDict,inputFileList)

    massAndEpsilonList = list(physicsAndIntputFileDict.keys())

    massAndEpsilonList.sort( key = lambda x: x[1] , reverse = False)

    massAndEpsilonList.sort( key = lambda x: x[0] , reverse = False)




    massAndEpsilonListBatches = [chunk for chunk in divide_chunks(massAndEpsilonList, 3)]




    TFile = ROOT.TFile("ZX_CombinedTruthTTree4.root", "OPEN")


    ROOT.gROOT.SetBatch(True)



    histPropertyDict, physicsObjectDict = defineHistProperties()


    for Zd_epsilon_batch in massAndEpsilonListBatches:

        histDict = {}

        for Zd, epsilon in Zd_epsilon_batch:


            # define hists

            histDict[ (Zd,epsilon)] = defineHist(Zd,epsilon, histPropertyDict, physicsObjectDict )

            currentHistSet = histDict[ (Zd,epsilon)]



            setOfFiles = physicsAndIntputFileDict[ (Zd,epsilon)]


            getTChain( setOfFiles, "truthTree_Zd")

            for file in physicsAndIntputFileDict[ (Zd,epsilon)]: 


                TFile = ROOT.TFile(file,"OPEN")
                TTree = TFile.Get("truthTree_Zd")

                for histName in currentHistSet:

                    hist = currentHistSet[histName]["hist"]

                    drawCommand = currentHistSet[histName]["drawCommand"]

                    TTree.Draw(drawCommand)

                    #ROOT.gROOT.SetBatch(False)

                    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

                    hist = ROOT.TH1F("test","test",100, 1,-1)
                    TTree.Draw("l2_pT >> test")



                    #hist.Print("Print.pdf")
                    canv = ROOT.TCanvas()
                    hist.Draw()
                    canv.Update()
                    canv.Print("Print.pdf")


                    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


                TFile.Close() 




                pass
                # draw in hists


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    for mass in [15, 35, 55]:

        TTree = TFile.Get("truthTree_Zd_%i_GeV"%mass)


        Zd_pT_Hist = ROOT.TH1D("Zd_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
        Zd_pT_Hist.GetXaxis().SetTitle("Z_{d} pT (GeV)")
        TTree.Draw(" Zd_pT >> Zd_pT_Hist%i" %mass)


        Zd_eta_Hist = ROOT.TH1D("Zd_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
        Zd_eta_Hist.GetXaxis().SetTitle("Z_{d} #eta")
        TTree.Draw(" Zd_eta >> Zd_eta_Hist%i" %mass)


        Z_pT_Hist = ROOT.TH1D("Z_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l pT distribution, m_{Zd} = %i GeV"%mass, 200,0,200)
        Z_pT_Hist.GetXaxis().SetTitle("Z pT (GeV)")
        TTree.Draw(" Z_pT >> Z_pT_Hist%i" %mass)


        Z_eta_Hist = ROOT.TH1D("Z_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
        Z_eta_Hist.GetXaxis().SetTitle("Z #eta")
        TTree.Draw(" Z_eta >> Z_eta_Hist%i" %mass)




        ll12_eta_Hist = ROOT.TH1D("ll12_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
        ll12_eta_Hist.GetXaxis().SetTitle("l_{1}, l_{2}lepton #eta")
        TTree.Draw(" l1_eta >> ll12_eta_Hist%i" %mass)
        TTree.Draw(" l2_eta >> ll12_eta_Hist%i" %mass)


        ll12_pT_Hist = ROOT.TH1D("ll12_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll  pT distribution, m_{Zd} = %i GeV"%mass, 100,0,100)
        ll12_pT_Hist.GetXaxis().SetTitle("l_{1}, l_{2} lepton pT (GeV)")
        TTree.Draw(" l1_pT >> ll12_pT_Hist%i" %mass)
        TTree.Draw(" l2_pT >> ll12_pT_Hist%i" %mass)



        ll34_eta_Hist = ROOT.TH1D("ll34_eta_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll #eta distribution, m_{Zd} = %i GeV"%mass, 81, -8,8)
        ll34_eta_Hist.GetXaxis().SetTitle("l_{3}, l_{4} lepton #eta")
        TTree.Draw(" l3_eta >> ll34_eta_Hist%i" %mass)
        TTree.Draw(" l4_eta >> ll34_eta_Hist%i" %mass)


        ll34_pT_Hist = ROOT.TH1D("ll34_pT_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll  pT distribution, m_{Zd} = %i GeV"%mass, 100,0,100)
        ll34_pT_Hist.GetXaxis().SetTitle("l_{3}, l_{4} lepton pT (GeV)")
        TTree.Draw(" l3_pT >> ll34_pT_Hist%i" %mass)
        TTree.Draw(" l4_pT >> ll34_pT_Hist%i" %mass)





        ll12_invMass_Hist = ROOT.TH1D("ll12_invMass_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll , ll invariant mass distribution, m_{Zd} = %i GeV"%mass, 100, 50, 115)
        ll12_invMass_Hist.GetXaxis().SetTitle("m_{12} (GeV)")
        TTree.Draw(" ll12_mInv >> ll12_invMass_Hist%i" %mass)


        ll34_invMass_Hist = ROOT.TH1D("ll34_invMass_Hist%i" %mass, "truth H #rightarrow ZZ_{d} #rightarrow 4l, Z_{d} #rightarrow ll , ll invariant mass distribution, m_{Zd} = %i GeV"%mass, 100, mass-.5,mass+0.5)
        ll34_invMass_Hist.GetXaxis().SetTitle("m_{34} (GeV)")
        TTree.Draw(" ll34_mInv >> ll34_invMass_Hist%i" %mass)


        for hist in [ Zd_pT_Hist, Zd_eta_Hist, Z_pT_Hist, Z_eta_Hist, ll12_eta_Hist, ll12_pT_Hist, ll34_eta_Hist, ll34_pT_Hist, ll12_invMass_Hist, ll34_invMass_Hist]:

            canvasName = hist.GetName() + "_%GeV" %mass
            canvas = ROOT.TCanvas(canvasName,canvasName, 1920/2, 1090 )
            hist.Draw()
            canvas.Update()

            canvas.Print(canvasName +".png")
            canvas.Print(canvasName +".pdf")


    #fillHist = ROOT.TH1D(weightVariation,weightVariation,200,0,100)








    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here