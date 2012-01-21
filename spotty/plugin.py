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
