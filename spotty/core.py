#!/usr/bin/python -tt
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
#
#     Code is for some part based on spotify-notify
#     by SveinT (sveint@gmail.com)
#     http://code.google.com/p/spotify-notify/
#

"""Various Spotify controller related classes."""

import dbus, gobject, signal, logging, traceback, sys
from optparse import OptionParser
from dbus.mainloop.glib import DBusGMainLoop

import pkg_resources

from spotty import LOG

# Mappings for xesam keys and simpler ones used internally
META_MAP = {"album": "xesam:album",
            "artist": "xesam:artist",
            "title": "xesam:title",
            "track": "xesam:trackNumber",
            "date": "xesam:contentCreated",
            "url": "xesam:url",
            "art_url": "mpris:artUrl"}

# TODO: Commandline parameters to disable different "plugins"

class Listener(object):
    """Wrapper class for signal listener callbacks."""
    def __init__(self, callback, priority, ignore_errors):
        if not callable(callback):
            raise TypeError("callback has to be callable")
        if not isinstance(priority, int):
            raise TypeError("priority has to be integer")
        self._callback = callback
        self._priority = priority
        self._ignore_errors = ignore_errors

    def __call__(self, *args, **kwargs):
        try:
            return self._callback(*args, **kwargs)
        except Exception:
            exc = sys.exc_info()[0]
            LOG.error("Listener %s (%s, %s) failed:%s" %
                    (self, args, kwargs, exc))
            if not self._ignore_errors:
                raise

    def __cmp__(self, obj):
        if not isinstance(obj, Listener):
            raise TypeError("can't compare %s to %s" %
                    (type(self), type(obj)))
        return cmp(self._priority, obj._priority)

    def __str__(self):
        return str(self._callback)

class Signal(object):
    """Simple signal class used to send signal between plugins."""
    def __init__(self):
        """Constructor."""
        self.listeners = []

    def connect(self, callback, priority=99, ignore_errors=True):
        """Connect listener to signal.
        :param listener: callable which should accept any keyword arguments
        :param priority: listeners will be called in priority order
            default is 99
        :param ignore_errors: if True, exceptions from listener will be ignored
        """
        listener = Listener(callback, priority, ignore_errors)
        self.listeners.append(listener)
        # Keep in priority order
        self.listeners.sort()

    def disconnect(self, callback):
        """Disconnect listener from this signal.
        :param callback: The earlier connected callback
        """
        cb_id = str(callback)
        for index, listener in enumerate(self.listeners):
            if str(listener) == cb_id:
                self.listeners.pop(index)

    def send(self, *args, **kwargs):
        """Dispatch signal."""
        for listener in self.listeners:
            new_args = listener(*args, **kwargs)
            if isinstance(new_args, dict):
                kwargs.update(new_args)

class SpotifyControl(object):
    """Class for controlling spotify through DBus."""

    def __init__(self):
        """Constructor."""
        self.bus = dbus.SessionBus()
        self.spotifyservice = None
        self.connected = False
        self.track_changed = Signal()
        self.state_changed = Signal()
        self._current_track = None
        # Register listener for spotify start up
        proxy = self.bus.get_object("org.freedesktop.DBus",
                "/org/freedesktop/DBus")
        proxy.connect_to_signal("NameOwnerChanged",
                self._cb_spotify_spy)

    def _cb_spotify_spy(self, *args):
        """DBus listener for spying spotify start/quit."""
        try:
            name, old, new = args
        except (ValueError, TypeError):
            LOG.error("Bad values: %s" % args)
        if name != "com.spotify.qt":
            return
        if not old and new:
            LOG.debug("Spotify appeared!")
            self.connect()
        elif old and not new:
            LOG.debug("Spotify went away")
            self.spotifyservice = None
            self.connected = False
            self.state_changed.send(False)
        else:
            LOG.debug("Spotify dbus interface did something weird")

    def connect(self):
        """Connect to spotify dbus interface."""
        LOG.debug("Connecting")
        try:
            self.spotifyservice = self.bus.get_object(
                    "com.spotify.qt", "/org/mpris/MediaPlayer2")
            self.spotifyservice.connect_to_signal(
                    "PropertiesChanged", self._cb_track_changed)
            self.connected = True
            self.state_changed.send(True)
        except Exception:
            exc = sys.exc_info()[1]
            LOG.error("Connection to Spotify failed: %s" % exc)
        return self.connected

    def _cb_track_changed(self, *args):
        """Metadata change listener."""
        clear_data = {}
        try:
            data = args[1]["Metadata"]
        except (IndexError, KeyError):
            return
        if not data:
            return
        for key, name in META_MAP.items():
            clear_data[key] = data.get(name, None)
        # Parse year
        if clear_data["date"]:
            clear_data["year"] = clear_data["date"].split("-")[0]
        else:
            clear_data["year"] = None
        if isinstance(clear_data["artist"], dbus.Array):
            clear_data["artist"] = " - ".join(clear_data["artist"])
        # TODO: Convert all the dbus data types
        LOG.debug(str(clear_data))
        self._current_track = clear_data
        self.track_changed.send(**clear_data)

    def _call_spotify(self, method):
        """Helper to call spotify method."""
        if not self.connected:
            LOG.debug("Not connected")
            return
        self.spotifyservice.get_dbus_method(method,
                "org.mpris.MediaPlayer2.Player")()

    def play_pause(self):
        """Togle play/pause on spotify."""
        self._call_spotify("PlayPause")

    def next(self):
        """Skip to next track."""
        self._call_spotify("Next")

    def previous(self):
        """Skip to previous track."""
        self._call_spotify("Previous")

    def stop(self):
        """Stop spotify."""
        self._call_spotify("Stop")

    def pause(self):
        """Pause spotify."""
        self._call_spotify("Pause")

def parse_args():
    """Parses commandline arguments."""
    parser = OptionParser()
    parser.add_option("-d", "--debug", action="store_true",
            help="Enable debug output")
    return parser.parse_args()

def main():
    """Entry point"""
    # TODO configuration file handling and commandline options
    options, _ = parse_args()
    if options.debug:
        LOG.setLevel(logging.DEBUG)
    DBusGMainLoop(set_as_default=True)
    spotify = SpotifyControl()
    # Load plugins
    enabled = ["GnomeMediaKeys", "Notify", "CoverFetcher"]
    plugins = {}
    LOG.debug("Loading plugins...")
    for entry in pkg_resources.iter_entry_points("spotty.plugin"):
        plugin = entry.load()
        if plugin.__name__ not in enabled:
            LOG.debug("%s not enabled, skipping...", plugin.__name__)
            continue
        LOG.debug("Loading plugin %s", plugin.__name__)
        try:
            plugins[plugin.__name__] = plugin.load(spotify)
        except Exception:
            LOG.error("Failed to load %s", plugin.__name__)
            traceback.print_exc()
    
    # Start the mainloop
    spotify.connect()
    loop = gobject.MainLoop()
    signal.signal(signal.SIGINT, lambda *args: loop.quit())
    loop.run()
    # Unload plugins
    for name, plugin in plugins.iteritems():
        LOG.debug("Unloading %s", name)
        try:
            plugin.unload()
        except Exception:
            LOG.error("Failed to unload %s", name)
            traceback.print_exc()

if __name__ == "__main__":
    main()
