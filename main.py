#!/usr/bin/python3

import os
import sys
import time
from datetime import datetime
import json
import argparse
from pwd import getpwuid
from collections import defaultdict
import shutil
import ldap
import smtplib
from email.message import EmailMessage

class warnFile:
    def __init__(self,quarantine,max_age):

        self.quarantine=quarantine
        self.max_age=max_age+quarantine

        try:
            with open('warnfile', 'r') as self.json_data:
                self.warnStore = json.load(self.json_data)
                self.json_data.close()

                self.wf_age=int((time.time()-float(self.warnStore['date']))/86400)
                if self.wf_age >= self.quarantine:
                    self.isKillable=True
                else:
                    self.isKillable=False

        except:
            self.warnStore=None



    def write(self,fHash):
        self.warnStore=fHash

        with open('warnfile', 'w') as outfile:
            json.dump(fHash, outfile)


    def dump(self):
        print(self.warnStore)


    def kill(self):
        self.logFileName=datetime.now().strftime('killed.%d%m%Y.log')
        self.rmFiles=[]

        if not self.isKillable:
            print("WARN: Filesystem scan is not long enough in quarantine")

        else:
            for self.f in self.warnStore['file'].keys():
                if not os.path.isfile(self.f):
                    continue

                self.age=int(time.time()-os.path.getmtime(self.f))//86400
                if self.age > self.max_age:
                    self.rmFiles.append(self.f)
                    #os.remove(self.f)

            with open(self.logFileName, "a") as self.killLog:
                self.killLog.write("Killed on {}".format(datetime.now().strftime('%d.%m.%Y')))
                if self.rmFiles:
                    self.killLog.write("\n".join(self.rmFiles))
                    self.killLog.write("\n")

        return(self.rmFiles)


class fileSystem:
    def __init__(self,root,max_age):
        self.fs={'file':{},'date':time.time()}
        self.start_path=root
        self.max_age=max_age
        self.fileOwner=defaultdict(list)

        for self.dirpath, self.dirnames, self.filenames in os.walk(self.start_path):
            for self.f in self.filenames:
                self.fp = os.path.join(self.dirpath, self.f)
                if os.path.isfile(self.fp):
                    self._storeFile(self.fp)


    def _storeFile(self,fp):
        self.file=fp
        self.age=(time.time()-os.path.getmtime(fp)) // (24 * 60 * 60)

        if self.age > self.max_age:
            try:
                self.owner = getpwuid(os.stat(self.file).st_uid).pw_name
            except KeyError:
                self.owner='nobody'

            self.fileOwner[self.owner].append(self.file)
            self.fs['file'][self.file]={'owner':self.owner,'age':self.age}


    def dump(self):
        print(self.fs)


    def reportOwner(self):
        for self.o in self.fileOwner.keys():
            self.repFileName="owner_{}.report".format(self.o)

            if os.path.isfile(self.repFileName):
                os.remove(self.repFileName)

            with open(self.repFileName,"w") as self.report:
                self.report.write("\n".join(self.fileOwner[self.o]))

            shutil.chown(self.repFileName, user=self.o, group=None)
            os.chmod(self.repFileName, 0o400)
            self.ownerEmail=self._getEmailAddress(self.o)
            self._sendReport(self.ownerEmail,self.fileOwner[self.o])


    def _sendReport(self,email,fileList):
        self.email=email
        self.fileList=fileList

        self.msg = EmailMessage()
        self.msg.set_content("\n".join(self.fileOwner[self.o]))

        # me == the sender's email address
        # you == the recipient's email address
        self.msg['Subject'] = 'List of files to be deleted for {}'.format(self.email)
        self.msg['From'] = "maxwell.service@desy.de"
        self.msg['To'] = "sven.sternberger@desy.de"

        self.s = smtplib.SMTP('mail.desy.de')
        self.s.send_message(self.msg)
        self.s.quit()

    def _getEmailAddress(self,uid):
        self.uid=uid

        ## first you must open a connection to the server
        try:
            self.l = ldap.open(host="it-ldap-slave.desy.de",port=1389)
            self.l.protocol_version = ldap.VERSION3
        except ldap.LDAPError as e:
            print(e)

        self.baseDN = "ou=rgy,o=DESY,c=DE"
        self.searchScope = ldap.SCOPE_SUBTREE
        ## retrieve all attributes - again adjust to your needs - see documentation for more options
        self.retrieveAttributes = ['mail']
        self.searchFilter = "uid={}".format(uid)

        try:
            self.result=""
            self.ldap_result_id = self.l.search(self.baseDN, self.searchScope,self.searchFilter, self.retrieveAttributes)
            self.result_type, self.result_data = self.l.result(self.ldap_result_id, 0)
            if self.result_type == ldap.RES_SEARCH_ENTRY:
                self.result=self.result_data[0][1]['mail'][0].decode("utf-8")
            else:
                self.result="bitbucket@desy.de"

        except ldap.LDAPError as e:
            print(e)

        return(self.result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("root_path")
    parser.add_argument("-f","--force", action="store_true")
    parser.add_argument("-m","--max_age",type=int)
    parser.add_argument("-q","--quarantine",type=int)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-sfs", "--scanFS", action="store_true")
    group.add_argument("-cfs", "--cleanFS", action="store_true")
    args=parser.parse_args()

    if not args.quarantine:
        quarantine=40
    else:
        quarantine=args.quarantine

    if not args.max_age:
        max_age=90
    else:
        max_age=args.max_age

    myWarnFile=warnFile(quarantine,max_age)
    if args.scanFS:
        myfs=fileSystem(args.root_path,max_age)
        if myWarnFile.warnStore and not args.force:
            print("WARN: Old warn file found. Give --force to overwrite")
        else:
            myWarnFile.write(myfs.fs)
            myfs.reportOwner()

    elif args.cleanFS:
        rmFiles=myWarnFile.kill()
        print("Removed {} files from {}".format(len(rmFiles),args.root_path))
    else:
        print("WARN: nothing to do. give --scanFS or --cleanFS")


    #print(resHash)
    #myWarnFile.write(resHash)

    #myWarnFile.dump()
