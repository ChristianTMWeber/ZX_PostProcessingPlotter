import ROOT

def generateTDirContents(TDir):
    # this is a python generator 
    # this one allows me to loop over all of the contents in a given ROOT TDir with a for loop

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    for TKey in TDirKeys: 
        yield TKey.ReadObj() # this is how I access the element that belongs to the current TKey


if __name__ == '__main__':


    fullFile = ROOT.TFile("allShapes.root","OPEN")

    subsetFile = ROOT.TFile("subsetShapes.root", "RECREATE")

    subsetFile.cd()

    for tObject in generateTDirContents(fullFile): 

        if "m34" in tObject.GetName(): tObject.Write()


    subsetFile.Close()

    import pdb; pdb.set_trace() # import the debugger and instruct it to stop here