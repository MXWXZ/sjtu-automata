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
from sjtu_automata.electsys.automata import (check_class_full, check_round_available,
                                             expend_page, list_teacher,
                                             navpage, select_teacher, submit,
                                             view_arrange, parse_renxuan, list_classid,
                                             list_group, check_classtype)
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
        self.reqclassid = None  # tmp req classid list
        self.tmpparams = None   # tmp req params
        self.tmpdata = None     # tmp req data

    def __cd_classtype(self, new_classtype):
        if self.depth == 2:
            return None
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
        self.reqclassid, self.tmpdata, self.tmpparams = view_arrange(
            self.session, self.classtype, self.classgroup, classid, self.data, self.grade)
        self.classid = classid
        self.depth = 2
        return self.reqclassid

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
            ret = list_teacher(self.reqclassid.text)
            echo('      TID\tName')

        for name, value in ret.items():
            echo('      '+name+'\t'+value)

    def print_cookie(self):
        echoinfo('Your cookie:')
        echo(('; '.join(
            ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    def login(self, useocr, cookie):
        """User login.

        Args:
            useocr: bool, True to use ocr autocaptcha.
            cookie: bool, True to print login cookie.
        """
        echowarning(
            'Only one session was permitted at the same time. Do NOT login on other browsers!')
        echoinfo('Login to your JAccount:')
        while True:
            if not self.username or not self.__password:
                self.username = input('Username: ')
                self.__password = getpass('Password(no echo): ')
            self.session = login(
                'http://electsys.sjtu.edu.cn/edu/login.aspx', self.username, self.__password, useocr)

            if not self.session:
                echoerror('Wrong username or password! Try again!')
                self.__password = ''  # empty former password, otherwise wont ask for new
            else:
                break

        echoinfo('Login successful!')
        self.islogin = True

        if cookie:
            self.print_cookie()

    def check_round_available(self):
        # check round available
        flg, self.req, self.data = check_round_available(
            self.session, self.round)
        if flg:
            echoinfo('Elect round %d is available!' % self.round)
        else:
            echoerror('Elect round %d is unavailable!' % self.round)
        return flg

    def select_teacher(self, teacherid):
        """Elect class.

        Args:
            teacherid: int, elect teacher id.
        """
        if self.depth != 2:
            return False
        self.req, self.data, self.params = select_teacher(
            self.session, teacherid, self.tmpdata, self.tmpparams)
        return True

    def submit(self):
        if self.classtype != 4:
            self.grade = None
        req, ret = submit(self.session, self.classtype,
                          self.data, self.params, self.grade)
        if ret:
            self.islogin = False
            return True
        else:
            echoerror('Submit error!')
            exit()

# TODO: more cmd in future


def interactive():
    def show_interactive_help(show_error=False):
        if show_error:
            echoerror('Command format error!')

        echo('\n           AutoElect Interactive Mode')
        echo('back                                      back when in classid')
        echo('cd [classtype/classgroup/teacherid]       change directory')
        echo('cookie                                    print cookie')
        echo('elect [teacherid]                         elect class')
        echo('help                                      show this message')
        echo('login                                     login')
        echo('ls                                        list current')
        echo('option                                    show options')
        echo('quit                                      quit script')
        echo('set [option] [value]                      set option to value')
        echo('update                                    check update')
        echo('version                                   show version')
        echo()

    def parse_inter_one(ui, options, cmd):
        if cmd == 'help':
            show_interactive_help()
        elif cmd == 'login':
            ui.round = int(options['round'])
            # options['ocr'] is string
            ui.login(options['ocr'] == 'True', False)
            if not ui.check_round_available():
                exit()
        elif cmd == 'option':
            echo('\n\tCurrent Options')
            for key, value in options.items():
                echo('%s = %s' % (key, value))
            echo()
        elif cmd == 'quit':
            exit()
        elif cmd == 'update':
            check_update()
        elif cmd == 'cookie':
            if not ui.islogin:
                return False
            ui.print_cookie()
        elif cmd == 'version':
            echoinfo('Version: '+__version__)
        elif cmd == 'ls':
            if not ui.islogin:
                return False
            ui.ls()
        elif cmd == 'back':
            ui.cd_back()
        else:
            show_interactive_help(True)
        return True

    def parse_inter_dou(ui, options, cmd):
        if cmd[0] == 'cd':
            if not ui.islogin:
                return False
            ui.cd(cmd[1])
        elif cmd[0] == 'elect':
            if not ui.islogin:
                return False
            if not cmd[1].isdigit():
                echoerror('Param teacherid require int')
            echoinfo('Selecting teacher...(1/2)')
            if ui.select_teacher(int(cmd[1])):
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
            show_interactive_help(True)
        return True

    def parse_inter_tri(ui, options, cmd):
        if cmd[0] == 'set':
            if cmd[1] == 'ocr':
                if cmd[2] == 'True':
                    options['ocr'] = 'True'
                elif cmd[2] == 'False':
                    options['ocr'] = 'False'
                else:
                    echoerror('Param ocr require True/False')
                    return True
                echoinfo('Param ocr is set to '+cmd[2])
            elif cmd[1] == 'round':
                if cmd[2] in ['1', '2', '3']:
                    options['round'] = cmd[2]
                    echoinfo('Param round is set to '+cmd[2])
                else:
                    echoerror('Param round require 1/2/3')
            else:
                echoerror('No param '+cmd[1])
        else:
            show_interactive_help(True)
        return True

    # options
    options = {'ocr': 'False', 'round': '2'}
    ui = UserInterface()
    parse_inter_one(ui, options, 'option')

    while True:
        if ui.islogin:
            if ui.depth == 2:
                secho('(%s %s)> ' %
                      (ui.username, ui.classid), fg='green', nl=False)
            else:
                secho('(%s)> ' % ui.username, fg='green', nl=False)
            cmd = input()
        else:
            cmd = input('(AutoElect)> ')
        cmd = cmd.split()

        if len(cmd) == 1:
            ret = parse_inter_one(ui, options, cmd[0])
        elif len(cmd) == 2:
            ret = parse_inter_dou(ui, options, cmd)
        elif len(cmd) == 3:
            ret = parse_inter_tri(ui, options, cmd)
        else:
            show_interactive_help(True)
        if not ret:
            echoerror('command needs login')


def print_version(ctx, param, value):
    # override click version print
    if not value or ctx.resilient_parsing:
        return
    echo('AutoElect by '+__author__)
    echo('Version: '+__version__)
    ctx.exit()


# For security reasons, we do not support username/password param pass.


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-v', '--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
@click.option('-i', '--interact', is_flag=True, help='go to interactive mode (ignore other param)')
@click.option('-l', '--list-teacher', is_flag=True, help='list teacher id [CTYPE CGP CID]')
@click.option('--no-update', is_flag=True, help='do not check update when start')
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
@click.argument('ctype-cgp-cid-tid', nargs=-1)
def cli(interact, list_teacher, no_update, ocr, print_cookie, round, ctype_cgp_cid_tid):
    def parse_arg(arg, count=4):
        """Parse command pass args.

        The args will be split according to ctype.

        Args:
            arg: list, command pass arg list.
            count: int, param count.

        Returns:
            list in list, [[g0n0,g0n1,g0n2...],[g1n0,g1n1,g1n2...]...]
        """
        if not arg:
            raise ParamError(
                'Unsupport argument! Format: classtype classid [opt]teacherid')

        # TODO: Be more pythonic
        ret = []
        i = 0
        while i != len(arg):
            check_classtype(int(arg[i]))
            tmp = []
            if arg[i] == '1':
                for j in range(count-1):
                    tmp.append(arg[j])
                ret.append(tmp)
                i += count-1
            else:
                for j in range(count):
                    tmp.append(arg[j])
                ret.append(tmp)
                i += count
        return ret

    version = __version__
    echo('AutoElect by '+__author__)
    echo('Version: '+version)
    echo('Github: '+__url__+'\n')

    # TODO: remove in 1.0.0
    if not (no_update or check_update()):
        cmd = input('Continue without updating?(y/N)')
        if cmd != 'y':
            exit()

    if interact:
        interactive()
    else:
        ui = UserInterface(int(round))

        if not list_teacher:
            lst = parse_arg(ctype_cgp_cid_tid, 4)
            for i in lst:
                if ui.username:
                    echoinfo(
                        'Going next, you must wait a while for not being banned...')
                    sleep(16)   # or you will be banned for 30

                classtype = i[0]
                if classtype == '1':
                    classid = i[1]
                    teacherid = int(i[2])
                else:
                    classgroup = i[1]
                    classid = i[2]
                    teacherid = int(i[3])

                ui.login(ocr, print_cookie)
                if ui.check_round_available():
                    if classtype != '1':
                        ui.cd(classtype)
                        ui.cd(classgroup)
                    ui.cd(classid)
                    ui.select_teacher(teacherid)
                    ui.submit()
                else:
                    exit()
        else:
            lst = parse_arg(ctype_cgp_cid_tid, 3)
            ui.login(ocr, print_cookie)
            if not ui.check_round_available():
                exit()

            for i in lst:
                classtype = i[0]
                if classtype == '1':
                    classid = i[1]
                else:
                    classgroup = i[1]
                    classid = i[2]

                if classtype != '1':
                    ui.cd(classtype)
                    ui.cd(classgroup)
                ui.cd(classid)
                ui.ls()


if __name__ == '__main__':
    cli()
