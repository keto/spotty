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
#

# TODO Rewrite this with synchronous getting of track info
"""Spotty commandline interface."""

import sys, gobject, logging, threading
from optparse import OptionParser
from spotty import LOG
from spotty.core import SpotifyControl
from dbus.mainloop.glib import DBusGMainLoop

def parse_opts():
    """Parses commandline arguments."""
    parser = OptionParser()
    parser.add_option("-n", "--next", action="store_const", dest="command",
             const="next")
    parser.add_option("-p", "--previous", action="store_const", dest="command",
             const="previous")
    parser.add_option("-P", "--play", action="store_const", dest="command",
             const="play_pause")
    parser.add_option("-q", "--quiet", action="store_true",
            help="Don't print track info")
    parser.add_option("-d", "--debug", action="store_true",
            help="Enable debug output")
    return parser.parse_args()

class SpottyCLI(threading.Thread):
    """Commandline Spottty operator."""
    def __init__(self, quiet=False):
        super(SpottyCLI, self).__init__()
        self._loop = gobject.MainLoop()
        self._spot = SpotifyControl()
        self._spot.track_changed.connect(self.cb_track_changed)
        self._quiet = quiet
        self._spot.connect()

    def run(self):
        LOG.debug("Starting mainloop")
        self._loop.run()
        LOG.debug("Mainloop ended")

    def terminate(self):
        """Terminates the mainloop."""
        if self._loop.is_running():
            LOG.debug("Terminating mainloop")
            self._loop.quit()

    def send_command(self, command):
        """Send given command to Spotify."""
        LOG.debug("Sending command")
        if self._spot.connected:
            getattr(self._spot, command)()
            LOG.debug("Command sent")
        else:
            LOG.error("Failed to connect spotify")

    def cb_track_changed(self, **info):
        """Spotty track_changed handler."""
        LOG.debug("Track changed")
        if not self._quiet:
            artist = info.get("artist", u"")
            title = info.get("title", u"")
            print("%s - %s" % (artist, title))
        self.terminate()

def main():
    """Commandline entry point."""
    DBusGMainLoop(set_as_default=True)
    options, _ = parse_opts()
    if options.debug:
        LOG.setLevel(logging.DEBUG)
    if not options.command:
        return

    gobject.threads_init()
    cli = SpottyCLI(options.quiet)
    cli.start()
    cli.send_command(options.command)
    if options.command not in ["Previous"]:
        cli.join(2)
    cli.terminate()
    return 0

if __name__ == "__main__":
    sys.exit(main())
