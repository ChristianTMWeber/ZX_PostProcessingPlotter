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

    paretnDir = "/direct/usatlas+u/chweber/usatlasdata/signalDAODs"

    count = 0

    for (root,dirs,files) in os.walk(paretnDir): 
        for file in files:

            regexMatch =  re.search("(?<=Zd)\d\d",root)

            if not regexMatch : continue

            count += 1

            inputLocation = os.path.join(root,file)

            tTreeName = "truthTree_Zd_" + regexMatch.group() + "_GeV"

            outputName = "ZX_truthTTree_%03i.root" % count

            submitLine = "python truthPlots_pyROOT.py %s --outputName %s --tTreeName %s --nEventsToProcess %i" %(inputLocation, outputName, tTreeName, -1)

            #import pdb; pdb.set_trace()
            shellScript = "truthOnGrid_%03i.sh" % count
            with open(shellScript, "w") as shellWrite:
                shellWrite.write('#!/bin/bash\n')
                shellWrite.write('%s\n' %submitLine)
                #b.write(gangacmd)

            os.chmod(shellScript, 0755)

            submitScriptName = makeSubmitScript( shellScript)

            os.system( "condor_submit " + submitScriptName)

    #time.sleep(1)

    print("All submitted!")


    #import pdb; pdb.set_trace()