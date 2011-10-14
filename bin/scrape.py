#!/usr/bin/env python
#-*- coding: utf-8 -*-
# 
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses
#
# -- scrape.py: a better last.fm scraper (API is not working...) and it's MULTITHREADED!1

import sys, re, random
reload(sys); sys.setdefaultencoding('utf-8')

from urllib import urlopen, quote
from time import strftime, strptime, mktime, localtime
from htmlentitydefs import name2codepoint

from threading import Thread
from Queue import Queue

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: func(*args, **kargs)
            except Exception, e: print e
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

def entity2unicode(s):
    """converts html entity to unicode char"""
    
    return re.sub('&([^;]+);', lambda m: unichr(name2codepoint[m.group(1)]), s)

def page(n, result):
    """open n-th track page and add tuple to result"""
    
    global API
    site = urlopen(API % n).read()
    
    timestamps = [ mktime(strptime(t, '%Y-%m-%dT%H:%M:%SZ'))
                        for t in re.findall('<abbr title="([^"]+)"', site) ]
    artists = [entity2unicode(artist) for artist in 
                re.findall('<a href="/music/[^/]*">([^<]+)</a>', site)[:-1]]
    tracks = [entity2unicode(track) for track in
                re.findall('<a href="/music/[^/]+/[^"]+">([^<]+)</a>', site)]
    
    for tuple in zip(timestamps, artists, tracks):
        result.append(tuple)
    print >> sys.stderr, ' --', n


if __name__ == '__main__':
    
    from optparse import OptionParser
    parser = OptionParser(usage="usage: python %prog [options] USERNAME")
    
    parser.add_option("-u", dest="update", metavar="FILE", default=None,
                      help="update FILE")
    parser.add_option("-j", dest="jobs", action="store", type="int",
                      help="concurrent jobs [default: %default]", default=4)
    
    (options, args) = parser.parse_args()
    if len(args) == 1:
        
        API = "http://www.lastfm.de/user/"+ quote(args[0]) +"/tracks?page=%s"
        try:
            end = int( re.search('<a .*class="lastpage"[^>]*>(\d+)</a>',
                                     urlopen(API % 1).read()).groups(0)[0] )
        except AttributeError:
            print >> sys.stderr, '%s not found ...exiting' % args[0]
            sys.exit(1)
            
        if options.update:
            # figures out, how many pages you really need (approx.)
            end = int((end*50-len(open(options.update).readlines()))/50.)
            print >> sys.stderr, " -- %s %s left" % (end, 'pages' if end > 1 else 'page')
            
        # pool implementation stolen from http://code.activestate.com/recipes/577187-python-thread-pool/
        pool = ThreadPool(options.jobs)
        result = []
        splitup = [range(1, end+1)[x::options.jobs] for x in range(options.jobs)]
        if options.jobs == 1: splitup = [[x, ] for x in range(1, end+1)]
        
        for jobs in map(None, *splitup):
            for job in [j for j in jobs if j != None]:
                pool.add_task(page, *[job, result])
        try:
            pool.wait_completion()
        except KeyboardInterrupt: # I believe, this will not work properly, but it's a try
            sys.exit(1)
        
        result = sorted(result, key=lambda k: k[0])
        if options.update:
            # appending from latest timestamp. Requires a _sorted_ file
            latest = 0
            for line in open(options.update):
                latest = max(float(line.split('\t', 1)[0]), latest)
            
            f = open(options.update, 'a')
            for timestamp, artist, title in result:
                if float(timestamp) > latest:
                    f.write('\t'.join((str(timestamp), artist, title)) + '\n')
            f.close()
        else:
            for timestamp, artist, title in result:
                print '\t'.join((str(timestamp), artist, title))
    else:
        parser.print_usage()
