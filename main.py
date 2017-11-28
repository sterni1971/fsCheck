#!/usr/bin/python3

import os
import sys
import time
import json
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

class warnFile:
    def __init__(self):
        try:
            with open('data.txt', 'r') as json_data:
                self.warnStore = json.loads(json_data)
                json_data.close()

        except:
            self.warnStore=None

    def write(self.fHash):
        with open('data.txt', 'w') as outfile:
            json.dump(self.fHash, outfile)


def storeResult(metaHash):
    resHash['file'][metaHash['name']]={'owner':metaHash['owner'],'age':metaHash['age']}
    return None

if __name__ == '__main__':

    start_path=sys.argv[1]

    myWarnFile=warnFile()

    resHash={'file':{},'date':time.time()}

    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                print(fp)
                metaHash=getFileMetaData(fp)
                if metaHash['age'] > 90:
                    storeResult(metaHash)

                print(metaHash)

    print(resHash)
    warnFile(resHash)
