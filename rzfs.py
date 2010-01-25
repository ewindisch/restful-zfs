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
        '/iscsit/(.*)', 'iscsitDB'
)

class AbstractDB(object):
    """Abstract database that handles the high-level HTTP primitives."""
    def GET(self, name):
        try:
            return json.dumps(self.get_key(str(name)))
        except:
            return None

class iscsitDB(AbstractDB):
    """Accesses iscsitadm"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/iscsitadm","list","target","-v",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            #return soo[0].rstrip("\n").split("\t")
            di=dict()
            for line in soo[0].splitlines():
                kval=line.strip(" ").split(":",1)
                di[kval[0]]=kval[1].strip(" ")
            return di
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        
class zfsDB(AbstractDB):
    """Accesses zfs"""

    def get_key(self, key):
        try:
            sp=subprocess.Popen(("/usr/sbin/zfs","list","-H",key),stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            soo=sp.communicate()
            return soo[0].rstrip("\n").split("\t")
        except Exception as (errno):
            return "Error on key ({0}) - ({1})".format(key, errno)
        
if __name__ == "__main__":
    web.application(urls, globals()).run()
