#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

import os
import collections
import logging

from os.path import join, isfile
from fnmatch import fnmatch
from xml.etree.ElementTree import Element, tostring, parse

from mutagen.easyid3 import EasyID3

log = logging.getLogger('syncfm.collection')


def alignment(si, sj, g=lambda k: (k-1)+0.5, d=lambda a, b: 0 if a==b else 1):
    """a needleman-wunsch implementation providing global alignments. Per
    default each gap costs 0.5, mismatch 1 and match 0. Minimum is the best
    score in matrix[m][n]. Unfortunately O(n*m)"""
    # TODO: gotoh-like affine gap cost g(k) = {start: 1, ext: sqrt(k)}
    
    m = len(si)
    n = len(sj)
    matrix = [[0 for y in range(n)] for x in range(m)]
    
    # init
    matrix[0][0] = 0
    for i in range(1, m):
        matrix[i][0] = g(i)
    for j in range(1, n):
        matrix[0][j] = g(j)
    
    # rekurrenz
    for i in range(1, m):
        for j in range(1, n):
            
            matrix[i][j] = min(
                matrix[i-1][j-1] + d(si[i], sj[j]),
                matrix[i-1][j] + g(1),
                matrix[i][j-1] + g(1))
    
    return matrix[m-1][n-1]


class MetadataException(Exception):
    pass


class File:
    '''Audio File class, containing all relevant information for later
    playlist generation.'''
    
    def __init__(self, path):
        
        self.path = path
        self.count = 0
        self.weight = 0.0
        
        f = EasyID3(path)
        self.album = f.get('album', [None])[0]
        self.title = f.get('title', [None])[0]
        self.artist = f.get('artist', [None])[0]
        
        if not self.artist or not self.title:
            raise MetadataException('artist and title are required tags')
        
        # last.fm does not track file's album, thus I give them
        # a lower score, (only when duplicate occur)
        if self.album and filter(lambda p: self.album.lower().find(p) > -1,
                                    ['live', 'instrumental']):
            self.weight += 0.5
    
    def __repr__(self):
        return '\n'.join(["<Music File '%s'>" % self.path,
                          "\t artist: %s" % self.artist,
                          "\t album: %s" % self.album,
                          "\t title: %s" % self.title,
                          "\t count: %s" % self.count])


class XMLTrack(File):
    '''XMLTrack interpretation of File'''
    
    def __init__(self, path, count, weight, artist, album, title):
        
        self.path = path
        self.count = count
        self.weight = weight
        self.album = album
        self.artist = artist
        self.title = title


class SearchResult:
    """SearchResults contains a list of possible matches and will also
    apply weighting from local tracks."""
    
    def __init__(self, *args):
        
        self.res = sorted([(m+f.weight, f) for m, f in args])
        
    def __iter__(self):
        for m, f in self.res:
            yield (m, f)
    
    def __getitem__(self, index):
        return self.res[index]
        
    def __repr__(self):
        return repr(self.res)
        
    def __nonzero__(self):
        return True if self.res else False


class TrackList(list):
    """Tracklist extends the builtin list to make `__contain__`
    case-insensitive and enable a search using needleman-wunsch algorithm."""
    
    def __contains__(self, title):
        return filter(lambda t: t.title.lower() == title.lower(), self)
    
    def __getitem__(self, title):
        for item in self:
            if item.title.lower() == title.lower():
                return item
        else:
            raise KeyError(title)
    
    def search(self, key, results=3):
        
        def w(a, b):
            """match identical characters: -0.1 (alphanummeric) else 0.0
               match ignored case characters: 0 if alphanummeric else 0.1
               mismatch: alphanummeric 1
               mismatch: non-alphanummeric: 0.7"""
            
            if a == b:
                return -0.1 if a.isalnum() else 0
            elif a.lower() == b.lower():
                return 0 if a.isalnum() else 0.1
            else:
                if a.isalnum() and b.isalnum():
                    return 1
                else:
                    return 0.7
        
        # this is *really* slow, but most accurate
        return SearchResult(*sorted([(alignment(key.title, f.title, d=w), f)
                                for f in self])[:results])


