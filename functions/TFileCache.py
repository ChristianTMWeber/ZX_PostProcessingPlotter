import os
import shutil 

"""
TFileCache( pathToFile , tFileModality = "READ")

This is a helper file for when running ROOT from a linux container on a Windows machine
There is some overhead when acessing files from wihtin the container that are stored in the Windows file system.

This overhad can be meaningfull when processing larger files. 
As a workaround TFileCache copies the file to a folder in the linux file system, before opening the TFile.

"""


def copyToTemp( inputFile, targetDir = os.path.expanduser("/tmp")):
    

    if not os.path.exists(targetDir): os.mkdir(targetDir)

    fileName = inputFile.split("/")[-1]

    targetPath = os.path.join(targetDir,fileName)

    dest = shutil.copyfile(inputFile, targetPath) 

    return targetPath


def TFileCache( pathToFile , tFileModality = "READ"):

    import ROOT

    cachedFile =  copyToTemp( pathToFile) # copy the file to the to a temporary linux file system, to speed up access when using a container

    return ROOT.TFile(cachedFile, tFileModality)



if __name__ == '__main__':


    def generate_big_random_letters(filename,size):
        """
        generate big random letters/alphabets to a file
        :param filename: the filename
        :param size: the size in bytes
        :return: void
        """
        import random
        import string

        chars = ''.join([random.choice(string.letters) for i in range(size)]) #1


        with open(filename, 'w') as f:   f.write(chars)
        return None



    referenceFileName = "test.txt"

    generate_big_random_letters(referenceFileName,100)

    cachedFileName = copyToTemp( referenceFileName )


    referenceFile = open(referenceFileName, "r")
    referenceOutput = referenceFile.read() 

    os.remove(referenceFileName)




    cachedFile = open(cachedFileName, "r")

    cachedFileOutput = cachedFile.read() 

    os.remove(cachedFileName)

    assert  referenceOutput == cachedFileOutput

    print( "TFileCache / copyToTemp passed test!")



