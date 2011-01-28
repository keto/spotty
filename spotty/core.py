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
#
#     Code is for some part based on spotify-notify
#     by SveinT (sveint@gmail.com)
#     http://code.google.com/p/spotify-notify/

"""Various Spotify controller related classes."""

import dbus, gobject, os, signal, logging
from optparse import OptionParser
from dbus.mainloop.glib import DBusGMainLoop

from spotty import LOG
from spotty.fetchart import SpotifyCoverFetcher
from spotty.notify import get_notificator


# Set to False to disable notifications
NOTIFY = True
# Set to false to disable cover fetching
COVER = True
# Indicator applet support (Not needed
INDICATE = False

# Mappings for xesam keys and simpler ones used internally
META_MAP = {"album": "xesam:album",
            "artist": "xesam:artist",
            "title": "xesam:title",
            "track": "xesam:trackNumber",
            "date": "xesam:contentCreated",
            "url": "xesam:url"}

# TODO: Commandline parameters to disable different "plugins"


class Signal(object):
    """Simple signal class used to send signal between plugins."""

    class Listener(object):
        """Signal listener."""
        def __init__(self, callback, priority, ignore_errors):
            if not callable(callback):
                raise TypeError("callback has to be callable")
            if not isinstance(priority, int):
                raise TypeError("priority has to be integer")
            self._id = id(callback)
            self.calback = callback
            self.priority = priority
            self.ignore_errors = ignore_errors

        def __cmp__(self, obj):
            if not isinstance(obj, Listener):
                raise TypeError("can't compare %s to %s" %
                        (type(self), type(obj)))
            return cmp(self.priority, obj.priority)

    def __init__(self, arguments):
        """Constructor.
        :param arguments: list of argument names accepted by signal
        """
        self._args = arguments
        self.listeners = []

    def connect(self, callback, priority=99, ignore_errors=True):
        """Connect listener to signal.
        :param listener: callable which should accept any keyword arguments
        :param priority: listeners will be called in priority order
            default is 99
        :param ignore_errors: if True, exceptions from listener will be ignored
        """
        # TODO: prevent duplicate listeners
        self.listeners.append(Listener(callback, priority, ignore_errors))
        self.listeners.sort()

    def disconnect(self, callback):
        cb_id = id(callback)
        for index, listener in enumerate(self.listeners):
            if listener.id == cb_id:
                self.listeners.pop(index)


    def send(self, **kwargs):
        """Dispatch signal
        Takes list of keyword arguments to pass to listener
        raises TypeError if bad argumen names provided
        """
        original_args = dict(kwargs)
        # TODO check promised args
        for listener in self.listeners:
            try:
                new = listener.callback(original_args, **kwargs)
                kwargs.update(new)
            except Exception, exobj:
                if listener.ignore_errors:
                    LOG.error("Signal %s callback %s failed: %s" %
                            (self, listener, exobj))
                else:
                    raise