class Library:
    """Library is the interface to your locally stored audio files.  It must
    be invoked with a valid directory containing your music."""
    
    def __init__(self, path):
        '''initialize path and default values.'''
        
        self.db = collections.defaultdict(TrackList)
        self.path = path
        
    def index(self, ext=['*.mp3']):
        """index the given directory and store it as easy accessible dict.
        Use ext=[ext1, ext2] to include extensions used in fnmatch filtering.
        """
    
        filelist = []
        # whitelisting using ext=[...], skip failed tracks
        for root, dirs, files in os.walk(self.path, followlinks=True):
            for file in files:
                j = join(root, file)
                if filter(lambda p: fnmatch(j, p), ext) and isfile(j):
                    filelist.append(j)
    
        for i, f in enumerate(filelist):
            if i > 0 and (i+1) % 1000 == 0:
                log.info('- %.2f %% done [%s]', ((i+1.0)/len(filelist)*100), self.path)
            try:
                audio = File(f)
            except MetadataException:
                log.error("unable to load '%s'. artist and/or title is missing" % f)
                continue
    
            self.db[audio.artist].append(audio)
        
        return self
        
    def toxml(self):
        """dict -> xml"""
        
        root = Element('library', root=self.path)#, lastfm=options.history)
        for artist in self:
            atree = Element('artist', artist=artist)
            for track in self[artist]:
                t = Element('track', title=track.title, count=str(track.count),
                    album=track.album, path=track.path, weight=str(track.weight))
                atree.append(t)
            root.append(atree)
            
        return tostring(root, encoding="utf-8")
            
    def load(self):
        """build from xml"""
        if not isfile(self.path):
            log.fatal("'%s' is not a valid file", self.path)
            sys.exit(1)
            
        tree = parse(self.path)
        for artist in tree.iter('artist'):
            tl = TrackList()
            for track in artist.iter('track'):
                tl.append(
                    XMLTrack(
                        track.attrib['path'],
                        int(track.attrib['count']),
                        float(track.attrib['weight']),
                        unicode(artist.attrib['artist']),
                        unicode(track.attrib['album']),
                        unicode(track.attrib['title']))
                    )
            self.db[artist.attrib['artist']] = tl
        
        return self
    
    def __getitem__(self, key):
        for k in self:
            if k == key or k.lower() == key.lower():
                return self.db[k]
        else:
            raise KeyError(key)
        
    def __contains__(self, key):
        return filter(lambda t: t.lower() == key.lower(), self.db)
    
    def __iter__(self):
        return self.db.__iter__()
        

class UserDict(dict):
    """A wrapper class to have a nicer dict handling when
    using inherited class"""
    
    def __init__(self, name=None):
        super(UserDict, self).__init__()
        self.name = name
    
    def __repr__(self):
        return "<%s '%s', %s>" % (self.__class__.__name__,
                                      self.name, self.count)
    
    def __iter__(self):
        for key in self.keys():
            yield self[key]


class Artist(UserDict):
    
    def __init__(self, name, count):
        self.name = name
        self.count = count


class Track(Artist):

    def __init__(self, name, count):
        self.title = name
        self.name = name # used for __repr__
        self.count = count



class LastfmHistory(UserDict):
    """LastfmHistory provides a basic interface to your scrobbling history.
    It allocates each "artist -> title" in filename (generated by scrape.py)
    and builds a nested dict-like data structure."""
    
    count = 0
    
    def __init__(self, fhistory, *args, **kwargs):
        
        super(LastfmHistory, self).__init__(*args, **kwargs)
    
        for line in open(fhistory):
            x, y, z = line.split('\t')
            timestamp, artist, track = float(x), unicode(y), unicode(z.strip())
        
            self.count += 1    
            if artist in self:
                self[artist].count += 1
                if track in self[artist]:
                    self[artist][track].count += 1
                else:
                    self[artist][track] = Track(track, 1)
            else:
                self[artist] = Artist(artist, 1)


if __name__ == '__main__':
    
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    lib = Library('../../music')
