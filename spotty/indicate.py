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

"""Spotty indicator applet support plugin."""

from spotty.core import SpottyPlugin

class IndicatorPlugin(SpottyPlugin):
    """Class for handling indicator applet."""

    def __init__(self, controller):
        try:
            import indicate
        except ImportError:
            raise PluginError("Indicator plugin needs python-indicate")
        self._server = indicate.indicate_server_ref_default()
        self._server.set_type("music.spotify")
        self._server.set_desktop_file(
                "/usr/share/applications/spotify.desktop")
        self._visible = False


    def cb_status_changed(self, running):
        # TODO this does not seem to work
        if self._visible == running:
            return
        if running:
            self._server.show()
            self._visible = True
        else:
            self._server.hide()
            self._visible = False
