#!/usr/bin/python3

import os
import sys
import time
from pwd import getpwuid

def getFileMetaData(fp):
    resHash={}

    resHash['name']=fp
    try:
        resHash['owner'] = getpwuid(os.stat(fp).st_uid).pw_name
    except KeyError:
        resHash['owner']='nobody'

    resHash['age']=(time.time()-os.path.getmtime(fp)) // (24 * 60 * 60)

    return(resHash)

def warnFile(fHash):
    with open(fHash['owner']+'.warn','a') as f:
        f.write(fHash['name']+'\n')


if __name__ == '__main__':

    start_path=sys.argv[1]

    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                print(fp)
                metaHash=getFileMetaData(fp)
                if metaHash['age'] > 90:
                    warnFile(metaHash)
                print(metaHash)
