from distutils.version import StrictVersion

import requests
from click import echo, secho

from .__version__ import __version__, __update_url__

name = "sjtu_automata"

def echoinfo(msg):
    secho('[Info] ', fg='green', nl=False)
    echo(msg)


def echowarning(msg):
    secho('[Warning] ', fg='yellow', nl=False)
    echo(msg)


def echoerror(msg):
    secho('[ERROR] ', fg='red', nl=False)
    echo(msg)


def check_update():
    """Check for script version.

    Check latest version on Github page.

    Returns:
        bool, True for new version released.
    """
    echoinfo('Checking update...')
    req = requests.get(__update_url__)
    if StrictVersion(req.text) > StrictVersion(__version__):
        echoinfo('Found new version: '+req.text)
        echowarning(
            'New version found! We strongly recommand you to update to the latest version!')
        echowarning('Use "pip3 install sjtu-automata --upgrade" to upgrade!')

        return True
    else:
        echoinfo('You are up-to-date!')
    return False
