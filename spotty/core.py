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

import dbus, gobject, os, signal
import logging
from dbus.mainloop.glib import DBusGMainLoop
try:
    import indicate
    INDICATE = True
except ImportError:
    INDICATE = False

from pkg_resources import resource_filename

from spotty.fetchart import SpotifyCoverFetcher

# TODO: Propper logging configuration
LOG = logging.getLogger()
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.DEBUG)

DEFAULT_ICON = os.path.abspath(resource_filename(__name__, "icon_spotify.png"))

# Set to False to disable notifications
NOTIFY = True
# Set to false to disable cover fetching
COVER = True

# TODO: Commandline parameters to disable different "services"

class Notifier(object):
    """Class for displaying song info notifications."""
    def __init__(self, cover_fetcher=None):
        """Constructor.
        optional cover fetcher object used to fetch album art.
        """
        self._fetcher = cover_fetcher
        self._notifyservice = None
        self._notifyid = 0

    @property
    def notifyservice(self):
        """Lazy binding to dbus notification interface."""
        if self._notifyservice == None:
            try:
                bus = dbus.SessionBus()
                proxy = bus.get_object(
                        "org.freedesktop.Notifications",
                        "/org/freedesktop/Notifications")
                self._notifyservice = dbus.Interface(proxy,
                        "org.freedesktop.Notifications")
            except Exception, exobj:
                LOG.error("Notification service connectin failed: %s" % exobj)
        return self._notifyservice

    def display_track(self, data):
        """Display notification.
        :param dict data: Dictionary containing song info
        """
        artist = data.get("artist", "Unknown").encode("latin-1")
        album = data.get("album", "Unknown").encode("latin-1")
        title = data.get("title", "Unknown").encode("latin-1")
        url = data.get("url", None)
        year = str(data.get("year", ""))
        
        cover = ""
        if self._fetcher and url:
            try:
                cover = self._fetcher.fetch(artist, album, url)
            except Exception, exobj:
                LOG.error("failed to fetch cover: %s" % exobj)
        cover = cover or DEFAULT_ICON
        self._notifyid = self.notifyservice.Notify(
                "spotty", self._notifyid, cover, artist,
                "%s\n %s (%s)" % (title, album , year), [], {}, 2)


class SpotifyControl():
    """Class for controlling spotify through DBus."""

    def __init__(self):
        """Constructor."""
        self.bus = dbus.SessionBus()
        # Register listener for spotify start up
        proxy = self.bus.get_object("org.freedesktop.DBus",
                "/org/freedesktop/DBus")
        proxy.connect_to_signal("NameOwnerChanged",
                self.cb_spotify_spy)
        self.spotifyservice = None
        self.connected = False
        self.connect()
        self.track_change_listeners = []
        self.state_change_listeners = []

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
        for key in data:
            for k in ["title", "artist", "album", "url"]:
                if k in key:
                    clear_data[k] = data[key]
                    break
        # Special case for year
        clear_data["year"] = data.get("xesam:contentCreated", "").split("-")[0]
        LOG.debug(str(data))
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
        for key in mmkeys:
            if key not in self.KEYS:
                continue
            for handler in self.handlers:
                try:
                    handler(key)
                except Exception, exobj:
                    LOG.error("Key handler %s failed: %s" % (handler, exobj))

class IndicatorHandler(object):
    """Class for handling indicator applet."""

    def __init__(self):
        self._server = indicate.indicate_server_ref_default()
        self._server.set_type("music.spotify")
        self._server.set_desktop_file(
                "/usr/share/applications/spotify.desktop")
        self._visible = False

    def cb_status_changed(self, running):
        if self._visible == running:
            return
        if running:
            self._server.show()
            self._visible = True
        else:
            self._server.hide()
            self._visible = False


def main():
    """Entry point"""
    # TODO configuration file handling and commandline options
    DBusGMainLoop(set_as_default=True)
    key_listener = MediaKeyListener()
    spotify = SpotifyControl()
    key_listener.add_handler(spotify.cb_key_handler)
    if NOTIFY:
        fetcher = None
        if COVER:
            fetcher = SpotifyCoverFetcher(
                    os.path.join(os.environ.get("HOME", "/tmp"),
                            ".spotcovers"))
        notifier = Notifier(fetcher)
        spotify.add_change_listener(notifier.display_track)
    if INDICATE:
        indicator = IndicatorHandler()
        indicator.cb_status_changed(spotify.connected)
        spotify.add_spotify_state_listener(indicator.cb_status_changed)

    loop = gobject.MainLoop()
    signal.signal(signal.SIGINT, lambda *args: loop.quit())
    loop.run()

if __name__ == "__main__":
    main()
