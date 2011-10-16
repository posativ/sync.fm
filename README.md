# sync.fm

sync.fm is a library and toolchain to use your last.fm history to generate
playlists and fill your mp3 player with a given amount of tracks. It offers
also some useful tools when interacting with last.fm's API and webservices.

## bin/sync.fm

The workflow is now as follows:
    
    %> sync.fm init posativ
    %> sync.fm add ~/Music
    %> scrape.py -j 10 posativ > ~/.sync-fm/lastfm.history
    %> sync.fm update
    %> sync.fm sync /media/device/music/

## bin/scrape.py

    # downloading whole history using ten simultaneous connections (weee!)
    python bin/scrape.py -j 10 john > john.txt
    
    # updating file
    python bin/scrape.py john -u john.txt
    
**NOTE**: you have to turn off "hide realtime stats" in profile settings.
    
scrape.py is a multi-threaded python script to get your (almost) complete
last.fm scrobbling history. It does not depend on last.fm's REST API, because
it <del>sucks</del> will not give you your complete history (due some database
changes, don't know or whatever) except some scrobbles at really early time (
early 2008) when you could import your existing iTunes scrobbles.

It produces a long list of timestamp, artist and title separated by
tab to simplify shell processing (e.g. `wc -l`).
