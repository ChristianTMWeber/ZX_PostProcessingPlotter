import ROOT
import collections # so we can use collections.defaultdict to more easily construct nested dicts on the fly
import re
import difflib # to help me match strings via 'difflib.get_close_matches'


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

if __name__ == '__main__':

    inputFileName = "limitOutput_asimov_PullsAndFitImpacts.root"

    inputTFile = ROOT.TFile(inputFileName, "OPEN")

    pullParamDict, impactParamDict = getPullAndImpactTTreeDicts(inputTFile)



    

    #for x in sorted(pullParamDict.keys()) : pullParamDict[x]
    for mass in sorted(pullParamDict.keys()) :
        pullTTree = pullParamDict[mass]
        impactTTree = impactParamDict[mass]


        pullMeanDict, pullErrorDict = calculatePulls(pullTTree)
        impactVarDict = makeImpacts(impactTTree)

        pullGraph = ROOT.TGraphAsymmErrors()
        pullGraph.SetName("pullGraph")

        prefitImpactGraph = ROOT.TGraphAsymmErrors()
        prefitImpactGraph.SetName("prefitImpactGraph")

        postfitImpactGraph = ROOT.TGraphAsymmErrors()
        postfitImpactGraph.SetName("postfitImpactGraph")

        nLabels = len(impactVarDict)


        offset = 0.5
        th2Name = "Pull and fit impact, m_{Z_{d}} = %i GeV" %mass
        # TH2F (                   *name,  *title, Int_t nbinsx, Double_t xlow, Double_t xup, Int_t nbinsy, Double_t ylow, Double_t yup)
        labelTH2 = ROOT.TH2F("labelHist", th2Name, 1, -1.2, +1.2,                         nLabels + 1, +offset, nLabels + 1 + offset);
        labelTH2.GetXaxis().SetTitle("(#hat{#theta} - #theta_{0})/#Delta#theta , fit impact" )


        impactTH2 = ROOT.TH2F("impactTH2", "impactTH2", 1, -0.2, +.2,                         nLabels + 1, +offset, nLabels + 1 + offset);


        counter = 0 
        #for nuisanceParameter in sorted(pullMeanDict): 
        for nuisanceParameter in sorted(impactVarDict): 
            counter += 1

            print "%i %s" %(counter, nuisanceParameter)
            
            # make pull plots
            if nuisanceParameter in pullMeanDict:
                pullPointNr = pullGraph.GetN()
                pullGraph.SetPoint( pullPointNr, pullMeanDict[nuisanceParameter] , counter )
                # these are really erros here. I.e. how far the error bars extend in each direction from the center point
                pullGraph.SetPointError( pullPointNr, pullErrorDict[nuisanceParameter],pullErrorDict[nuisanceParameter], 0 , 0 )  

            #make impact plots

            impactVars = impactVarDict[nuisanceParameter]


            #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
            if "mu_preFitUp_" in impactVars:
                prefitPointNr = prefitImpactGraph.GetN()

                prefitMean = impactVars["mu_preFitUp_"] - impactVars["mu_preFitDown_"]
                prefitImpactGraph.SetPoint( prefitPointNr, 0 , counter )
                # these are really erros here. I.e. how far the error bars extend in each direction from the center point
                prefitImpactGraph.SetPointError( prefitPointNr, abs(impactVars["mu_preFitDown_"]), abs(impactVars["mu_preFitUp_"]), 0.4 , 0.4 )  

            postfitPointNr = postfitImpactGraph.GetN()

            
            postfitMean = impactVars["mu_postFitUp_"] - impactVars["mu_postFitDown_"]
            postfitImpactGraph.SetPoint( postfitPointNr, 0 , counter )
            # these are really erros here. I.e. how far the error bars extend in each direction from the center point
            postfitImpactGraph.SetPointError( postfitPointNr, abs(impactVars["mu_postFitDown_"]), abs(impactVars["mu_postFitUp_"]), 0.4 , 0.4 )  


            nuisanceParameterYLabel = nuisanceParameter.strip("_") # remove leading and trailing underscores
            labelTH2.GetYaxis().SetBinLabel(counter, nuisanceParameterYLabel)

            #pullGraph.GetYaxis().SetBinLabel(counter, x)






        #labelTH2.GetYaxis().SetTitleOffset(2.)
        labelTH2.SetStats( False) # remove stats box
        canvas = ROOT.TCanvas()
        canvas.SetLeftMargin(0.45)


        #pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.0, 1.0, 1.0, 0);
        #pad1.SetLeftMargin(0.35)
        #pad1.Draw();
        #pad1.cd();

        labelTH2.Draw()
        


        #impactTH2.Draw("same")


        prefitImpactGraph.SetFillColor( ROOT.kAzure);
        #prefitImpactGraph.SetFillStyle(3001);
        prefitImpactGraph.Draw("same 2 ")

        ROOT.gStyle.SetHatchesLineWidth(2) #define the hatches line width.
        ROOT.gStyle.SetHatchesSpacing(0.5) # to define the spacing between hatches.


        postfitImpactGraph.SetFillColor(1);
        postfitImpactGraph.SetFillStyle(3354);
        #postfitImpactGraph.SetFillColor(ROOT.kGray+3);
        #postfitImpactGraph.SetLineWidth()
        postfitImpactGraph.Draw("same 2 ")

        pullGraph.Draw("same P")


        legend = setupTLegend()

        legend.AddEntry(pullGraph , "pull"  , "l");
        legend.AddEntry(prefitImpactGraph , "prefitImpact" , "f");
        legend.AddEntry(postfitImpactGraph , "postfitImpact" , "f");
        legend.Draw()



        canvas.Update()


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
        import pdb; pdb.set_trace() # import the debugger and instruct it to stop here



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

