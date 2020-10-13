import ROOT
import re
import os


def makeXRDCPFile( commandLines, fileName ="xrdcpTransferFromEOS.sh" ):

    with open(fileName, "w") as submitWrite:
        submitWrite.write('#!/bin/bash\n')
        for command in commandLines: submitWrite.write(command +'\n')

    return None



if __name__ == '__main__':


    sourceParentDir ="/afs/cern.ch/user/c/chweber/myEOS_locations/EOS_HBSM_ZdZd/production_20200222"

    realpath = os.path.realpath(sourceParentDir)

    requiredEnding = ".root"

    newDestinationPaths = set()


    xrdcpCommandLines = []



    for (root,dirs,files) in os.walk(realpath): 
        for file in files:

            if not file.endswith(requiredEnding): continue

            subdir =  re.search("(?<=%s/).*" %realpath ,root).group()

            newDestinationPaths.add(subdir)


            xrdcpCommand = "xrdcp  root://eosuser.cern.ch/%s   %s"  %(os.path.join(root,file), os.path.join(subdir,file))

            xrdcpCommandLines.append(xrdcpCommand)


    makeXRDCPFile( xrdcpCommandLines )

    print( "make sure the necessary subfolders have been created")

    for subdir in newDestinationPaths: print("mkdir " + subdir )

    #import pdb; pdb.set_trace() # import the debugger and instruct it to stop here
