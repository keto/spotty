#
#    Copyright 2010, 2011, 2012 Pami Ketolainen
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

"""Plugin for desktop notifications"""
import dbus

from spotty import DEFAULT_ICON, LOG
from spotty.plugin import SpottyPlugin

class Notify(SpottyPlugin):
    """Plugin for displaying info notifications."""
    def __init__(self, spotify):
        """Constructor.
        
        :param string name: Name of the notifications sender
        :param string default_icon: Path to default icon file
        """
        super(Notify, self).__init__(spotify)
        self._icon = DEFAULT_ICON
        self._notifyservice = None
        self._notifyid = 0
        self.spotify.track_changed.connect(self.cb_track_changed)

    def unload(self):
        self.spotify.track_changed.disconnect(self.cb_track_changed)

    @property
    def notifyservice(self):
        """Lazy binding to dbus notification interface."""
        if self._notifyservice == None:
            try:
                proxy = self.spotify.bus.get_object(
                        "org.freedesktop.Notifications",
                        "/org/freedesktop/Notifications")
                self._notifyservice = dbus.Interface(proxy,
                        "org.freedesktop.Notifications")
            except Exception, exobj:
                LOG.error("Notification service connectin failed: %s" % exobj)
        return self._notifyservice

    def send(self, title, text="", icon=None, timeout=3000):
        """Display notification.

        :param string title: Notification title
        :param string text: Notification content text
        :param string icon: Path to notification icon
        :param integer timeout: Notification timeout
        """
        # TODO handle exceptions
        self._notifyid = self.notifyservice.Notify("spotty", self._notifyid,
                icon or self._icon, title, text, [], {}, timeout)

    def cb_track_changed(self, *_, **info):
        """Spotty track_changed handler."""
        artist = info.get("artist", u"")
        title = info.get("title", u"")
        album = info.get("album", u"")
        year = info.get("year", "")
        cover = info.get("cover", None)
        summary = "%s - %s" % (artist, title)
        body = "%s\n%s" % (album, year and "(%s)" % year)
        self.send(summary, text=body, icon=cover)

