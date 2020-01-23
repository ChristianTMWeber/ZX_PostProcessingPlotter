import ROOT

# This script helps me to print multiple plots from mulitple 'plotPostProcess.py' output files to pdf
# The idea here is the following: 
# Let's say I have three output files from 'plotPostProcess.py':
#   ZX_mc16a_distributions.root, ZX_mc16d_distributions.root, ZX_mc16e_distributions.root
# And for each file I wanna plot the SignalRegion_m34 and SignalRegion_m4l figures
# This script helps me with that
#
# Just add the fileNames and figure names to the appropriate lists below
#

def generateTDirContents(TDir):
    # this is a python generator 
    # this one allows me to loop over all of the contents in a given ROOT TDir with a for loop

    TDirKeys = TDir.GetListOfKeys() # output is a TList

    for TKey in TDirKeys: 
        yield TKey.ReadObj() # this is how I access the element that belongs to the current TKey


def generateTDirPathAndContentsRecursive(TDir, baseString = "" , newOwnership = None):
    # for a given TDirectory (remember that a TFile is also a TDirectory) get all non-directory objects
    # redturns a tuple ('rootFolderPath', TObject) and is a generator

    baseString += TDir.GetName() +"/"

    for TObject in generateTDirContents(TDir):
        #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
        if newOwnership is not None: ROOT.SetOwnership(TObject, newOwnership) # do this to prevent an std::bad_alloc error, setting it to to 'True' gives permission to delete it, https://root.cern.ch/root/htmldoc/guides/users-guide/ObjectOwnership.html
        if isinstance(TObject, ROOT.TDirectoryFile ):

            for recursiveTObject in generateTDirPathAndContentsRecursive(TObject, baseString = baseString, newOwnership = newOwnership):
                yield recursiveTObject

        else :
            yield baseString + TObject.GetName() , TObject



if __name__ == '__main__':

    fileNameList = ["post_20191114_173904_mc16a_ZX_BckgSignalData_NoSyst_mc16a_.root",
                    "post_20191114_174147_mc16d_ZX_BckgSignalData_NoSyst_mc16d_.root",
                    "post_20191114_174252_mc16e_ZX_BckgSignalData_NoSyst_mc16e_.root",
                    "post_20191114_17_mc16ade_ZX_BckgSignalData_NoSyst_mc16ade_.root"]

    figureNameList = ["ZXVR1_4mu_LowMassSidebands_m34", "ZXVR1_2e2mu_LowMassSidebands_m34", "ZXVR1_2mu2e_LowMassSidebands_m34", "ZXVR1_4e_LowMassSidebands_m34", "ZXVR1_All_LowMassSidebands_m34"]

    outputEnding = ".pdf"

    for fileName in fileNameList:
        file = ROOT.TFile(fileName,"READ")

        # go through all objects in the file
        for path, tCanvas in generateTDirPathAndContentsRecursive(file):
            #check the given tObject against all the figureFileNames that we wanna print out
            for figureName in figureNameList:
                if figureName in tCanvas.GetName() :     


                    prefix = fileName.split(".")[0].split("_")[-2]

                    newFilename = prefix +"_" + figureName + outputEnding

                    tCanvas.Draw()
                    tCanvas.Print(newFilename)

        file.Close()

    print "All done!"
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


