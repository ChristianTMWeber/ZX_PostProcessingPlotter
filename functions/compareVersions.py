import re # regular expression, so that we can find all the digits in our version string

def compareVersions( versionStr1, versionStr2 ):

    #def getAllDigits( aVersionString ) : return re.findall("\d{1}",AA)

    getAllDigits =  lambda aVersionString : re.findall("\d{1}",aVersionString)

    version1ReOut = getAllDigits(versionStr1)
    version2ReOut = getAllDigits(versionStr2)

    version1Int = int( "".join(version1ReOut))
    version2Int = int( "".join(version2ReOut))

    deltaLength = len(version1ReOut) - len(version2ReOut)

    # resolve the issue of possible ommitted trailing zeros by multiplying with a power of 10
    if deltaLength > 0 :
        version2Int *= 10**( deltaLength  )
    elif deltaLength < 0:
        version1Int *= 10**( -deltaLength  )

    # cmp(a,b) Returns: -1 if a<b ;  0 if a=b ; 1 if a>b        
    return cmp(version1Int, version2Int)



if __name__ == '__main__':

    # get ROOT version
    # ROOT.gROOT.GetVersion()

    assert compareVersions( '6.14/04', '6.14/04' ) == 0 
    assert compareVersions( '6.15/04', '6.14/04' ) == 1
    assert compareVersions( '6.15/04', '6.20/04' ) == -1
    assert compareVersions( '6.14/0', '6.14/' ) == 0 


    print("All ok!")



#import pdb; pdb.set_trace() # import the debugger and instruct it to stop here