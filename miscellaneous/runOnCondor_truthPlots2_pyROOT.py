import re
import os
import time 


import condorHelper.condorSubmitScriptMaker as condorSubmitScriptMaker


if __name__ == '__main__':

    paretnDir = "/gpfs/mnt/atlasgpfs01/usatlas/data/chweber/ReanaActiveLearningProject/generatedZXSamples/evnt"
    #paretnDir = "/usatlas/u/chweber/usatlasdata/ZX_signalDAOD"
    #paretnDir = "/usatlas/u/chweber/usatlasdata/ZX_signalDAOD/"


    relevantInputFileReTag = ".*\.truthDAOD\.pool\.root\.1"



    analysisScript = os.path.join(os.getcwd(),"truthPlots_pyROOT.py" )
    

    for (root,dirs,files) in os.walk(paretnDir): 
        for file in files:

            if not re.search(relevantInputFileReTag,file): continue

            #print(root)

            outputFileName = os.path.join(root,re.sub("\.truthDAOD\.pool\.",".flat.TTree.",file)) 

            fullPathToInputFile = os.path.join(root,file)


            tTreeName = "truthTree_Zd"
            
            runCommmand = "python %s %s --outputName %s --tTreeName %s --nEventsToProcess -1" %(analysisScript, fullPathToInputFile, outputFileName, tTreeName)


            shellScriptName = os.path.join(root,re.sub("\.truthDAOD\.pool\.root\.1",".sh",file))
            condorSubmitScriptMaker.writeShellScript(shellScriptName , runCommmand)

            submitScript = condorSubmitScriptMaker.makeSubmitScript(shellScriptName) # make a submit script for condor
            #submit the job to condor
            condorSubmitScriptMaker.submitToCondorFromSubmitScriptLocation(submitScript, changeDir = True, actuallySubmit = True)

            #import pdb; pdb.set_trace()

    #time.sleep(1)

    print("All submitted!")


    #import pdb; pdb.set_trace()