import re
import os
import time 

def makeSubmitScript( shellScriptName):

    submitScriptName = re.sub(".sh", ".sub", shellScriptName) # replace '.sh' with '.sub'
    with open(submitScriptName, "w") as submitWrite:
        submitWrite.write("universe                = vanilla\n" )
        submitWrite.write("executable              = "+shellScriptName+"\n" )
        submitWrite.write("# Get the environment from the submission host?\n" )
        submitWrite.write("#arguments               = $Fnx(filename)\n" )
        submitWrite.write("output                  = $(ClusterId).$(ProcId).out\n" )
        submitWrite.write("error                   = $(ClusterId).$(ProcId).err\n" )
        submitWrite.write("log                     = $(ClusterID).log\n" )
        #submitWrite.write("request_memory          = 4 GB\n" )
        submitWrite.write("getenv                  = True\n" )
        submitWrite.write("#should_transfer_files   = YES\n" )
        submitWrite.write("#when_to_transfer_output = ON_EXIT\n" )
        submitWrite.write("accounting_group = group_atlas.tier3.yale\n" )
        #submitWrite.write("accounting_group = group_atlas.tier3.yale.long\n" )
        submitWrite.write("Queue 1\n" )
        #submitWrite.write("#queue filename matching (/direct/usatlas+u/chweber/ZdZd_area/Pull-rankingTool/condor/mZd15_combined_NormalMeasurement_model/*.sh)\n" )

    os.chmod(submitScriptName, 0755)


    return submitScriptName

if __name__ == '__main__':

    paretnDir = "/usatlas/u/chweber/usatlasdata/Za_DAOD_samples/"
    #paretnDir = "/usatlas/u/chweber/usatlasdata/ZX_signalDAOD"
    #paretnDir = "/usatlas/u/chweber/usatlasdata/ZX_signalDAOD/"

    count = 0

    doZa = True
    doZX = False#True

    doTruthPlots = False
    doFiducialmeasruement = True

    for (root,dirs,files) in os.walk(paretnDir): 
        for file in files:

            if "r9315"    in root: fileSuffix = "_mc16a" # select only mc16a
            elif "r10201" in root: fileSuffix = "_mc16d" # select only mc16d
            elif "r10724" in root: fileSuffix = "_mc16e" # select only mc16e
            else:                  fileSuffix = ""

            if doZX:  regexMatch =  re.search("(?<=Zd)\d\d",root)
            elif doZa:
                alteredRoot = re.sub("_a_", "_a", root)
                regexMatch =  re.search("(?<=_a)\d+",alteredRoot)

            if not regexMatch : continue

            count += 1

            inputLocation = os.path.join(root,file)

            if doTruthPlots: 
                tTreeName = "truthTree_Zd_" + regexMatch.group() + "_GeV"
                outputName = "ZX_truthTTree_%03i_.root" % count
                submitLine = "python truthPlots_pyROOT.py %s --outputName %s --tTreeName %s --nEventsToProcess %i" %(inputLocation, outputName, tTreeName, -1)

            elif doFiducialmeasruement: 
                outputName = outputName = "ZX_Fiducial_%03i%s.root" % (count,fileSuffix)
                histName = "mZd" + regexMatch.group() + ""
                if doZa: 
                    outputName = outputName = "Za_Fiducial_%03i%s.root" % (count,fileSuffix)
                    histName = "ma" + regexMatch.group()
                #outputName = outputName = "ZX_Fiducial_%03i_mc16e.root" % count
                submitLine = "python measureFiducialAcceptance_pyROOT.py %s --outputName %s --nEventsToProcess %i --outputHistName %s" %(inputLocation, outputName, -1, histName)



            #import pdb; pdb.set_trace()
            shellScript = "truthOnGrid_%03i.sh" % count
            with open(shellScript, "w") as shellWrite:
                shellWrite.write('#!/bin/bash\n')
                shellWrite.write('%s\n' %submitLine)
                #b.write(gangacmd)

            os.chmod(shellScript, 0755)

            submitScriptName = makeSubmitScript( shellScript)

            #print inputLocation

            os.system( "condor_submit " + submitScriptName)

    #time.sleep(1)

    print("All submitted!")


    #import pdb; pdb.set_trace()