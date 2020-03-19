import ROOT

import math

import copy


def getRooRealVarFromTree( branchName, relevantTTree ):
    return ROOT.RooRealVar(branchName,branchName, math.floor(relevantTTree.GetMinimum(branchName)), math.ceil(relevantTTree.GetMaximum(branchName)))


def getZXTTree( fileName, treeName = "t_ZXTree"):
    aTFile = ROOT.TFile(fileName, "OPEN")
    aTTree = aTFile.Get(treeName)

    ROOT.SetOwnership(aTFile, False)  # we change the ownership here to False in the attempt to prevent deletion
    ROOT.SetOwnership(aTTree, False)  # we change the ownership here to False in the attempt to prevent deletion

    return aTTree



def getShapeRooDataSetAndIndepVar(ZXTTree):

    ### Setup variables for RooDataSet etc.

    m34 = getRooRealVarFromTree( "llll_m34", aTTree )
    #m34.setMax(45000)
    m4l = getRooRealVarFromTree( "llll_m4l", aTTree )

    weight = getRooRealVarFromTree( "weight", aTTree )
    weight.setMin(0)

    decayChannel = getRooRealVarFromTree( "decayChannel", aTTree )

    # and put the into sets and lists, as needed by the different Root Methods beliw
    anArgSet = ROOT.RooArgSet(m34, weight, m4l, decayChannel)
    anArgList = ROOT.RooArgList(anArgSet)

    # decay channel 1 <-> 4mu
    #               2 <-> 2e2mu
    #               3 <-> 2mu2e
    #               4 <-> 4e

    if   finalState == "llmumu": decaySetting = "decayChannel <= 2"
    elif finalState == "llee"  : decaySetting = "decayChannel >= 3"

    aFormula = ROOT.RooFormulaVar("cuts"," llll_m4l > 115000 && llll_m4l < 130000 &&  " + decaySetting, anArgList) #  &&       


        #aTTree.GetMinimum("mc_channel_number") aTTree.GetMaximum("mc_channel_number")

    if aTTree.GetMaximum("mc_channel_number") < 1.: 
        print("Data Sample detected, omitting weights")
        aDataSet   = ROOT.RooDataSet("h4lData", "h4lData", aTTree, anArgSet, aFormula)
    else: aDataSet = ROOT.RooDataSet("h4lData", "h4lData", aTTree, anArgSet, aFormula, "weight")


    # m34 is here the independent variable
    return aDataSet, m34



if __name__ == '__main__':

    ## llmumu shapes are from Z+HeavyFlavor and ttbar MC 
    ## llee   shapes are from Z+HeavyFlavor MC and 3l+X 

    #fileName = "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root"

    shapeSourceFiles = { "HeavyFlavor" : "post_20200228_203930__ZX_Run2_ZJetBFilter_May_Minitree.root", 
                         "ttBar"       : "post_20200228_152824__ZX_Run2_ttbar_May_Minitree.root",
                         "3l+X"        : "post_20200319_122149__ZX_Run2_Data_May_3lX_Minitree.root"      }
    

    canvasDict = {}

    for finalState in ["llmumu" , "llee"]:

        canvasCounter = 0
        canv = ROOT.TCanvas( finalState+"_canvas", finalState+"_canvas", 900, 900)
        canv.Divide(2,2)
        canvasDict[finalState] = canv

        for shapeType in shapeSourceFiles:

            fileName = shapeSourceFiles[shapeType]



            aTTree = getZXTTree( fileName )


            aDataSet, m34 = getShapeRooDataSetAndIndepVar(aTTree)

            kest1 = ROOT.RooKeysPdf("kest1", "kest1", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            kest2 = ROOT.RooKeysPdf("kest2", "kest2", m34, aDataSet)#                        ROOT.RooKeysPdf.MirrorBoth)
            kest3 = ROOT.RooKeysPdf("kest3", "kest3", m34, aDataSet, ROOT.RooKeysPdf.MirrorBoth)#                        ROOT.RooKeysPdf.MirrorBoth)

            plotName = shapeType + ": " + finalState

            canvasCounter += 1
            canv.cd(canvasCounter)

            xFrameHists = m34.frame() # frame to plot my PDFs on
            xFrameHists.SetTitle(plotName)
            aDataSet.plotOn(xFrameHists)
            #aDataSetWeighted.plotOn(xFrameHists, ROOT.RooFit.LineColor(ROOT.kGreen+1),ROOT.RooFit.MarkerColor(ROOT.kGreen+1) )#, ROOT.RooFit.MarkerColor(ROOT.kGreen+1))
            #
            #kest1.plotOn(xFrameHists)
            kest2.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kRed+1)) # , ROOT.RooFit.LineWidth(5) 
            kest3.plotOn(xFrameHists,ROOT.RooFit.LineColor(ROOT.kGreen+1),ROOT.RooFit.LineStyle(7))


            xFrameHists.Draw()
            canv.Update()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


    # aTFile.Get()

    # aDataSetWeighted.sumEntries()
    # aTFile.Get("410472").Get("Nominal").Get("h_ZXSR_All_HWindow_m34").Integral()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
