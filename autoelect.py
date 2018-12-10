import getopt
import sys
import click
from click import echo, secho

from sjtu_automata import *

__author__ = 'MXWXZ'


def echoinfo(msg):
    secho('[Info] ', fg='green', nl=False)
    echo(msg)


def echowarning(msg):
    secho('[Warning] ', fg='yellow', nl=False)
    echo(msg)


class UserInterface:
    def __init__(self, useocr,cookie, round=2):
        self.session = None  # login session
        self.useocr = useocr # true for use ocr
        self.cookie = cookie # true to print cookie
        self.round = round   # 1 for 1st, 2 for 2nd, 3 for 3rd

    def Login(self):
        self.session = Login(
            'http://electsys.sjtu.edu.cn/edu/login.aspx', self.useocr)
        if self.cookie:
            echoinfo('Your cookie:')
            echo(('; '.join(['='.join(item) for item in self.session.cookies.items()])).replace('"',''))

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


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--version', is_flag=True, callback=PrintVersion,
              expose_value=False, is_eager=True)
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
def cli(ocr, print_cookie,round):
    echo('AutoElect by '+__author__)
    echo('Version: '+GetVersion())
    echowarning(
        'Only one session was permitted at the same time. Do NOT login on other browsers!')
    echoinfo('Login to your JAccount:')
    ui = UserInterface(ocr,print_cookie, round)
    ui.Login()
    print(ui.CheckAvailable())


if __name__ == '__main__':
    cli()
