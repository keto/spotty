"""
Media key support plugin.
"""
from spotty import LOG
from spotty.plugin import SpottyPlugin

class GnomeMediaKeys(SpottyPlugin):
    """Support for media key control under Gnome."""

    # Mapping of keys to spotify control methods
    KEY_MAP = {
            "Play": "play_pause",
            "Pause": "pause",
            "Stop": "stop",
            "Next": "next",
            "Previous": "previous"}

    def __init__(self, spotify):
        super(GnomeMediaKeys, self).__init__(spotify)
        self.spotify.state_changed.connect(self.cb_state_changed)
        self._grabbed = False
        self._interface = self.spotify.bus.get_object(
                    "org.gnome.SettingsDaemon",
                    "/org/gnome/SettingsDaemon/MediaKeys")
        self._interface.connect_to_signal(
                "MediaPlayerKeyPressed", self.cb_handle_mediakey)

    def _grab(self):
        """Grab the media key control."""
        LOG.debug("Grabing media keys")
        self._interface.GrabMediaPlayerKeys(
                "spotty", 0,
                dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        self._grabbed = True

    def _release(self):
        """Release the media key control."""
        LOG.debug("Releasing media keys")
        self._interface.ReleaseMediaPlayerKeys("spotty",
                dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
        self._grabbed = False

    def unload(self):
        self._release()
        self.spotify.state_changed.disconnect(self.cb_state_changed)
        # TODO disconnect signal

    def cb_state_changed(self, state, *args, **kwargs):
        """Spotify running state change listener."""
        if state and not self._grabbed:
            self._grab()
        elif not state and self._grabbed:
            self._release()

    def cb_handle_mediakey(self, app, key):
        """Media key event callback."""
        LOG.debug("Media key event %s %s" % (app, key))
        if app != "spotty":
            return
        if self._interface is None:
            LOG.error("Disconnected, but got media key?!?!?!")
            return
        if key not in self.KEY_MAP:
            LOG.debug("No method to handle key %s" % key)
            return
        action = getattr(self.spotify, self.KEY_MAP[key], None)
        if action:
            action()
        else:
            LOG.error("%s has no method %s" %
                    (self.spotify, self.KEY_MAP[key]))
