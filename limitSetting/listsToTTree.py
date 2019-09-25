import ROOT # to do all the ROOT stuff
import array

def fillTTreeWithDictOfList(aDict):
    # input: aDict[ 'branchName1'] = [n1, n2 ,n3, ...]
    #        aDict[ 'branchName2'] = [m1, m2 ,m3, ...]
    # list elemets are assumed to be numbers and are going to be saved as floats

    # make sure that all the lists are the same leng

    nListElements = len(aDict.values()[0])

    if len(aDict.keys()) > 1: # if we have more than one list, make sure they all have the same length
        for aList in aDict.values(): assert len(aList) == nListElements


    TTree = ROOT.TTree( 'myTTree', 'myTTree' ) # this will be TTree to fill and output

    # each TTree branch needs to be associated with an array
    # we will set those up here and associate them with each other
    arrayDict = {}

    for key in aDict: 
        # setup the array
        arrayDict[key] = array.array( "f", [ 0. ] )      # can also use "d" here for doubles
        TTree.Branch( key, arrayDict[key], key+"/F" )# can also use "D" here for doubles


    # fill the branches
    for n in xrange( nListElements ): # loop over list elemets
        for key in aDict: # fill the arrays with the n-th element of the lists
            arrayDict[key][0] = aDict[key][n]
        # fill all the branches of the TTree
        TTree.Fill()

    return TTree



if __name__ == '__main__':

    testDict = {}

    testDict["var1"] = range(10)
    testDict["var2"] = [ 2*x for x in xrange(10)]


    myTTree = fillTTreeWithDictOfList(testDict)

    myTTree.Scan()


    testTFile = ROOT.TFile( 'test.root', 'recreate' )

    myTTree.Write()

    testTFile.Write()
    testTFile.Close()

