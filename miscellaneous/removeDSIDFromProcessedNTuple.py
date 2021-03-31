import ROOT
import argparse # to parse command line options


def TDirToList(TDir): # return the contents of a TDir as a list
    outputList = []
    for TKey in TDir.GetListOfKeys(): outputList.append( TKey.ReadObj() ) # this is how I access the element that belongs to the current TKey
    return outputList

#def getTDirContentNames(TDir): return [tObj.GetName() for tObj in TDirToList(TDir)] 
def getTDirContentNames(TDir): 
    for tObj in TDirToList(TDir): yield tObj.GetName()


def deleteObjectByNameMatch( TDir, tagForDeletion):
    for objectName in getTDirContentNames(TDir): 
        if tagForDeletion in objectName: 
            print( "deleting: " +objectName + ";1") 
            TDir.Delete( objectName + ";1") # need to add the ;1 manually

            assert( objectName not in [getTDirContentNames(TDir)] ) # check that it actually got deleted

    return None



if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    #parser.add_argument( "--outputName", type=str, default="checkPMGWeights.root" , help = "Pick the name of the output TFile." )
    #parser.add_argument( "--weightVariations", nargs='*', default=[] )
    #parser.add_argument( "--DSID", type=str, default="345060" )

    parser.add_argument("input", type=str, help="name or path to the input file, whose content we want to partially delete")
    parser.add_argument("DSID", type=str, nargs='*',help="DSID of the associated files we want to delete")

    args = parser.parse_args()


    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here

    file = ROOT.TFile(args.input,"UPDATE")

    for DSID in args.DSID: deleteObjectByNameMatch( file, DSID)

    cutflowTDir = file.Get("Cutflow").Get("Nominal")

    for DSID in args.DSID: deleteObjectByNameMatch( cutflowTDir, DSID)

    file.Close()

    print( "All done!")

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
