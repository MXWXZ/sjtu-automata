import getopt
from time import sleep
import sys
from getpass import getpass
import click
from click import echo, secho
import requests
from distutils.version import StrictVersion

from sjtu_automata import *

__author__ = 'MXWXZ'
__versionurl__ = 'https://raw.githubusercontent.com/MXWXZ/AutoElect/master/Version'


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
    def __init__(self, round=2):
        self.session = None   # login session
        self.__username = ''    # username
        self.__password = ''    # password
        self.round = round    # 1 for 1st, 2 for 2nd, 3 for 3rd

    def PrintCookie(self):
        echoinfo('Your cookie:')
        echo(('; '.join(
            ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    # CALL SMALLER STEP BEFORE USE FUNCTION!
    # STEP 0
    def Login(self, useocr, cookie):
        echowarning(
            'Only one session was permitted at the same time. Do NOT login on other browsers!')
        echoinfo('Login to your JAccount:')
        while True:
            if self.__username == '' or self.__password == '':
                self.__username = input('Username: ')
                self.__password = getpass('Password(no echo): ')
            self.session = Login(
                'http://electsys.sjtu.edu.cn/edu/login.aspx', self.__username, self.__password, useocr)
            if self.session == None:
                echoerror('Wrong username or password! Try again!')
                self.__password = ''  # empty former password, otherwise wont ask for new
            else:
                break

        echoinfo('Login successful!')

        if cookie:
            self.PrintCookie()

    # STEP 1
    def CheckAvailable(self):
        if CheckAvailable(self.session, self.round):
            echoinfo('elect round '+str(self.round)+' is available!')
            return True
        else:
            echoerror('elect round '+str(self.round)+' is unavailable!')
            return False

    # STEP 2
    def ElectLesson(self, classtype, classid, teacherid):
        echoinfo('Class infomation:')
        echo('      classtype: '+classtype)
        echo('      classid: '+classid)
        echo('      teacherid: '+teacherid)
        echoinfo('Start electing!')
        postparam, text = ViewPage(self.session, self.round, classtype)
        echoinfo('Step 1/4...')
        postparam, getparam, text = ViewArrange(
            self.session, self.round, classtype, classid, postparam)
        echoinfo('Step 2/4...')
        sleep(2)   # seems query time check, just wait a while...
        postparam, getparam, text = SelectLesson(
            self.session, self.round, teacherid, postparam, getparam)
        echoinfo('Step 3/4...')
        Submit(self.session, self.round, classtype, postparam, getparam)
        echoinfo('Elect OK!')

    # STEP 2
    def ListTeacher(self, classtype, classid):
        ls = ListTeacher(self.session, self.round, classtype, classid)
        echoinfo('Teachers for '+classid+" :")
        echo('      TID\tName')
        for tid, name in ls.items():
            echo('      '+tid+'\t'+name)


def GetVersion():
    with open('Version', 'r') as f:
        return f.read()


def PrintVersion(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    echo('AutoElect by '+__author__)
    echo('Version: '+GetVersion())
    ctx.exit()


def CheckUpdate(url, version):
    echoinfo('Checking update...')
    r = requests.get(url)
    if StrictVersion(r.text) > version:
        echoinfo('Found new version: '+r.text)
        echowarning(
            'New version found! We strongly recommand you to update to the latest version!')
        cmd = input('Continue without updating?(y/N)')
        if cmd != 'y':
            return False
    else:
        echoinfo('You are up-to-date!')
    return True


def ParseArg(arg, count=3):
    if not arg:
        raise Exception('No argument! Format: classtype classid [opt]teacherid')
    if len(arg) % count:
        raise Exception('Not match classtype-classid-teacherid')

    ret= [arg[i:i+count] for i in range(0, len(arg), count)]

    for i in ret:
        if i[0] not in ['1', '2', '3', '4']:
            raise Exception('Unknown classtype: '+i[0])
    return ret

def ShowInteractiveHelp():
    echo('\tAutoElect Interactive Mode')
    echo('elect [classtype] [classid] [teacherid]\telect class')
    echo('help\t\t\t\t\tshow this message')
    echo('login\t\t\t\t\tlogin')
    echo('ls [classtype] [classid]\t\tlist teacher')
    echo('option\t\t\t\t\tshow options')
    echo('set [option] [value]\t\t\tset option to value')

# TODO: become bash like shell in future
# TODO: Refactor
def Interactive():
    ocr=False
    round=2
    ui=None
    while True:
        cmd=input('(AutoElect)> ')
        cmd=cmd.split()
        
        if len(cmd) ==1:
            if cmd[0]=='help':
                ShowInteractiveHelp()
            elif cmd[0]=='login':
                ui = UserInterface(round)
                ui.Login(ocr, False)
                if not ui.CheckAvailable():
                    exit()
            elif cmd[0]=='option':
                echo('ocr='+str(ocr))
                echo('round='+str(round))
            else:
                ShowInteractiveHelp()
        elif len(cmd) == 3:
            if cmd[0]=='ls':
                if not ui:
                    echoerror('Need login')
                    continue
                ui.ListTeacher(int(cmd[1]),cmd[2])
            elif cmd[0]=='set':
                if cmd[1]=='ocr':
                    if cmd[2]=='True':
                        ocr=True
                    elif cmd[2]=='False':
                        ocr=False
                    else:
                        echoerror('param error')
                        continue
                elif cmd[1]=='round':
                    round=int(cmd[2])
                else:
                    echoerror('param error')
            else:
                ShowInteractiveHelp()
        elif len(cmd) == 4:
            if cmd[0]=='elect':
                if not ui:
                    echoerror('Need login')
                    continue
                ui.ElectLesson(int(cmd[1]),cmd[2], cmd[3])
        else:
            ShowInteractiveHelp()


# For security reasons, we do not support username/password param pass.


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--version', is_flag=True, callback=PrintVersion,
              expose_value=False, is_eager=True)
@click.option('-i','--interactive', is_flag=True, help='go to interactive mode (ignore other param)')     
@click.option('-l', '--list-teacher', is_flag=True, help='list teacher id [CTYPE CID]')
@click.option('--no-checkupdate', is_flag=True, help='do not check update when start')
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
@click.argument('ctype-cid-tid', nargs=-1)
def cli(interactive,list_teacher, no_checkupdate, ocr, print_cookie, round, ctype_cid_tid):
    version = GetVersion()
    echo('AutoElect by '+__author__)
    echo('Version: '+version)
    echo('Github: https://github.com/MXWXZ/AutoElect\n')

    if not (no_checkupdate or CheckUpdate(__versionurl__, version)):
        exit()

    if interactive:
        Interactive()
    else:
        ui = UserInterface(round)

        if not list_teacher:
            lst = ParseArg(ctype_cid_tid)
            for i in lst:
                classtype = int(i[0])
                classid = i[1]
                teacherid = i[2]

                ui.Login(ocr, print_cookie)
                if ui.CheckAvailable():
                    ui.ElectLesson(classtype, classid, teacherid)
                else:
                    exit()
        else:
            lst = ParseArg(ctype_cid_tid,2)
            ui.Login(ocr, print_cookie)
            if not ui.CheckAvailable():
                exit()

            for i in lst:
                classtype = int(i[0])
                classid = i[1]

                ui.ListTeacher(classtype,classid)


if __name__ == '__main__':
    cli()
