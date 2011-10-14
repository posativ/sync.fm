# lastsync

lastsync uses your last.fm history to generate playlists based on different
keys like a song, tags or artist. It offers also some useful tools when
interacting with last.fm's API and webservices.

## tools/scrape.py

    # downloading whole history using ten simultaneous connections (weee!)
    python scrape.py -j 10 john > john.txt
    
    # updating file
    python scrape.py john -u john.txt
    
scrape.py is a multi-threaded tool to get your (almost) complete last.fm
scrobbling history. It does not depend on last.fm's REST API, because it
<del>sucks</del> will not give you your complete history (due some database
changes, don't know or whatever) except some scrobbles at really early time (
early 2008) when you could import your existing iTunes scrobbles.

It creates a flat textfile with timestamp, artist and title separated by
tab, to simplify shell processing (e.g. `wc -l`).