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
import os
import sys

from spotty import LOG

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

    def _check_cache(self, file_id):
        """Get image from cache if exists."""
        cover_file = "/tmp/spotty-cover.png"
        exists = False
        if self._cache:
            cover_file = os.path.join(self._cache, file_id)
            if os.path.isfile(cover_file):
                exists = True
        return cover_file, exists

    def fetch(self, url):
        """Fetch cover image based on URL."""
        _, file_name = os.path.split(url)
        cover_file, exists = self._check_cache(file_name)
        if not exists:
            LOG.debug("Downloading %s", url)
            try:
                open(cover_file, "w").write(urllib2.urlopen(url).read())
            except Exception, exobj:
                raise CoverError("Failed to download: %s" % exobj)
        else:
            LOG.debug("Cover in cache")
        return cover_file

if __name__ == "__main__":
    print(SpotifyCoverFetcher().fetch(sys.argv[1]))
