import logging, os
from pkg_resources import resource_filename

# TODO: Propper logging configuration
# Setup root logger
LOG = logging.getLogger()
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.DEBUG)

DEFAULT_ICON = os.path.abspath(resource_filename(__name__, "icon_spotify.png"))
