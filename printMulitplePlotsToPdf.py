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


def scaleCanvas(tCanvas, scale = 2, newHeight = None):
    # if "newHeight" is not None, interpret "scale" as "newWidth"
    # tCanvas needs to have been drawn

    old_width  = tCanvas.GetWindowWidth()
    old_height = tCanvas.GetWindowHeight()

    if newHeight is None:
        newWidth  = int(old_width*scale)
        newHeight = int(old_height*scale)
    else:
        newWidth  = int(scale)
        newHeight = int(newHeight)

    temp_canvas = ROOT.TCanvas("temp", "", newWidth , newHeight )
    tCanvas.DrawClonePad()

    temp_canvas.Update()

    temp_canvas.SetName(tCanvas.GetName())
    temp_canvas.SetTitle(tCanvas.GetTitle())

    return temp_canvas


if __name__ == '__main__':

    fileNameList = ["post_20200219_204021__ZX_Run2_AllReducibles_May_mc16ade_.root"]

    #figureNameList = ["ZXVR2_4mu_HighMassSideBand1_m4l", "ZXVR2_2e2mu_HighMassSideBand1_m4l", "ZXVR2_2mu2e_HighMassSideBand1_m4l", "ZXVR2_4e_HighMassSideBand1_m4l", "ZXVR2_All_HighMassSideBand1_m4l"]
    #figureNameList = ["ZXSR_4mu_HWindow_m4l", "ZXSR_2e2mu_HWindow_m4l", "ZXSR_2mu2e_HWindow_m4l", "ZXSR_4e_HWindow_m4l", "ZXSR_All_HWindow_m4l"]
    figureNameList = ["ZXSR_4mu_HWindow_m34", "ZXSR_2e2mu_HWindow_m34", "ZXSR_2mu2e_HWindow_m34", "ZXSR_4e_HWindow_m34", "ZXSR_All_HWindow_m34"]

    outputEnding = ".png"

    ROOT.gROOT.SetBatch(True)

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
                    # increase resolution for non-vector formats
                    
                    tCanvas = scaleCanvas(tCanvas, scale = 2)
                    #tCanvas.Draw()
                    tCanvas.Print(newFilename)

        file.Close()

    print "All done!"
    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here


