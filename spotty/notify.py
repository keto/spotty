#!/usr/bin/python -tt
#
#    Copyright 2010, 2011 Pami Ketolainen
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

"""Notification helper class."""
import dbus, os

from spotty import DEFAULT_ICON

class SpottyNotify(object):
    """Class for displaying info notifications."""
    def __init__(self, name=None, default_icon=None):
        """Constructor.
        
        :param string name: Name of the notifications sender
        :param string default_icon: Path to default icon file
        """
        self._name = name or "spotty"
        self._icon = default_icon or DEFAULT_ICON
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

    def send(self, title, text="", icon=None, timeout=3000):
        """Display notification.

        :param string title: Notification title
        :param string text: Notification content text
        :param string icon: Path to notification icon
        :param integer timeout: Notification timeout
        """
        # TODO handle exceptions
        self._notifyid = self.notifyservice.Notify(self._name, self._notifyid,
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

__notificator = None

def get_notificator():
    """Notificator 'singleton' helper."""
    global __notificator
    if not __notificator:
        __notificator = SpottyNotify()
    return __notificator
