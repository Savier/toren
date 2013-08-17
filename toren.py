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
__version_major__   = 1
__version_minor__   = 0
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


def find_torrent(client, mask):
  for torrent in client.get_torrents():
    if fnmatch(torrent.name, mask):
      return torrent
  
  print('Not found torrent for {}'.format(mask))
  exit(1)


def rename_torrent(client, torrent, toname):
 
  client.rename_torrent_path(torrent.id, torrent.name, toname)
  print('Rename command sent.')
  torrent = client.get_torrent(torrent.id)
  print('Now torrent named {}'.format(torrent.name))
  return torrent.name == toname


def list_torrents(client, mask=None):
  for torrent in client.get_torrents():
    if mask is not None and not fnmatch(torrent.name, mask):
      continue
    print('{0:>3}  {1:<50} {2}'.format(torrent.id, torrent.name, torrent.downloadDir))


def move_torrent(client, torrent, path):
  client.move_torrent_data(torrent.id, path)
  print('Move command sent.')
  torrent = client.get_torrent(torrent.id)
  print('Now torrent placed {}'.format(torrent.downloadDir))
  return torrent.downloadDir == path
 

def argparser():
  parser = argparse.ArgumentParser(prog='Toren', description='Transmission torrent renamer.')
  parser.add_argument('filemask', help='Glob mask defines torrent to rename.', nargs='?', default=None)
  parser.add_argument('newname', help='New name for torrent.', nargs='?', default=None)
  parser.add_argument('-m', '--move', help='Move torrent data to specified path.')
  parser.add_argument('-u', '--url', help='Where to find transmission instance, ex user:password@host:port.')
  parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(__version__))

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

  torrent = None
  if args.move:
    torrent = find_torrent(client, args.filemask)
    move_torrent(client, torrent, args.move)

  if not args.newname:
    if not args.move:
      list_torrents(client, args.filemask)

  else:
    if torrent is None:
      torrent = find_torrent(client, args.filemask)
    if rename_torrent(client, torrent, args.newname):
      print('Ok.')
    else:
      print('Failed.')
