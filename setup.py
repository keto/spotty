
from setuptools import setup, find_packages

setup(
    name = "spotty",
    version = "0.1",
    author = "Pami Ketolainen",
    author_email = "pami.ketolainen@gmail.com",
    description = "Spotify notifacation and media key handler",
    license = "GPL-3",
    url = "http://to.be.done",
    packages = find_packages(),
    entry_points = { "console_scripts": [
            "spotty = spotty.core:main",
            "spotty-cli = spotty.cli:main"]
            },
    include_package_data = True
    )

