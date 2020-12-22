import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import difflib # to help me match strings via 'difflib.get_close_matches'
import numpy as np

import math

# import sys and os.path to be able to import things from the parent directory
import sys 
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) ) # need to append the parent directory here explicitly to be able to import plotPostProcess
import functions.rootDictAndTDirTools as TDirTools
import functions.RootTools as RootTools


def getPullAndImpactTTreeDicts(inputTFile):

    pullParamDict = {}
    impactParamDict = {}

    for rootObj in TDirTools.generateTDirContents(inputTFile):
        rootObjName = rootObj.GetName()

        pullOrImpactMatch = re.search("(pullParameters|prePostFitImpact)", rootObjName)

        if pullOrImpactMatch:

            mass = re.search("\d\d",rootObjName).group()
            if pullOrImpactMatch.group() == "pullParameters": 
                pullParamDict[int(mass)] = rootObj
            else:  # impactParameter
                impactParamDict[int(mass)] = rootObj


    return pullParamDict, impactParamDict


def calculatePulls(pullTTree):

    pullVarNames = [branch.GetName()  for branch in pullTTree.GetListOfBranches()]

    prefitErrors  = {}
    prefitMeans   = {}
    postfitValues = {}
    postfitErrors = {}

    pullMeanDict = {}
    pullErrorDict = {}

    for varName in sorted(pullVarNames): 

        if varName.startswith("nom"):
            if varName.endswith("upperLimit") : prefitErrors[varName] = RootTools.GetValuesFromTree(pullTTree, varName)[0]
            else:                               prefitMeans[varName] = RootTools.GetValuesFromTree(pullTTree, varName)[0]

        elif varName.endswith("_err"): postfitErrors[varName] = RootTools.GetValuesFromTree(pullTTree, varName)[0]
        else:                          postfitValues[varName] = RootTools.GetValuesFromTree(pullTTree, varName)[0]


    for postfitName in sorted(postfitValues): 

        matchDict = {}

        matchDict[ "postfitValue"] = [postfitName]
        matchDict[ "postfitError"] = difflib.get_close_matches( postfitName  , postfitErrors.keys(), n=1, cutoff =0.3 )
        matchDict[ "prefitValue" ] = difflib.get_close_matches( postfitName  , prefitMeans.keys(), n=1, cutoff =0.3 )
        matchDict[ "prefitError" ] = difflib.get_close_matches( postfitName  , prefitErrors.keys(), n=1, cutoff =0.3 )

        allVarsMatched = all( [len(value)>0 for value in matchDict.values()  ] )

        if allVarsMatched :
            varDict = {}
            for varType in matchDict: 
                varTTreeName = matchDict[varType][0]
                varDict[varType]  = RootTools.GetValuesFromTree(pullTTree, varTTreeName )[0]

            pullMeanDict[postfitName]  = (varDict["postfitValue"] - varDict["prefitValue"])/varDict["prefitError"]
            pullErrorDict[postfitName] = (varDict["postfitValue"] + varDict["postfitError"]- varDict["prefitValue"])/varDict["prefitError"]

    # for x in pullMeanDict: (x, pullMeanDict[x], pullErrorDict[x])
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    return pullMeanDict, pullErrorDict

def makeImpacts(impactTTree):

    impactVarNames = [branch.GetName()  for branch in impactTTree.GetListOfBranches()]

    varNames = []

    prefixes = ["mu_postFitUp_", "mu_postFitDown_", "mu_preFitUp_", "mu_preFitDown_"] 

    impactVarsDict = collections.defaultdict(dict)

    # make var names that are consistent with the pull ones

    for impactName in impactVarNames: 

        if impactName.startswith("mu_postFitUp_"):  varNames.append( re.sub('mu_postFitUp_', "", impactName) )
        elif "reference" in impactName: refMuValue = RootTools.GetValuesFromTree(impactTTree, impactName )[0]

        #prefixFound = re.search("mu_\w+?_", impactName)
        #if prefixFound: prefixes.add( prefixFound.group() )

    for varName in varNames: 
        for prefix in prefixes:
            if prefix+varName in impactVarNames:
                impactVarsDict[varName][prefix] = RootTools.GetValuesFromTree(impactTTree, prefix+varName )[0] - refMuValue
                #print varName + " " + prefix  + " " + str( impactVarsDict[varName][prefix])

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
    # rucio download  --ndownloader 1  `cat containers.txt`

    return impactVarsDict


