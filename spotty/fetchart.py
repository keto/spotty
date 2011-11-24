#!/usr/bin/python -tt
#
#    Copyright 2010 Pami Ketolainen
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Spotify album cover art fetching utility."""

import urllib2
import simplejson
import os
import re
import sys

from spotty import LOG

# META_API_URL + 'spotify:track:TRACKIDHASH'
META_API_URL = "http://ws.spotify.com/lookup/1/.json?uri="
# OPEN_URL + 'ALBUMIDHASH'
OPEN_URL = "http://open.spotify.com/album/"

class CoverError(Exception):
    """Cover retrieval error class."""
    pass

class SpotifyCoverFetcher(object):
    """Spotify album art fetcher."""
    def __init__(self, cache_dir=None):
        """Constructor.
        :param string cache_dir: Directory to use as cache for album covers
        """
        if cache_dir and not os.path.exists(cache_dir):
            try:
                os.mkdir(cache_dir)
            except OSError:
                self._cache = None
        self._cache = cache_dir
        self._image_pat = re.compile(
                "<img\s*id=\"cover-art\"\s*src=\"(.*)\".*>")

    def _check_cache(self, album_id):
        """Get image from cache if exists."""
        # TODO: investigate if it would be possible to use spotify cache
        if self._cache is None:
            return None
        cover_file = os.path.join(self._cache, album_id)
        if os.path.isfile(cover_file):
            return cover_file
        return None

    def _fetch_image(self, album_id):
        """Download image from open.spotify.com"""
        if self._cache:
            cover_file = os.path.join(self._cache, album_id)
        else:
            cover_file = "/tmp/spot-cover.png"
        # Get the open.spotify.com album page and parse cover image from it
        try:
            LOG.debug("fetching %s%s" % (OPEN_URL, album_id))
            url = urllib2.urlopen(OPEN_URL + album_id)
            webpage = url.read()
        except Exception, exobj:
            raise CoverError("Fetching data from open.spotify.com failed: %s" %
                    exobj)

        matchobject = self._image_pat.search(webpage)
        if matchobject:
            imageurl = matchobject.group(1)
            LOG.debug("fetching %s", imageurl)
            try:
                url = urllib2.urlopen(imageurl)
                open(cover_file, "w").write(url.read())
            except Exception, exobj:
                raise CoverError("Failed to fetch cover image: %s" % exobj)
            return cover_file
        else:
            raise CoverError("Cover img url not found")

    def fetch(self, artist, album, track_id=None):
        """Return cover image file name or raise CoverError."""
        if not track_id:
            LOG.error("Track ID needed")
            # TODO turn artist+album to spotify id
            return None

        # Some validation for the given id
        track_id = track_id.split(":")
        if len(track_id) == 3 and track_id[0] == "spotify" \
                and track_id[1] == "track":
            track_id = ":".join(track_id)
        elif len(track_id) == 1:
            track_id = "spotify:track:" + track_id[0]
        else:
            raise ValueError("Bad spotify track id '%s'. "
                    "Should be either ID or spotify:track:ID" % track_id)
    
        # Fetch track metadata
        try:
            url = urllib2.urlopen(META_API_URL + track_id)
            data = simplejson.loads(url.read())
        except Exception, exobj:
            raise CoverError("Fetching track metadata failed: %s" % exobj)
    
        # Get album id from track data
        try:
            album_id = data["track"]["album"]["href"].split(":")[2]
        except Exception, exobj:
            raise CoverError("Failed to get album uri: %s" % exobj)

        cover_file = self._check_cache(album_id)
        if not cover_file:
            LOG.debug("cover not in cache")
            cover_file = self._fetch_image(album_id)
        return cover_file

if __name__ == "__main__":
    print(SpotifyCoverFetcher().fetch(None, None, sys.argv[1]))
