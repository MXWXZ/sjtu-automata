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
from sjtu_automata.electsys.automata import (check_round, list_teacher,
                                             select_class, submit,
                                             view_arrange, view_page)
from sjtu_automata.utils.exceptions import ParamError


class UserInterface(object):
    def __init__(self, round=2):
        """
        Args:
            round=2: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        """
        self.session = None   # login session
        self.username = ''    # username
        self.__password = ''  # password
        self.round = round    # 1 for 1st, 2 for 2nd, 3 for 3rd

    def print_cookie(self):
        echoinfo('Your cookie:')
        echo(('; '.join(
            ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    # CALL SMALLER STEP BEFORE USE FUNCTION!
    def login(self, useocr, cookie):
        """User login.

        STEP 0

        Args:
            useocr: bool, True to use ocr autocaptcha.
            cookie: bool, True to print login cookie.
        """
        echowarning(
            'Only one session was permitted at the same time. Do NOT login on other browsers!')
        echoinfo('Login to your JAccount:')
        while True:
            if self.username == '' or self.__password == '':
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

        if cookie:
            self.print_cookie()

    def check_round(self):
        # check round available
        # STEP 1
        if check_round(self.session, self.round):
            echoinfo('elect round %d is available!' % self.round)
            return True
        else:
            echoerror('elect round %d is unavailable!' % self.round)
            return False

    def elect_class(self, classtype, classid, teacherid):
        """Elect class.

        STEP 2

        Args:
            classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
            classid: string, elect class id, e.g. AV001.
            teacherid: int, elect teacher id.
        """
        echoinfo('Class infomation:')
        echo('      classtype: %d' % classtype)
        echo('      classid: '+classid)
        echo('      teacherid: %d' % teacherid)
        echoinfo('Start electing!')
        postparam, text = view_page(self.session, self.round, classtype)
        echoinfo('Step 1/4...')
        postparam, getparam, text = view_arrange(
            self.session, self.round, classtype, classid, postparam)
        echoinfo('Step 2/4...')
        sleep(2)   # seems query time check, lets have a rest...
        postparam, getparam, text = select_class(
            self.session, self.round, teacherid, postparam, getparam)
        echoinfo('Step 3/4...')
        submit(self.session, self.round, classtype, postparam, getparam)
        echoinfo('Elect OK!')

    def list_teacher(self, classtype, classid):
        """List class teacher.

        STEP 2

        Args:
            classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
            classid: string, elect class id, e.g. AV001.
        """
        ls = list_teacher(self.session, self.round, classtype, classid)
        echoinfo('Teachers for '+classid+" :")
        echo('      TID\tName')
        for tid, name in ls.items():
            echo('      '+tid+'\t'+name)


# TODO: become bash like shell in future

def interactive():
    def show_interactive_help(show_error=False):
        if show_error:
            echoerror('Command format error!')

        echo('\n           AutoElect Interactive Mode')
        echo('cookie                                    print cookie')
        echo('elect [classtype] [classid] [teacherid]   elect class')
        echo('help                                      show this message')
        echo('login                                     login')
        echo('ls [classtype] [classid]                  list teacher')
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
            ui = UserInterface(int(options['round']))
            # options['ocr'] is string
            ui.login(options['ocr'] == 'True', False)
            if not ui.check_round():
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
            if not ui.username:
                echoerror('cookie command need login')
                return ui
            ui.print_cookie()
        elif cmd == 'version':
            echoinfo('Version: '+__version__)
        else:
            show_interactive_help(True)
        return ui

    def parse_inter_tri(ui, options, cmd):
        if cmd[0] == 'ls':
            if not ui.username:
                echoerror('ls command need login')
                return
            if cmd[1] not in ['1', '2', '3', '4']:
                echoerror('classtype require 1/2/3/4')
                return
            ui.list_teacher(int(cmd[1]), cmd[2])
        elif cmd[0] == 'set':
            if cmd[1] == 'ocr':
                if cmd[2] == 'True':
                    options['ocr'] = 'True'
                elif cmd[2] == 'False':
                    options['ocr'] = 'False'
                else:
                    echoerror('Param ocr require True/False')
                    return
                echoinfo('param ocr is set to '+cmd[2])
            elif cmd[1] == 'round':
                if cmd[2] in ['1', '2', '3']:
                    options['round'] = cmd[2]
                    echoinfo('param round is set to '+cmd[2])
                else:
                    echoerror('Param round require 1/2/3')
            else:
                echoerror('No param '+cmd[1])
        else:
            show_interactive_help(True)

    def parse_inter_qua(ui, options, cmd):
        if cmd[0] == 'elect':
            if not ui.username:
                echoerror('elect command need login')
                return
            if cmd[1] not in ['1', '2', '3', '4']:
                echoerror('classtype require 1/2/3/4')
                return
            if not cmd[3].isdigit():
                echoerror('teacherid require int')
                return
            ui.elect_class(int(cmd[1]), cmd[2], int(cmd[3]))
        else:
            show_interactive_help(True)

    # options
    options = {'ocr': 'False', 'round': '2'}
    ui = UserInterface()

    while True:
        if ui.username:
            secho('(%s)> ' % ui.username, fg='green', nl=False)
            cmd = input()
        else:
            cmd = input('(AutoElect)> ')
        cmd = cmd.split()

        if len(cmd) == 1:
            ui = parse_inter_one(ui, options, cmd[0])
        elif len(cmd) == 3:
            parse_inter_tri(ui, options, cmd)
        elif len(cmd) == 4:
            parse_inter_qua(ui, options, cmd)
        else:
            show_interactive_help(True)


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
@click.option('-l', '--list-teacher', is_flag=True, help='list teacher id [CTYPE CID]')
@click.option('--no-update', is_flag=True, help='do not check update when start')
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-r', '--round', default='2', type=click.Choice(['1', '2', '3']), help='elect round, default is 2')
@click.argument('ctype-cid-tid', nargs=-1)
def cli(interact, list_teacher, no_update, ocr, print_cookie, round, ctype_cid_tid):
    def parse_arg(arg, count=3):
        """Parse command pass args.

        Args:
            arg: list, command pass arg list.
            count=3: int, param each group.

        Returns:
            list in list, [[g0n0,g1n0,g2n0...],[g0n1,g1n1,g2n1...]...]
            example:
                arg=[1,2,3,4,5,6] count=2
                return [[1,3,5],[2,4,6]]
        """
        if not arg:
            raise ParamError(
                'Unsupport argument! Format: classtype classid [opt]teacherid')
        if len(arg) % count:
            raise ParamError('Not match classtype-classid-teacherid')

        ret = [arg[i:i+count] for i in range(0, len(arg), count)]

        for i in ret:
            if i[0] not in ['1', '2', '3', '4']:
                raise ParamError('Unsupport param: classtype='+i[0])
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
        ui = UserInterface(round)

        if not list_teacher:
            lst = parse_arg(ctype_cid_tid)
            for i in lst:
                classtype = int(i[0])
                classid = i[1]
                teacherid = i[2]

                ui.login(ocr, print_cookie)
                if ui.check_round():
                    ui.elect_class(classtype, classid, teacherid)
                else:
                    exit()
        else:
            lst = parse_arg(ctype_cid_tid, 2)
            ui.login(ocr, print_cookie)
            if not ui.check_round():
                exit()

            for i in lst:
                classtype = int(i[0])
                classid = i[1]

                ui.list_teacher(classtype, classid)


if __name__ == '__main__':
    cli()
