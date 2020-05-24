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


if __name__ == '__main__':

    inputFileName = "limitOutput_asimov_PullsAndFitImpacts.root"

    inputTFile = ROOT.TFile(inputFileName, "OPEN")

    pullParamDict, impactParamDict = getPullAndImpactTTreeDicts(inputTFile)



    

    #for x in sorted(pullParamDict.keys()) : pullParamDict[x]
    for mass in sorted(pullParamDict.keys()) :
        pullTTree = pullParamDict[mass]
        impactTTree = impactParamDict[mass]


        pullMeanDict, pullErrorDict = calculatePulls(pullTTree)

        graph = ROOT.TGraphAsymmErrors()
        graph.SetName("TestGraph")

        nLabels = len(pullMeanDict)


        offset = 0
        # TH2F ( *name,  *title, Int_t nbinsx, Double_t xlow, Double_t xup, Int_t nbinsy, Double_t ylow, Double_t yup)
        labelTH2 = ROOT.TH2F("labelHist", "labelHist", 1, -1.2, +1.2, nLabels + offset + 1, -offset, nLabels + 1);

        counter = 0 
        for nuisanceParameter in sorted(pullMeanDict): 
            counter += 1
            
            graph.SetPoint( counter, 0, counter )

            # these are really erros here. I.e. how far the error bars extend in each direction from the center point
            graph.SetPointError( counter, pullErrorDict[nuisanceParameter],pullErrorDict[nuisanceParameter], 0 , 0 )  


            nuisanceParameterYLabel = nuisanceParameter.strip("_") # remove leading and trailing underscores
            labelTH2.GetYaxis().SetBinLabel(counter, nuisanceParameterYLabel)

            #graph.GetYaxis().SetBinLabel(counter, x)


        #labelTH2.GetYaxis().SetTitleOffset(2.)
        labelTH2.SetStats( False) # remove stats box
        canvas = ROOT.TCanvas()
        canvas.SetLeftMargin(0.45)


        #pad1 = ROOT.TPad("pad1", "pad1", 0.0, 0.0, 1.0, 1.0, 0);
        #pad1.SetLeftMargin(0.35)
        #pad1.Draw();
        #pad1.cd();

        labelTH2.Draw()
        graph.Draw("same")
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

