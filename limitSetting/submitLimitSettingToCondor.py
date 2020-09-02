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
        submitWrite.write("getenv                  = True\n" )
        submitWrite.write("#should_transfer_files   = YES\n" )
        submitWrite.write("#when_to_transfer_output = ON_EXIT\n" )
        submitWrite.write("accounting_group = group_atlas.tier3.yale\n" )
        submitWrite.write("Queue 1\n" )
        #submitWrite.write("#queue filename matching (/direct/usatlas+u/chweber/ZdZd_area/Pull-rankingTool/condor/mZd15_combined_NormalMeasurement_model/*.sh)\n" )

    os.chmod(submitScriptName, 0755)


    return submitScriptName

if __name__ == '__main__':

    parentFolder = "/usatlas/u/chweber/usatlasdata/backgroundDAODs/"

    massPoints = [16, 17]

    for mass in massPoints:


        submitLine = "python limitSetting.py --inputFileName  post_20200809_203927_ZX_Run2_BckgSignal_PreppedHist_PMGWeights_V3.root  --limitType asymptotic --nSystematics 0  --skipStatAndTheoryError --outputDir /direct/usatlas+u/chweber/ZdZd_area/ZX_PostProcessingPlotter/limitSetting/testCondor --outputFileName test_Zd_%i.root --nMassPoints %i" %(mass, mass)

        #import pdb; pdb.set_trace()
        shellScript = "batchRun_"+str(mass)+".sh"
        with open(shellScript, "w") as shellWrite:
            shellWrite.write('#!/bin/bash\n')
            shellWrite.write('%s\n' %submitLine)
            #b.write(gangacmd)

        os.chmod(shellScript, 0755)

        submitScriptName = makeSubmitScript( shellScript)

        os.system( "condor_submit " + submitScriptName)

        time.sleep(1)

    print("All submitted!")


    #import pdb; pdb.set_trace()