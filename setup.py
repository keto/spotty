from setuptools import setup, find_packages

setup(
    name = "spotty",
    version = open("debian/changelog").readline().split()[1][1:-1],
    author = "Pami Ketolainen",
    author_email = "pami.ketolainen@gmail.com",
    description = "Spotify Linux desktop integration",
    license = "GPL-3",
    url = "https://github.com/keto/spotty",
    packages = find_packages(),
    entry_points = { "console_scripts": [
            "spotty = spotty.core:main",
            "spotty-cli = spotty.cli:main"]
            },
    include_package_data = True
    )

