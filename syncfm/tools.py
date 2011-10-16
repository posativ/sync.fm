#-*- coding: utf-8 -*-
# 
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

from os.path import join
import re

import logging
log = logging.getLogger('syncfm.tools')

class ColorFormatter(logging.Formatter):
    """Implements basic colored output using ANSI escape codes."""
    
    BLACK = '\033[0;30m%s\033[0m'
    RED = '\033[0;31m%s\033[0m'
    GREY = '\033[0;37m%s\033[0m'
    RED_UNDERLINE = '\033[4;31m%s\033[0m'
    
    def __init__(self, fmt='[%(levelname)s] %(name)s: %(message)s'):
        logging.Formatter.__init__(self, fmt)
        
    def format(self, record):
        if record.levelname == 'DEBUG':
            record.levelname = self.BLACK % record.levelname
        elif record.levelname == 'INFO':
            record.levelname = self.GREY % record.levelname
        elif record.levelname in ('WARN', 'WARNING'):
            record.levelname = self.RED % record.levelname
        elif record.levelname in ('ERROR', 'CRITICAL', 'FATAL'):
            record.levelname = self.RED_UNDERLINE % record.levelname
        return logging.Formatter.format(self, record)


def lastfm2local(lastfm, lib, lookup={}):
    
    c, d = 0, 0
    new = {}
    
    for artist in lastfm:
        if not artist.name in lib:
            continue
        
        for track in artist:
            c += track.count
            if track.title in lib[artist.name]:
                d += track.count
                lib[artist.name][track.title].count += track.count
            elif join(artist.name, track.title) in lookup:
                d += track.count
                a, t = lookup[join(artist.name, track.title)].split('/')
                lib[a][t].count += track.count
                new[join(artist.name, track.name)] = lookup[join(artist.name, track.name)]
            else:
                if track.count < 10:
                    continue
                result = lib[artist.name].search(track)
                if not result:
                    continue
                score, t = result[0]
                if score < 2.0:
                    lib[artist.name][t.title].count += track.count
                    d += track.count
                    log.debug("match: {0} '[{1}] {2}' => '{3}' from '{4}'".format(
                        str(score).rjust(4), str(track.count).rjust(3),
                        track.name, t.title, t.album))
                    new[join(artist.name, track.name)] = join(t.artist, t.title)
                else:
                    choices = [("%s: '%s'" % (m, t.title)) for m, t in result]
                    msg = "mismatch for [%s scrobbles] '%s' by '%s'" % \
                                (track.count, track.title, artist.name)
                    log.warn(msg + '\n\t' + '\n\t'.join(choices))
    
    return lib, new


def fat32(fname):
        
    return re.sub('[/?\\:]+', '', fname)