def getLeftAndRightErrors( posOrNegError ):

    leftError = 0 ;  rightError = 0

    if posOrNegError > 0: rightError = posOrNegError
    else :                leftError  = abs(posOrNegError)

    return leftError, rightError


def setupTLegend():
    # set up a TLegend, still need to add the different entries
    xOffset = 0.02; yOffset = 0.85
    xWidth  = 0.2; ywidth = 0.15
    TLegend = ROOT.TLegend(xOffset, yOffset ,xOffset + xWidth, yOffset+ ywidth)
    TLegend.SetFillColor(ROOT.kWhite)
    TLegend.SetLineColor(ROOT.kWhite)
    TLegend.SetNColumns(1);
    TLegend.SetFillStyle(0);  # make legend background transparent
    TLegend.SetBorderSize(0); # and remove its border without a border
    return TLegend


def scalePrePostFit( mass ):

    if mass >= 50: scale = 150
    elif mass >= 35 : scale = 50
    else: scale = 60

    return scale


def floorToPowerOfTen(numberToFloor, powerOfTen ):

    scaleFactor = 10**powerOfTen

    return   math.floor(numberToFloor/scaleFactor)*scaleFactor

if __name__ == '__main__':

    inputFileName = "prePostFitImpact5_PGM_All_Combined.root"

    inputTFile = ROOT.TFile(inputFileName, "OPEN")

    pullParamDict, impactParamDict = getPullAndImpactTTreeDicts(inputTFile)

    H4lNormDict = {}


    ROOT.gROOT.SetBatch(True)
    

    #for x in sorted(pullParamDict.keys()) : pullParamDict[x]
    for mass in sorted(pullParamDict.keys()) :
        pullTTree = pullParamDict[mass]
        impactTTree = impactParamDict[mass]

        H4lNormDict[mass] = RootTools.GetValuesFromTree(pullTTree, "H4lNorm")[0]


        pullMeanDict, pullErrorDict = calculatePulls(pullTTree); 
        impactVarDict = makeImpacts(impactTTree)

        pullGraph = ROOT.TGraphAsymmErrors();                 pullGraph.SetName("pullGraph")
        backgroundGraph = ROOT.TGraphErrors();                backgroundGraph.SetName("backgroundTGraph")
        prefitImpactGraph = ROOT.TGraphAsymmErrors();         prefitImpactGraph.SetName("prefitImpactGraph")
        postfitImpactGraph = ROOT.TGraphAsymmErrors() ;       postfitImpactGraph.SetName("postfitImpactGraph")

        postfitImpactUPGraph = ROOT.TGraphAsymmErrors() ;       postfitImpactUPGraph.SetName("postfitImpactUPGraph")
        postfitImpactDOWNGraph = ROOT.TGraphAsymmErrors() ;     postfitImpactDOWNGraph.SetName("postfitImpactDOWNGraph")

        nLabels = len(impactVarDict)
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        offset = 0.5

        nuisanceParameterListSorted = impactVarDict.keys()

        #def getMuPostFitUpValue(prameterName): return impactVarDict[prameterName]['mu_postFitUp_']
        nuisanceParameterListSorted.sort( key =  lambda x: abs((impactVarDict[x]['mu_postFitUp_'])) + abs((impactVarDict[x]['mu_postFitDown_'])) ) # alternative use 'mu_postFitUp_'

        impactScale =  floorToPowerOfTen( 1/ max(abs(np.array( impactVarDict[ nuisanceParameterListSorted[-1] ].values() ))), 1)

        th2Name = "Pull and fit impact, m_{Z_{d}} = %i GeV" %mass
        # TH2F (                   *name,  *title, Int_t nbinsx, Double_t xlow, Double_t xup, Int_t nbinsy, Double_t ylow, Double_t yup)
        labelTH2 = ROOT.TH2F("labelHist", th2Name, 1, -1.2, +1.2,                         nLabels + 1, +offset, nLabels + 1 + offset);
        labelTH2.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0})/#Delta#theta , fit impact #times %i"%impactScale )


        impactTH2 = ROOT.TH2F("impactTH2", "impactTH2", 1, -0.2, +.2,                         nLabels + 1, +offset, nLabels + 1 + offset);


        # 

        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

        barYWidth = 0.5




        counter = 0 
        #for nuisanceParameter in sorted(pullMeanDict): 
        for nuisanceParameter in nuisanceParameterListSorted: 
            counter += 1

            print "%i %s" %(counter, nuisanceParameter)
            
            ############ make pull plots ############
            if nuisanceParameter in pullMeanDict:
                pullPointNr = pullGraph.GetN()
                pullGraph.SetPoint( pullPointNr, pullMeanDict[nuisanceParameter] , counter )
                # these are really erros here. I.e. how far the error bars extend in each direction from the center point
                pullGraph.SetPointError( pullPointNr, pullErrorDict[nuisanceParameter],pullErrorDict[nuisanceParameter], 0 , 0 )  

            #make impact plots

            impactVars = impactVarDict[nuisanceParameter]

            


            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            ############ make prefit impact plots ############
            if "mu_preFitUp_" in impactVars:
                prefitPointNr = prefitImpactGraph.GetN()

                prefitMean = impactVars["mu_preFitUp_"] - impactVars["mu_preFitDown_"]
                prefitImpactGraph.SetPoint( prefitPointNr, 0 , counter )
                # these are really erros here. I.e. how far the error bars extend in each direction from the center point

                upAndDownImpact = np.array( [impactVars["mu_preFitDown_"] , impactVars["mu_preFitUp_"] ])

                #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

                leftImpact  = abs(min(upAndDownImpact * (upAndDownImpact <0) ) )*impactScale 
                rightImpact =     max(upAndDownImpact* (upAndDownImpact >0) )*impactScale


                #prefitImpactGraph.SetPointError( prefitPointNr, abs(impactVars["mu_preFitDown_"])*impactScale, abs(impactVars["mu_preFitUp_"])*impactScale, barYWidth,barYWidth )  
                prefitImpactGraph.SetPointError( prefitPointNr, leftImpact, rightImpact, barYWidth,barYWidth )  

            postfitPointNr = postfitImpactGraph.GetN()

            

            ############ make prefit impact plots ############
            postfitMean = impactVars["mu_postFitUp_"] - impactVars["mu_postFitDown_"]
            postfitImpactGraph.SetPoint( postfitPointNr, 0 , counter )
            # these are really erros here. I.e. how far the error bars extend in each direction from the center point
            postfitImpactGraph.SetPointError( postfitPointNr, abs(impactVars["mu_postFitDown_"])*impactScale, abs(impactVars["mu_postFitUp_"])*impactScale, barYWidth,barYWidth )  


            postfitImpactUPGraph.SetPoint( postfitPointNr, 0 , counter )
            postfitImpactDOWNGraph.SetPoint( postfitPointNr, 0 , counter )


            leftError, rightError = getLeftAndRightErrors( impactVars["mu_postFitUp_"] )

            postfitImpactUPGraph.SetPointError( postfitPointNr, leftError*impactScale, rightError*impactScale, barYWidth,barYWidth )  


            leftError, rightError = getLeftAndRightErrors( impactVars["mu_postFitDown_"] )
            postfitImpactDOWNGraph.SetPointError( postfitPointNr, leftError*impactScale, rightError*impactScale , barYWidth,barYWidth )  

            # impactVars["mu_postFitDown_"]   ,   impactVars["mu_postFitUp_"]

            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            #if counter == 10 : import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

            nuisanceParameterYLabel = re.sub("alpha", "", nuisanceParameter) 
            nuisanceParameterYLabel = re.sub( "Uncert" , "_Norm",    nuisanceParameterYLabel)
            nuisanceParameterYLabel = re.sub( "(Scale)|(Variations)" , "_Shape",    nuisanceParameterYLabel)

            nuisanceParameterYLabel = nuisanceParameterYLabel.strip("_") # remove leading and trailing underscores

            labelTH2.GetYaxis().SetBinLabel(counter, nuisanceParameterYLabel) 

            #pullGraph.GetYaxis().SetBinLabel(counter, x)

            ############ add background ############

            if counter %2 == 0:

                backgroundPointNr = backgroundGraph.GetN()

                backgroundGraph.SetPoint( backgroundPointNr, 0 , counter )
                backgroundGraph.SetPointError(backgroundPointNr, 2.0 , barYWidth )




        canvasName = "PullPlot_%iGeV" %mass

        #labelTH2.GetYaxis().SetTitleOffset(2.)
        labelTH2.SetStats( False) # remove stats box
        canvas = ROOT.TCanvas(canvasName,canvasName,1920/2, 1080)
        canvas.SetLeftMargin(0.5)
        canvas.SetTopMargin(0.12)


        #pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.0, 1.0, 1.0, 0);
        #pad1.SetLeftMargin(0.35)
        #pad1.Draw();
        #pad1.cd();

        labelTH2.Draw()



        backgroundGraph.SetFillColor(ROOT.kGray )
        backgroundGraph.Draw("same 2 ")
        


        #impactTH2.Draw("same")


        prefitImpactGraph.SetFillColor( ROOT.kYellow-7);
        #prefitImpactGraph.SetFillStyle(3001);
        prefitImpactGraph.Draw("same 2 ")

        ROOT.gStyle.SetHatchesLineWidth(2) #define the hatches line width.
        ROOT.gStyle.SetHatchesSpacing(0.5) # to define the spacing between hatches.


        postfitImpactGraph.SetFillColor(ROOT.kBlue);
        postfitImpactGraph.SetLineColor(ROOT.kBlue);
        postfitImpactGraph.SetFillStyle(3354);
        #postfitImpactGraph.SetFillStyle(0);
        #postfitImpactGraph.SetFillColor(ROOT.kGray+3);
        postfitImpactGraph.SetLineWidth(1)
        #postfitImpactGraph.Draw("same 2 p ")

        postfitImpactGraph2 = postfitImpactGraph.Clone(postfitImpactGraph.GetName()+"2")

        postfitImpactGraph2.SetFillStyle(0);
        #postfitImpactGraph2.Draw("same 2 p ")


        postfitImpactUPGraph.SetFillColor(ROOT.kBlue);
        postfitImpactUPGraph.SetLineColor(ROOT.kBlue);
        postfitImpactUPGraph.SetFillStyle(3354);
        postfitImpactUPGraph.SetLineWidth(1)

        postfitImpactUPGraph.Draw("same 2 p ")


        postfitImpactDOWNGraph.SetFillColor(ROOT.kBlue);
        postfitImpactDOWNGraph.SetLineColor(ROOT.kBlue);
        postfitImpactDOWNGraph.SetFillStyle(0);
        postfitImpactDOWNGraph.SetLineWidth(1)

        postfitImpactDOWNGraph.Draw("same 2 p ")


        pullGraph.SetLineWidth(2)
        pullGraph.SetMarkerStyle(8)
        pullGraph.SetMarkerSize(1)

        pullGraph.Draw("same P")


        legend = setupTLegend()

        legend.AddEntry(pullGraph , "pull"  , "l");
        legend.AddEntry(prefitImpactGraph , "prefitImpact" , "f");
        legend.AddEntry(postfitImpactUPGraph , "postfitImpact +1#sigma" , "f");
        legend.AddEntry(postfitImpactDOWNGraph , "postfitImpact -1#sigma" , "f");
        legend.Draw()


        labelTH2.Draw("same")
        canvas.Update()

        canvas.Print(canvasName+".png")
        canvas.Print(canvasName+".pdf")


        #graph = ROOT.TGraphAsymmErrors()
        #graph.SetPoint( 0, 1, 1 )
        #graph.SetPointError( 0, 0.5, 2, .1 , .2 )
        #graph.Draw()





        #TH2F *h = new TH2F("h", "", 1, border_lo, border_hi, nrNuis + offset + 1, -offset, nrNuis + 1);

        #border_lo = -1
        #border_hi = +1
        
        
        #collections.defaultdict(dict)



        #for x in sorted(prefitErrors):  ( x, prefitErrors[x] )
        #for x in sorted(prefitMeans):   ( x, prefitMeans[x] )
        #for x in sorted(postfitValues): ( x, postfitValues[x] )
        #for x in sorted(postfitErrors): ( x, postfitErrors[x] )
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



    #######################################
    #def yieldBranchAndContent(TTree, cutAt = 10):
    #
    #
    #    for branch in pullTTree.GetListOfBranches():    branch     
    #        
    #        varName =  branch.GetName() 
    #        cutString = varName + " < " + str(cutAt)
    #
    #        arrayFromTTree = RootTools.GetValuesFromTree(TTree, varName, cutString)
    #
    #        mass = int(re.search("\d{2}", varName).group())  # systematics
    #
    #        yield mass, arrayFromTTree
        



    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

