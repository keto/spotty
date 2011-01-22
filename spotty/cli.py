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

"""Spotty commandline interface."""

import sys, gobject
from optparse import OptionParser
from spotty.core import SpotifyControl
from dbus.mainloop.glib import DBusGMainLoop

def parse_opts():
    """Parses commandline arguments."""
    parser = OptionParser()
    parser.add_option("-n", "--next", action="store_const", dest="command",
             const="Next")
    parser.add_option("-p", "--previous", action="store_const", dest="command",
             const="Previous")
    parser.add_option("-P", "--paly", action="store_const", dest="command",
             const="Play")
    return parser.parse_args()

def execute(spotify, command):
    spotify.cb_key_handler(command)
    sys.exit()


def main():
    """Commandline entry point."""
    DBusGMainLoop(set_as_default=True)
    options, args = parse_opts()
    if not options.command:
        return
    spot = SpotifyControl()
    loop = gobject.MainLoop()
    gobject.timeout_add(500, execute, spot, options.command)
    loop.run()

if __name__ == "__main__":
    main()
