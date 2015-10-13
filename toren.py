#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2013 Aleksandr Semenov <iamsav@gmail.com>
# Licensed under the MIT license.
#
# Script can list transmission downloads (use: toren [mask])
# And rename one-file torrents (use: toren mask newname)
#
# requires module 'transmissionrpc'

'''Transmission renamer.

Usage:
  toren [options] [(--id=<id> | --last | <oldname>)] [<newname>]
  toren -V | --version

Options:
  -u, --url=<url>    Url of transmission instance in the form user:password@host:port
  -m, --move=<dest>  Dir to move file (may use index from config table)
  -i, --id=<id>      Lookup by transmission id (very fast)
  -l, --last         Use last id
  -V, --version      Prints version info
'''

__author__ = 'Aleksandr Semenov <iamsav@gmail.com>'
__version_major__ = 1
__version_minor__ = 0
__version_3__ = 2
__version__ = '{0}.{1}.{2}'.format(__version_major__, __version_minor__, __version_3__)
__copyright__ = 'Copyright (c) 2013 Aleksandr Semenov <iamsav@gmail.com>'
__license__ = 'MIT'


import sys, os, os.path
import re
from fnmatch import fnmatch
from docopt import docopt

import transmissionrpc

LISTING_FORMAT = '{0.id:>3}  {0.name:<50} {0.downloadDir}'   
MOVE_DIRS = None


def safeprint(*args, **kwargs):
    f = kwargs.get('file', sys.stdout)
    print(*[arg.encode(f.encoding, 'replace').decode(f.encoding) for arg in args], **kwargs)


def load_config():

  cfg = {}

  try:
    exec(open(os.path.expanduser('~/toren.config'), encoding='utf-8').read(), cfg)   # Little bit insecure
  except FileNotFoundError:
    pass

  for var in ('HOST', 'PORT', 'USER', 'PASW'):
    fullvar = 'TRANSMISSION_{0}'.format(var)
    cfg[fullvar] = cfg.get(fullvar)   # Fill defaults with None

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


def find_torrents(client, args):
    if args['--id'] is not None:
        yield client.get_torrent(int(args['--id']))
        return

    print('Loading list...', end='', flush=True)
    torrents = client.get_torrents()
    print('done.')

    if args['--last']:
        yield torrents[-1]
        return

    returned = 0
    for torrent in torrents:
        if args['<oldname>'] is None or fnmatch(torrent.name, args['<oldname>']):
            returned += 1
            yield torrent
    if not returned:
        print('None found by mask {}'.format(args['<oldname>']))


def rename_torrent(client, torrent, toname):

  print('Previous name was "{}".'.format(torrent.name))
  client.rename_torrent_path(torrent.id, torrent.name, toname)
  print('Rename command sent.')
  torrent = client.get_torrent(torrent.id)
  print('Now torrent named {}'.format(torrent.name))
  return torrent.name == toname


def move_torrent(client, torrent, path):
  # Undocumented feature - MOVE_DIRS in config is a tuple of predefined directories
  if path.isdigit() and MOVE_DIRS and len(MOVE_DIRS) > int(path):
    path = MOVE_DIRS[int(path)]
    print('Path expanded to {}'.format(path))

  print('Previous folder was "{}".'.format(torrent.downloadDir))
  client.move_torrent_data(torrent.id, path)
  print('Move command sent.')
  torrent = client.get_torrent(torrent.id)
  print('Now torrent placed {}'.format(torrent.downloadDir))
  print('Ok.' if torrent.downloadDir == path else 'Failed.')
  return torrent.downloadDir == path


def parse_url(url):
  URL_RE = re.compile('((?P<user>[^:]+)(:(?P<pasw>.+))?@)?(?P<host>[^@:]+)(:(?P<port>\\d+))?')
  match = URL_RE.match(url)
  if match is None:
    raise BadUrlSyntax

  gr = match.groupdict()
  # print(gr.get('user'), gr.get('pasw'), gr.get('host'), gr.get('port'))
  return gr.get('user'), gr.get('pasw'), gr.get('host'), gr.get('port')


if __name__ == '__main__':

  cfg = load_config()
  if 'LISTING_FORMAT' in cfg:
    # global LISTING_FORMAT
    # TODO refactor to object wrapped over client which has config
    LISTING_FORMAT = cfg['LISTING_FORMAT']

  if 'MOVE_DIRS' in cfg:
    # global MOVE_DIRS
    # TODO refactor to object wrapped over client which has config
    MOVE_DIRS = cfg['MOVE_DIRS']

  args = docopt(__doc__, version=__version__ + '''
  Shortcut dirs:
{}'''.format('\n'.join('-m{}: {}'.format(i, d) for i, d in enumerate(MOVE_DIRS))))

  if args['--url'] is not None:
    (cfg['TRANSMISSION_USER'],
     cfg['TRANSMISSION_PASW'],
     cfg['TRANSMISSION_HOST'],
     cfg['TRANSMISSION_PORT']) = parse_url(args['--url'])

  #print(args)

  client = make_client(cfg)

  for torrent in find_torrents(client, args):
    if args['--move'] is not None:
      move_torrent(client, torrent, args['--move'])

    if args['<newname>'] is None:
      if args['--move'] is None:
        safeprint(LISTING_FORMAT.format(torrent))
    else:
      if rename_torrent(client, torrent, args['<newname>']):
        print('Ok.')
      else:
        print('Failed.')
