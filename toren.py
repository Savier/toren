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


import sys, os, os.path
import re
from fnmatch import fnmatch
import argparse

import transmissionrpc


def load_config():

  cfg = {}

  try:
    exec(open(os.path.expanduser('~/toren.config')).read(), cfg) #Little bit insecure
  except FileNotFoundError:
    pass

  for var in ('HOST', 'PORT', 'USER', 'PASW'):
    fullvar = 'TRANSMISSION_{0}'.format(var)
    cfg[fullvar] = cfg.get(fullvar) #Fill defaults with None

  return cfg


def make_client(cfg):
  if cfg['TRANSMISSION_HOST'] is None:
    print(cfg)
    print('Not configured. See README.')
    exit(1)
    
  return transmissionrpc.Client(cfg['TRANSMISSION_HOST'], 
                                port=cfg['TRANSMISSION_PORT'],
                                user=cfg['TRANSMISSION_USER'],
                                password=cfg['TRANSMISSION_PASW'])


def rename_torrent(client, fromname, toname):
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


def list_torrents(client, mask=None):
  for torrent in client.get_torrents():
    if mask is not None and not fnmatch(torrent.name, mask):
      continue
    print('{0}\t{1}'.format(torrent.id, torrent.name))


def move_torrent(client, filemask, path):
  #TODO make move
  raise NotImplemented
 

def argparser():
  parser = argparse.ArgumentParser(description='Transmission torrent renamer.')
  parser.add_argument('filemask', help='Glob mask defines torrent to rename.', nargs='?', default=None)
  parser.add_argument('newname', help='New name for torrent.', nargs='?', default=None)
  parser.add_argument('-m', '--move', help='Move torrent data to specified path.')
  parser.add_argument('-u', '--url', help='Where to find transmission instance, ex user:password@host:port.')

  return parser.parse_args()


def parse_url(url):
  URL_RE = re.compile('((?P<user>[^:]+)(:(?P<pasw>.+))?@)?(?P<host>[^@:]+)(:(?P<port>\\d+))?')
  match = URL_RE.match(url)
  if match is None:
    raise BadUrlSyntax

  gr = match.groupdict()
  #print(gr.get('user'), gr.get('pasw'), gr.get('host'), gr.get('port')) 
  return gr.get('user'), gr.get('pasw'), gr.get('host'), gr.get('port')


if __name__ == '__main__':
  args = argparser()

  if args.url:
    cfg = {}
    (cfg['TRANSMISSION_USER'], 
    cfg['TRANSMISSION_PASW'], 
    cfg['TRANSMISSION_HOST'],
    cfg['TRANSMISSION_PORT'] ) = parse_url(args.url)
  else:
    cfg = load_config()

  client = make_client(cfg)
  
  if not args.filemask:
    list_torrents(client)
    exit(0)

  if args.move:
    move_torrent(client, args.filemask, args.move)

  if not args.newname:
    if not args.move:
      list_torrents(client, args.filemask)

  else:
    if rename_torrent(client, args.filemask, args.newname):
      print('Ok.')
    else:
      print('Failed.')
