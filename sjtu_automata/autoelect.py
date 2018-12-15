import getopt
import sys
from getpass import getpass
from time import sleep

import click
from click import echo, secho

sys.path.append('../')

from sjtu_automata import check_update, echoerror, echoinfo, echowarning
from sjtu_automata.__version__ import __author__, __url__, __version__
from sjtu_automata.credential import login
from sjtu_automata.electsys.automata import (check_class_space, check_round_available,
                                             expend_page, list_teacher,
                                             navpage, select_teacher, submit,
                                             view_arrange, parse_renxuan, list_classid,
                                             list_group, check_classtype, check_class_selected)
from sjtu_automata.utils.exceptions import ParamError


class UserInterface(object):
    def __init__(self, round=2):
        """
        Args:
            round=2: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        """
        self.session = None     # login session
        self.username = None    # username
        self.__password = None  # password
        self.round = round      # 1 for 1st, 2 for 2nd, 3 for 3rd
        self.islogin = False    # True for login

        self.req = None         # last req
        self.classtype = 1      # current classtype
        self.classgroup = None  # current classgroup
        self.classid = None     # current classid
        self.data = None        # last post param
        self.params = None      # last get param
        self.grade = None       # current grade

        self.depth = 0          # current depth, 0 for mainpage, 1 for expand, 2 for view
        self.tmpreq = None  # tmp req classid list
        self.tmpparams = None   # tmp req params
        self.tmpdata = None     # tmp req data

    def __cd_classtype(self, new_classtype):
        if self.depth == 2:
            return None
        if self.classtype == new_classtype:
            return self.req
        self.req, self.data = navpage(
            self.session, self.classtype, new_classtype, self.data)
        self.classtype = new_classtype
        self.depth = 0
        return self.req

    def __cd_classgroup(self, classgroup):
        if self.classtype == 1:
            return None
        if self.depth == 2 and self.classtype in [2, 3, 4]:
            return None
        if self.classtype == 4:
            tmp, self.grade = parse_renxuan(self.req.text)
        else:
            self.grade = None
        self.req, self.data = expend_page(
            self.session, self.classtype, classgroup, self.data, self.grade)
        self.classgroup = classgroup
        self.depth = 1
        return self.req

    def __cd_classid(self, classid):
        if self.classtype == 1 and self.depth != 0:
            return None
        if self.classtype in [2, 3, 4] and self.depth != 1:
            return None
        if self.classtype != 4:
            self.grade = None
        # view arrange will be stored in tmp because of back operation
        self.tmpreq, self.tmpdata, self.tmpparams = view_arrange(
            self.session, self.classtype, self.classgroup, classid, self.data, self.grade)
        self.classid = classid
        self.depth = 2
        return self.tmpreq

    def cd_back(self):
        # cd back
        if self.depth != 2:
            return False
        if self.classtype in [2, 3, 4]:
            self.depth = 1
        elif self.classtype == 1:
            self.depth = 0
        return True

    def cd(self, cmd):
        # cmd: string, cd command
        if cmd in ['1', '2', '3', '4']:
            if not self.__cd_classtype(int(cmd)):
                echoerror('Command not valid!')
        else:
            if not self.__cd_classid(cmd) and not self.__cd_classgroup(cmd):
                echoerror('Command not valid!')

    def ls(self):
        if self.depth == 0:
            if self.classtype != 1:
                ret = list_group(self.req.text, self.classtype)
                echo('      \t\tCGP\t\t\tName')
            else:
                ret = list_classid(self.req.text)
                echo('      CID\tName')
        elif self.depth == 1:
            ret = list_classid(self.req.text)
            echo('      CID\tName')
        else:
            ret = list_teacher(self.tmpreq.text)
            echo('      TID\tName')

        for name, value in ret.items():
            echo('      '+name+'\t'+value)

    def print_cookie(self):
        echoinfo('Your cookie:')
        echo(('; '.join(
            ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    def login(self, ocr):
        """Login user.

        Args:
            ocr: bool, True to use ocr
        """
        echowarning(
            'Only one session was permitted at the same time. Do NOT login on other browsers!')
        echoinfo('Login to your JAccount:')
        while True:
            if not self.username or not self.__password:
                self.username = input('Username: ')
                self.__password = getpass('Password(no echo): ')
            self.session = login(
                'http://electsys.sjtu.edu.cn/edu/login.aspx', self.username, self.__password, ocr)

            if not self.session:
                echoerror('Wrong username or password! Try again!')
                self.__password = ''  # empty former password, otherwise wont ask for new
            else:
                break

        echoinfo('Login successful!')
        self.islogin = True

    def check_round_available(self, delay):
        """Check round available.

        Check if round is available.

        Args:
            delay: int, check delay, 0 for nocheck(exit directly)
        """
        while True:
            flg, self.req, self.data = check_round_available(
                self.session, self.round)
            if flg:
                echoinfo('Elect round %d is available!' % self.round)
                break
            else:
                if delay == 0:
                    echoerror('Elect round %d is unavailable!'%self.round)
                    exit()
                else:
                    echoerror('Elect round %d is unavailable! Retry in %ds...' % (
                        self.round, delay))
                    sleep(delay)

    def check_class_selected(self,classid):
        if not ((self.classtype==1 and self.depth==0) or (self.classtype !=1 and self.depth==1)):
            echoerror('Please go to the right page!')
            return False
        ret= check_class_selected(self.req.text,classid)
        if ret:
            echoinfo('Class %s is selected!'%classid)
        else:
            echoinfo('Class %s is not selected!'%classid)
        return ret

    def select_teacher(self, teacherid, delay):
        """Elect class.

        Args:
            teacherid: int, elect teacher id.
            delay: int, check delay, 0 for nocheck(exit directly)
        """
        if self.depth != 2:
            return False
        while True:
            if check_class_space(self.tmpreq.text, teacherid):
                self.req, self.data, self.params = select_teacher(
                    self.session, teacherid, self.tmpdata, self.tmpparams)
                break
            else:
                if delay == 0:
                    echoerror('Teacher %d is full!' % teacherid)
                    exit()
                else:
                    echoerror('Teacher %d is full! Retry in %ds...' %
                              (teacherid, delay))
                    sleep(delay - 1)  # sacrifice 1s for the elder...
        return True

    def submit(self):
        if self.classtype != 4:
            self.grade = None
        req, ret = submit(self.session, self.classtype,
                          self.data, self.params, self.grade)
        if ret:
            self.islogin = False

            self.classtype = 1
            self.session=self.req = self.classgroup = self.classid = self.data = self.params = self.grade = None

            self.depth = 0
            self.tmpreq = self.tmpparams = self.tmpdata = None
            return True
        else:
            echoerror('Submit error!')
            exit()

# TODO: more cmd in future


def shell(ui, cmd):
    def show_shell_help(show_error=False):
        if show_error:
            echoerror('Command format error!')

        echo('\n               AutoElect Shell Command')
        echo('back                                      back when in classid')
        echo('cd [classtype/classgroup/classid...]      change directory')
        echo('cookie                                    print cookie')
        echo('elect [teacherid] [delay=15]              elect class')
        echo('help                                      show this message')
        echo('login [round=2] [ocr=0] [delay=15]        login')
        echo('ls                                        list current')
        echo('quit                                      quit script')
        echo('update                                    check update')
        echo('version                                   show version')
        echo()

    def parse_cmd_one(ui, cmdlist):
        if cmdlist[0] == 'back':
            ui.cd_back()
        elif cmdlist[0] == 'cookie':
            if not ui.islogin:
                return False
            ui.print_cookie()
        elif cmdlist[0] == 'help':
            show_shell_help()
        elif cmdlist[0] == 'ls':
            if not ui.islogin:
                return False
            ui.ls()
        elif cmdlist[0] == 'quit':
            exit()
        elif cmdlist[0] == 'update':
            check_update()
        elif cmdlist[0] == 'version':
            echoinfo('Version: '+__version__)
        else:
            show_shell_help(True)
        return True

    def parse_cmd_dou(ui, cmdlist):
        if cmdlist[0] == 'cd':
            if not ui.islogin:
                return False
            ui.cd(cmdlist[1])
        else:
            show_shell_help(True)
        return True

    def parse_cmd_tri(ui, cmdlist):
        if cmdlist[0] == 'elect':
            if not ui.islogin:
                return False
            if not cmdlist[1].isdigit():
                echoerror('Param teacherid require int')

            echoinfo('Selecting teacher...(1/2)')
            if ui.select_teacher(int(cmdlist[1]), int(cmdlist[2])):
                sleep(1)
                echoinfo('Submitting...(2/2)')
                if ui.submit():
                    echoinfo('Elect OK~ You are logged out!')
                    echowarning(
                        'Your username and password will be remembered until you quit.')
                else:
                    echoerror('Submit error!')
                    exit()
            else:
                echoerror('Elect needs cd [classid] first!')
        else:
            show_shell_help(True)
        return True

    def parse_cmd_qua(ui, cmdlist):
        if cmdlist[0] == 'login':
            ui.round = int(cmdlist[1])
            ui.login(cmdlist[2] == '1')
            ui.check_round_available(int(cmdlist[3]))
        else:
            show_shell_help(True)
        return True

    def parse_cmd_many(ui, cmdlist):
        if cmdlist[0] == 'cd':
            if not ui.islogin:
                return 2
            for i in cmdlist[1:]:
                ui.cd(i)
                sleep(0.5)
        else:
            return 0
        # we do not need other checks.
        return 1

    cmdlist = cmd.split()
    if cmdlist[0] == 'elect' and len(cmdlist) == 2:
        cmdlist.append('15')
    if cmdlist[0] == 'login':
        if len(cmdlist) == 3:
            cmdlist.append('15')
        elif len(cmdlist) == 2:
            cmdlist.append('0')
            cmdlist.append('15')
        elif len(cmdlist) == 1:
            cmdlist.append('2')
            cmdlist.append('0')
            cmdlist.append('15')
    ret = False
    tmp = parse_cmd_many(ui, cmdlist)
    if tmp == 1:
        ret = True
    elif tmp == 0:
        if len(cmdlist) == 1:
            ret = parse_cmd_one(ui, cmdlist)
        elif len(cmdlist) == 2:
            ret = parse_cmd_dou(ui, cmdlist)
        elif len(cmdlist) == 3:
            ret = parse_cmd_tri(ui, cmdlist)
        elif len(cmdlist) == 4:
            ret = parse_cmd_qua(ui, cmdlist)
        else:
            show_shell_help(True)
            ret = True
    if not ret:
        echoerror('Command needs login')


def interactive():
    ui = UserInterface()

    while True:
        if ui.islogin:
            if ui.depth == 2:
                secho('(%s %s)$ ' %
                      (ui.username, ui.classid), fg='green', nl=False)
            else:
                secho('(%s)$ ' % ui.username, fg='green', nl=False)
            cmd = input()
        else:
            cmd = input('(AutoElect)> ')

        shell(ui, cmd)


def print_version(ctx, param, value):
    # override click version print
    if not value or ctx.resilient_parsing:
        return
    echo('AutoElect by '+__author__)
    echo('Version: '+__version__)
    ctx.exit()


# For security reasons, we do not support username/password param pass.

# TODO: Add more command

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
# system
@click.option('-v', '--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
# start-up
@click.option('-i', '--interact', is_flag=True, help='go to interactive mode (ignore other param)')
@click.option('--no-update', is_flag=True, help='do not check update when start')
# login param
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('--delay-elect', default=15, type=int, help='elect fresh delay(seconds), default is 15')
@click.option('--delay-login', default=15, type=int, help='user login delay(seconds) default is 15')
# mutex operation
@click.option('-e', '--elect', multiple=True, type=str, help='elect class [CTYPE/CGP/CID/TID]')
@click.option('-l', '--list-teacher', type=str, help='list teacher id [CTYPE/CGP/CID]')
def cli(interact, no_update, round, ocr, print_cookie, delay_elect, delay_login, elect, list_teacher):
    version = __version__
    echo('AutoElect by '+__author__)
    echo('Version: '+version)
    echo('Github: '+__url__+'\n')

    # TODO: remove in 1.0.0
    if not no_update and check_update():
        cmd = input('Continue without updating?(y/N)')
        if cmd != 'y':
            exit()

    if interact:
        interactive()
    else:
        # check operation
        if elect and list_teacher:
            raise ParamError('-e/-l are mutex operation!')

        ui = UserInterface()
        if elect:
            for i in elect:
                if ui.username:
                    echoinfo('Going for next elect, you must wait 30s for not being banned!')
                    sleep(31)
                i = i.split('/')
                cddir = 'cd '+' '.join(i[0:-2])
                if not ui.islogin:
                    shell(ui, 'login %s %d %d' % (round, ocr, delay_login))
                echoinfo('Switching to class...')
                shell(ui, cddir)
                if ui.check_class_selected(i[-2]):
                    echoinfo('Ignore elect...')
                    continue
                else:
                    shell(ui,'cd '+i[-2])
                    shell(ui, 'elect %s %d' % (i[-1], delay_elect))
        elif list_teacher:
            lst = list_teacher.split('/')
            cddir = 'cd '+' '.join(lst)
            shell(ui, 'login %s %d %d' % (round, ocr, delay_login))
            echoinfo('Switching to class...')
            shell(ui, cddir)
            shell(ui, 'ls')
        else:
            echoerror('One of -e/-l must exist!')
            exit()


if __name__ == '__main__':
    cli()
