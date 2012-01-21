#
#    Copyright 2010 - 2012 Pami Ketolainen
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
#

"""Cover art fetching plugin."""

import urllib2, os, traceback

from spotty import LOG
from spotty.plugin import SpottyPlugin

class CoverError(Exception):
    """Cover retrieval error class."""
    pass

class CoverFetcher(SpottyPlugin):
    """Plugin for fetching album cover art."""
    def __init__(self, spotify):
        """Constructor."""
        super(CoverFetcher, self).__init__(spotify)
        if os.environ.has_key("XDG_CACHE_HOME"):
            cache_dir = os.path.join(os.environ["XDG_CACHE_HOME"], "spotty")
        else:
            cache_dir = os.path.join(
                    os.environ.get("HOME", ""), ".cache", "spotty")
        if not os.path.exists(cache_dir):
            try:
                os.mkdir(cache_dir)
            except OSError:
                self._cache = None
        self._cache = cache_dir
        self.spotify.track_changed.connect(self.cb_track_changed, priority=50)

    def unload(self):
        self.spotify.track_changed.disconnect(self.cb_track_changed)

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
            except Exception:
                LOG.error("Failed to download: %s", url)
                traceback.print_exc()
        else:
            LOG.debug("Cover in cache")
        return cover_file

    def cb_track_changed(self, *_, **info):
        """Track change callback listener."""
        if info.has_key("art_url"):
            LOG.debug("fetching art url %s" % info["art_url"])
            return {"cover": self.fetch(info["art_url"])}
