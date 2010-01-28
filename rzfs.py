#!/usr/bin/env python2.6
# restful-zfs - Access ZFS and iscsitadm via a restful API
# Copyright (C) 2010 Eric Windisch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess

import web
import re
import uuid

import json

urls = ('/zfs/(.*)', 'zfsDB',
        '/iscsitadm/tpgt/(.*)', 'iscsitDBtpgt',
        '/iscsitadm/target/(.*)', 'iscsitDBtarget',
        '/iscsitadm/initiator/(.*)', 'iscsitDBinitiator',
        '/iscsitadm/admin/(.*)', 'iscsitDBadmin',
        '/iscsitadm/stats/(.*)', 'iscsitDBstats'
)

class AbstractDB(object):
    """Abstract database that handles the high-level HTTP primitives."""
    def GET(self, name):
        try:
            return json.dumps(self.get_key(str(name)))
        except:
            return None

    def POST(self, name):
        try:
            return json.dumps(self.put_key(str(name)))
        except:
            return None

class iscsitDBstats(AbstractDB):
    """Accesses iscsitadm stats"""

    def get_key(self, key):
        try:
            if key:
                sp=subprocess.Popen(("/usr/sbin/iscsitadm","show","stats",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                sp=subprocess.Popen(("/usr/sbin/iscsitadm","show","stats"),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            di=dict()
            soo0=soo[0].splitlines()
            for line in soo0[3:]:
                kval=line.split()
                name=kval[0]
                di[name]=dict()
                # read iops
                di[name]['read-ops']=kval[1]
                # write iops
                di[name]['write-ops']=kval[2]
                # read bw
                di[name]['read-bw']=kval[3]
                # write bw
                di[name]['write-bw']=kval[4]
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        

class iscsitDBadmin(AbstractDB):
    """Accesses iscsitadm admin"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/iscsitadm","show","admin"),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            di=dict()
            for line in soo[0].splitlines():
                kval=line.strip(" ").split(":",1)
                di[kval[0]]=kval[1].strip(" ")
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        

class iscsitDBinitiator(AbstractDB):
    """Accesses iscsitadm initiator"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/iscsitadm","list","initiator","-v",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            di=dict()
            for line in soo[0].splitlines():
                kval=line.strip(" ").split(":",1)
                di[kval[0]]=kval[1].strip(" ")
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        

class iscsitDBtpgt(AbstractDB):
    """Accesses iscsitadm tpgt"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/iscsitadm","list","tpgt","-v",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            di=dict()
            for line in soo[0].splitlines():
                kval=line.strip(" ").split(":",1)
                di[kval[0]]=kval[1].strip(" ")
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        

class iscsitDBtarget(AbstractDB):
    """Accesses iscsitadm target"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/iscsitadm","list","target","-v",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            ret=dict()
            di=dict()
            for line in soo[0].splitlines():
                kval=line.strip(" ").split(":",1)
                di[kval[0]]=kval[1].strip(" ")
            ret[di['Target']]=di
            return ret
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        
class zfsDB(AbstractDB):
    """Accesses zfs"""

    def get_key(self, key):
        try:
            if key:
                sp=subprocess.Popen(("/usr/sbin/zfs","list","-H",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                sp=subprocess.Popen(("/usr/sbin/zfs","list","-H"),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            di=dict()
            soo0=soo[0].splitlines()
            for line in soo0:
                kval=line.split()
                name=kval[0]
                di[name]=dict()
                di[name]['used']=kval[1]
                di[name]['avail']=kval[2]
                di[name]['refer']=kval[3]
                di[name]['mntpnt']=kval[4]
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)


    def put_key(self,volname):
        try:
            zdata=json.loads(web.data())
            if not volname:
                if zdata['volname']:
                    volname=zdata['volname']
                else:
                    return web.internalerror("volname not specified.")

            if volname and zdata['volsize']:
                cmd=("/usr/bin/pfexec","/usr/sbin/zfs","create","-V",zdata['volsize'],volname)
                sp=subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                soo=sp.communicate()
                return soo[0]
            else:
                return web.internalerror("volsize not specified.")
            return 999

        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(volname, errno)


if __name__ == "__main__":
    app=web.application(urls, globals()).run()