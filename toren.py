#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2013 Aleksandr Semenov <iamsav@gmail.com>
# Licensed under the MIT license.
#
# Script can list transmission downloads (use: toren [mask])
# And rename one-file torrents (use: toren mask newname)
#
# requires module 'transmissionrpc'

__author__    		= 'Aleksandr Semenov <iamsav@gmail.com>'
__version_major__   = 0
__version_minor__   = 1
__version__   		= '{0}.{1}'.format(__version_major__, __version_minor__)
__copyright__ 		= 'Copyright (c) 2013 Aleksandr Semenov <iamsav@gmail.com>'
__license__   		= 'MIT'


import sys
from fnmatch import fnmatch

import transmissionrpc


#TODO move to the options, config, and/or environment variables
TRANSMISSION_HOST = 'host'  # Where to look for transmission
TRANSMISSION_PORT = 9091    # port


def rename_torrent(fromname, toname):
  client = transmissionrpc.Client('netgear', port=8181)
  got = None
  
  #TODO fetch torrents in order one-by-one till needed one
  for torrent in client.get_torrents():
    #TODO option for varios matching styles?
    if fnmatch(torrent.name, fromname):
      got = torrent
      break
  
  if got is None:
    print('Not found torrent for {}'.format(fromname))
    return False

  files = got.files()
  #TODO come up with something to handle multiple files
  if len(files) != 1:
    print('Sorry, only one file per torrent supported (got {}).'.format(len(files)))
    return False

  #Ok, got good torrent in got
  client.rename_torrent_path(got.id, files[0]['name'], toname)
  print('Rename command sent.')
  torrent = client.get_torrent(got.id)
  print('Now torrent named {}'.format(torrent.name))
  return torrent.name == toname


def list_torrents(mask=None):
  client = transmissionrpc.Client('netgear', port=8181)
  for torrent in client.get_torrents():
    if mask is not None and not fnmatch(torrent.name, mask):
      continue
    print('{0}\t{1}'.format(torrent.id, torrent.name))


if __name__ == '__main__':
  print('Transmission torrent renamer.')
  
  #TODO Add some argv framework with configuration options etc.
  if len(sys.argv) == 1:
    list_torrents()
  elif len(sys.argv) == 2:
    list_torrents(sys.argv[1])
  elif len(sys.argv) != 3:
    print('Error in parameters.')
    print('Use: [toren fromname toname] to rename or [toren]/[toren mask] to list')
    print('Used: [{0}]'.format(']['.join(sys.argv)))
  else:
    if rename_torrent(sys.argv[1], sys.argv[2]):
      print('Ok.')
    else:
      print('Failed.')
