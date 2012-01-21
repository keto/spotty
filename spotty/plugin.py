#
#    Copyright 2012 Pami Ketolainen
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

"""Plugin related stuff."""

class SpottyPlugin(object):
    """Spotty plugin base class."""
    # Plugins are singletons
    __instance = None
    #: Used to specify other required plugins
    requires = []

    @classmethod
    def load(cls, spotify):
        """Plugin loader.
        :param spotify: SpotifyControl object
        :returns: Plugin instance
        """
        if cls == SpottyPlugin:
            raise RuntimeError("Tried to load plain base plugin")
        if cls.__instance is None:
            cls.__instance = cls(spotify)
        return cls.__instance

    def __init__(self, spotify):
        """Constructor.
        :param spotify: SpotifyControl object
        """
        self.spotify = spotify

    def unload(self):
        """Plugin unloader."""
        pass
