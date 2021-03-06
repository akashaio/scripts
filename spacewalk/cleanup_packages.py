#!/usr/bin/python
# Script that uses RHN API to cleanup obsolete packages
# on Spacewalk server.
# Copyright (C) 2012  Nicolas PRADELLES
#
# Author: Nicolas PRADELLES (npradelles@eutelsat.fr)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Version Information:
# 0.2 - 2012-08-27 - Script rewritten in Python to access Spacewalk XML RPC API
# 0.1 - 2012-04-17 - First Release


import xmlrpclib
import string
import os

# CONFIG
## URL of Spacewalk XML RPC server
SATELLITE_URL = "https://server/rpc/api"
## User with Org Admin role (required to delete package in Spacewalk)
SATELLITE_LOGIN = "user"
SATELLITE_PASSWORD = "secretsauce"

# Open connection to XML RPC server
client = xmlrpclib.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

# extract spacewalk channels
list = client.channel.listAllChannels(key)

all_del_pkg = 0

# For each channel
for channel in list:
  print "################\n" + channel.get('label')

  # extract all packages in channel
  all_array = client.channel.software.listAllPackages(key, channel.get('label'))
  # extract latest packages in channel
  lst_array = client.channel.software.listLatestPackages(key, channel.get('label'))


  # Extract useful datas to find obsolete packages
  all_pkg = ()
  lst_pkg = ()

  # create a unique string to define a package, exemple:  java-1.6.0-sun-jdbc%1.6.0.31%1jpp.1.el6_2%58920
  for pkg in all_array:
    all_pkg = all_pkg + (pkg.get('name') + '%' + pkg.get('version') + '%' + pkg.get('release') + '%' + str(pkg.get('id')),)

  for pkg in lst_array:
    lst_pkg = lst_pkg + (pkg.get('name') + '%' + pkg.get('version') + '%' + pkg.get('release') + '%' + str(pkg.get('id')),)


  # diff the two lists to find obsolete packages
  old_pkg = set(all_pkg) - set(lst_pkg)

  del_pkg = 0

  # if we have found obsolete packages
  if len(old_pkg) > 0:
    for pkg in old_pkg:
      pkg_params = string.split(pkg, '%')
      # check if the old package is installed on a managed client
      systems = client.system.listSystemsWithPackage(key, pkg_params[0], pkg_params[1], pkg_params[2])

      # if this package is not installed on a managed client
      if len(systems) == 0:
        # delete the package
        print pkg_params[0] + '-' + pkg_params[1]
        client.packages.removePackage(key, int(pkg_params[3]))
        del_pkg += 1

  all_del_pkg += del_pkg
  print "all: " + str(len(all_pkg)) + ", latest: " + str(len(lst_pkg)) + ", old: " + str(len(old_pkg)) + ", deleted: " + str(del_pkg)


# Delete rpm files on disk
if all_del_pkg > 0:
  print "################\n\n\nClean RPM files\n"
  os.system('spacewalk-data-fsck -r -S -C -O')

# disconnect
client.auth.logout(key)
