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

from optparse import OptionParser
from spotty.core import SpotifyControl

def parse_opts():
    """Parses commandline arguments."""
    parser = OptionParser()
    parser.add_option("-n", "--next", action="store_true")
    parser.add_option("-p", "--previous", action="store_true")
    parser.add_option("-P", "--play", action="store_true")
    return parser.parse_args()

def main():
    """Commandline entry point."""
    options, args = parse_opts()
    spot = SpotifyControl()
    if options.play:
        spot.cb_key_handler("Play")
    elif options.next:
        spot.cb_key_handler("Next")
    elif options.previous:
        spot.cb_key_handler("Previous")

if __name__ = "__main__":
    main()
