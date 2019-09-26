import ROOT # to do all the ROOT stuff
import array
import re

def fillTTreeWithDictOfList(aDict, treeName = "myTTree" ):
    # input: aDict[ 'branchName1'] = [n1, n2 ,n3, ...]
    #        aDict[ 'branchName2'] = [m1, m2 ,m3, ...]
    # list elemets are assumed to be numbers and are going to be saved as floats

    # make sure that all the lists are the same leng

    nListElements = len(aDict.values()[0])

    if len(aDict.keys()) > 1: # if we have more than one list, make sure they all have the same length
        for aList in aDict.values(): assert len(aList) == nListElements


    TTree = ROOT.TTree( treeName, treeName ) # this will be TTree to fill and output

    # each TTree branch needs to be associated with an array
    # we will set those up here and associate them with each other
    arrayDict = {}

    for key in aDict: 
        # setup the array
        arrayDict[key] = array.array( "f", [ 0. ] )      # can also use "d" here for doubles

        keyNoSpace = re.sub(" " , "_", key) # replace space with underscore, because spaces breat root :(
        TTree.Branch( keyNoSpace, arrayDict[key], keyNoSpace+"/F" )# can also use "D" here for doubles


    # fill the branches
    for n in xrange( nListElements ): # loop over list elemets
        for key in aDict: # fill the arrays with the n-th element of the lists
            arrayDict[key][0] = aDict[key][n]
        # fill all the branches of the TTree
        TTree.Fill()

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    return TTree



if __name__ == '__main__':

    testDict = {}

    testDict["var1"] = range(10)
    testDict["var2"] = [ 2*x for x in xrange(10)]
    testDict["var3"] = [ 1./(1+x) for x in xrange(10)]


    myTTree = fillTTreeWithDictOfList(testDict)

    myTTree.Scan()


    testTFile = ROOT.TFile( 'test.root', 'recreate' )

    myTTree.Write()

    testTFile.Write()
    testTFile.Close()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
