import getopt
import sys
from getpass import getpass
import click
from click import echo, secho
import requests
from distutils.version import StrictVersion

from sjtu_automata import *

__author__ = 'MXWXZ'


def echoinfo(msg):
    secho('[Info] ', fg='green', nl=False)
    echo(msg)


def echowarning(msg):
    secho('[Warning] ', fg='yellow', nl=False)
    echo(msg)


def echoerror(msg):
    secho('[ERROR] ', fg='red', nl=False)
    echo(msg)


class UserInterface:
    def __init__(self, useocr, cookie, round=2):
        self.session = None   # login session
        self.username = ''    # username
        self.password = ''    # password
        self.useocr = useocr  # true for use ocr
        self.cookie = cookie  # true to print cookie
        self.round = round    # 1 for 1st, 2 for 2nd, 3 for 3rd

    def Login(self):
        echowarning(
            'Only one session was permitted at the same time. Do NOT login on other browsers!')
        echoinfo('Login to your JAccount:')
        while True:
            if self.username == '' or self.password == '':
                self.username = input('Username: ')
                self.password = getpass('Password(no echo): ')
            self.session = Login(
                'http://electsys.sjtu.edu.cn/edu/login.aspx', self.username, self.password, self.useocr)
            if self.session == None:
                echoerror('Wrong username or password! Try again!')
                self.password = ''  # empty former password, otherwise wont ask for new
            else:
                break

        if self.cookie:
            echoinfo('Your cookie:')
            echo(('; '.join(
                ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    def CheckAvailable(self):
        return CheckAvailable(self.session, self.round)


def GetVersion():
    with open('Version', 'r') as f:
        return f.read()


def PrintVersion(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    echo('AutoElect by '+__author__)
    echo('Version: '+GetVersion())
    ctx.exit()


# For security reasons, we do not support username/password param pass.
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--version', is_flag=True, callback=PrintVersion,
              expose_value=False, is_eager=True)
@click.option('--no-checkupdate', is_flag=True, help='do not check update when start')
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
def cli(no_checkupdate, ocr, print_cookie, round):
    version = GetVersion()
    echo('AutoElect by '+__author__)
    echo('Version: '+version)
    echo('Github: https://github.com/MXWXZ/AutoElect\n')

    if not no_checkupdate:
        echoinfo('Checking update...')
        r = requests.get(
            'https://raw.githubusercontent.com/MXWXZ/AutoElect/master/Version')
        if StrictVersion(r.text)>version:
            echoinfo('Found new version: '+r.text)
            echowarning('New version found! We strongly recommand you to update to the latest version!')
            cmd = input('Continue without updating?(y/N)')
            if cmd != 'y':
                exit()
        else:
            echoinfo('You are up-to-date!')

    ui = UserInterface(ocr, print_cookie, round)
    ui.Login()


if __name__ == '__main__':
    cli()
