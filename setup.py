#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = "spotty",
    version = "0.2.0",
    author = "Pami Ketolainen",
    author_email = "pami.ketolainen@gmail.com",
    description = "Spotify Linux desktop integration",
    license = "GPL-3",
    url = "https://github.com/keto/spotty",
    packages = find_packages(),
    entry_points = {
        "console_scripts": [
            "spotty = spotty.core:main",
            "spotty-cli = spotty.cli:main"],
        "spotty.plugin": [
            "media_keys = spotty.media_keys:GnomeMediaKeys",
            "notify = spotty.notify:Notify",
            "cover = spotty.fetchart:CoverFetcher"
            ]},
    include_package_data = True
    )