class SpotifyControl():
    """Class for controlling spotify through DBus."""

    def __init__(self, cover_fetcher=None):
        """Constructor."""
        self.bus = dbus.SessionBus()
        # Register listener for spotify start up
        proxy = self.bus.get_object("org.freedesktop.DBus",
                "/org/freedesktop/DBus")
        proxy.connect_to_signal("NameOwnerChanged",
                self.cb_spotify_spy)
        self._fetcher = cover_fetcher
        self.spotifyservice = None
        self.connected = False
        self.connect()
        self.track_change_listeners = []
        self.state_change_listeners = []
        self._current_track = None

    def cb_spotify_spy(self, *args):
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
            for callback in self.state_change_listeners:
                callback(True)
        elif old and not new:
            LOG.debug("Spotify went away")
            self.spotifyservice = None
            self.connected = False
            for callback in self.state_change_listeners:
                callback(False)
        else:
            LOG.debug("Spotify dbus interface did something weird")

    def connect(self):
        """Connect to spotify dbus interface."""
        LOG.debug("Connecting")
        try:
            self.spotifyservice = self.bus.get_object(
                    "com.spotify.qt", "/org/mpris/MediaPlayer2")
            self.spotifyservice.connect_to_signal(
                    "PropertiesChanged", self.cb_track_changed)
            self.connected = True
        except Exception, exobj:
            LOG.error("Connection to Spotify failed: %s" % exobj)
        return self.connected

    def cb_track_changed(self, *args):
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
        if self._fetcher:
            try:
                clear_data["cover"] = self._fetcher.fetch(clear_data["artist"],
                        clear_data["album"], track_id=clear_data["url"])
            except Exception, exobj:
                LOG.error("Fetching cover image failed: %s" % exobj)
        LOG.debug(str(clear_data))
        self._current_track = clear_data
        for listener in self.track_change_listeners:
            listener(clear_data)

    def add_change_listener(self, callback):
        """Add listener for track changes"""
        self.track_change_listeners.append(callback)

    def add_spotify_state_listener(self, callback):
        self.state_change_listeners.append(callback)

    def cb_key_handler(self, key):
        """Media key handler callback."""
        if not self.connected:
            LOG.debug("Not connected")
            return
        if key not in MediaKeyListener.KEYS:
            return
        if key == "Play":
            key = "PlayPause"
        self.spotifyservice.get_dbus_method(key,
                "org.mpris.MediaPlayer2.Player")()

class MediaKeyListener():
    """Class for listening media key events."""

    KEYS = ["Play", "Pause", "Stop", "Next", "Previous"]

    def __init__(self):
        self.handlers = []
        self.bus = dbus.SessionBus()
        self.bus_object = self.bus.get_object(
                "org.gnome.SettingsDaemon",
                "/org/gnome/SettingsDaemon/MediaKeys")
        self.bus_object.GrabMediaPlayerKeys(
                "Spotify", 0,
                dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        self.bus_object.connect_to_signal(
                "MediaPlayerKeyPressed", self.cb_handle_mediakey)

    def add_handler(self, handler):
        """Register media key handler function."""
        self.handlers.append(handler)

    def cb_handle_mediakey(self, *mmkeys):
        """Media key event callback."""
        LOG.debug("Got keys %s" % str(mmkeys))
        for key in mmkeys:
            if key not in self.KEYS:
                continue
            for handler in self.handlers:
                try:
                    handler(key)
                except Exception, exobj:
                    LOG.error("Key handler %s failed: %s" % (handler, exobj))

class SpottyPlugin(object):
    """Spotty plugin base class."""
    # Plugins are singletons
    __instance = None
    #: Used to specify other required plugins
    requires = []

    @classmethod
    def load(cls, controller):
        """Plugin loader.
        :param controller: The SpotifyControl instance
        :returns: Plugin instance
        """
        if cls == SpottyPlugin:
            raise RuntimeError("Tried to load plain base plugin")
        if not cls.is_loaded():
            cls.__instance = cls(controller)
        return cls.__instance

    @classmethod
    def is_loaded(cls):
        return cls.__instance is not None

    def __init__(self, controller):
        """Constructor."""
        pass

    def unload(self):
        """Plugin unloader."""
        pass


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
    fetcher = None
    if COVER:
        fetcher = SpotifyCoverFetcher(
                os.path.join(os.environ.get("HOME", "/tmp"),
                        ".spotcovers"))
    spotify = SpotifyControl(cover_fetcher=fetcher)
    try:
        key_listener = MediaKeyListener()
        key_listener.add_handler(spotify.cb_key_handler)
    except Exception, exobj:
        LOG.error("MediaKeyListener failed: %s" % exobj)

    if NOTIFY:
        notifier = get_notificator()
        spotify.add_change_listener(notifier.cb_track_changed)

    if INDICATE:
        indicator = IndicatorHandler()
        indicator.cb_status_changed(spotify.connected)
        spotify.add_spotify_state_listener(indicator.cb_status_changed)

    loop = gobject.MainLoop()
    signal.signal(signal.SIGINT, lambda *args: loop.quit())
    loop.run()

if __name__ == "__main__":
    main()
