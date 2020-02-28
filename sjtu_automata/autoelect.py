import getopt
import sys
from time import sleep

import click
from click import echo, secho
import threading

sys.path.append('../')

from sjtu_automata import check_update, echoerror, echoinfo, echowarning
from sjtu_automata.__version__ import __author__, __url__, __version__
from sjtu_automata.credential import login
from sjtu_automata.electsys.automata import (
    get_studentid, get_params, elect_class)


class UserInterface(object):
    def __init__(self):
        self.session = None     # login session

        self.params = None      # elect param
        self.studentid = None   # student id
        self.status = []        # elect status
        self.tp = []            # thread pool
        self.tl = []            # thread lock
        self.tclass = []        # thread classid
        self.id = 0             # thread id
        self.glock = threading.Lock()  # global lock

    def print_cookie(self):
        echoinfo('Your cookie:')
        echo(('; '.join(
            ['='.join(item) for item in self.session.cookies.items()])).replace('"', ''))

    def login(self, ocr, delay):
        """Login user.

        Args:
            ocr: bool, True to use ocr
            delay: int, retry delay

        Returns:
            true for success.
        """
        echoinfo('Login to your JAccount:')
        self.session = login(
            'https://i.sjtu.edu.cn/jaccountlogin', ocr)

        self.studentid = get_studentid(self.session)
        if not self.studentid:
            echoerror('Can\'t find student id!')
            return False

        while 1:
            self.params = get_params(self.session, self.studentid)
            if self.params['njdm_id'] and self.params['zyh_id']:
                break
            echoinfo('Not open, retry in %d seconds...' % delay)
            sleep(delay)

        echoinfo('Login successful!')
        return True

    def __elect_thread(self, tid, classtype, classid, jxbid, delay):
        while self.status[tid] == 2 or self.status[tid] == 4 or self.status[tid] == -1:
            ret = elect_class(self.session, self.studentid,
                              self.params, classtype, classid, jxbid)
            with self.tl[tid]:
                if self.status[tid] != 0 and self.status[tid] != 1 and self.status[tid] != 3:
                    self.status[tid] = ret
                    if ret == 0 or ret == 1 or ret == 3:
                        self.__parse_status(tid, ret)
                        break
            sleep(delay)

    def add_elect(self, number, classtype, classid, jxbid, delay):
        for i in range(number):
            self.tp.append(threading.Thread(
                target=self.__elect_thread, args=(self.id, classtype, classid, jxbid, delay,)))
        self.tl.append(threading.Lock())
        self.tclass.append(classid)
        self.status.append(-1)
        self.id += 1

    def start_elect(self):
        echoinfo('Starting thread...')
        for i in self.tp:
            i.daemon = True
            i.start()
        echoinfo('Task running! Input "s" to view status.')

    def __parse_status(self, tid, status):
        with self.glock:
            if status == -1:
                secho('[' + self.tclass[tid] + '] ', fg='red', nl=False)
                echo('Not started!')
            elif status == 0:
                secho('[' + self.tclass[tid] + '] ', fg='green', nl=False)
                echo('Finished!')
            elif status == 1:
                secho('[' + self.tclass[tid] + '] ', fg='red', nl=False)
                echo('Time conflict! Stopped.')
            elif status == 2:
                secho('[' + self.tclass[tid] + '] ', fg='yellow', nl=False)
                echo('Class is full! Retrying...')
            elif status == 3:
                secho('[' + self.tclass[tid] + '] ', fg='red', nl=False)
                echo('Param error! Stopped.')
            elif status == 4:
                secho('[' + self.tclass[tid] + '] ', fg='yellow', nl=False)
                echo('Unknown error! Retrying...')

    def fetch_status(self):
        echoinfo('Current status:')
        for i, j in enumerate(self.status):
            self.__parse_status(i, j)

    def get_input(self):
        while True:
            cmd = input()
            if cmd == 's':
                self.fetch_status()

    def check_alive(self):
        for i in self.status:
            if i == -1 or i == 2 or i == 4:
                return True
        return False


def print_version(ctx, param, value):
    # override click version print
    if not value or ctx.resilient_parsing:
        return
    echo('AutoElect by ' + __author__)
    echo('Version: ' + __version__)
    ctx.exit()

# TODO: Add more command


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
# system
@click.option('-v', '--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
# start-up
@click.option('--no-update', is_flag=True, help='do not check update when start')
# login param
@click.option('-o', '--ocr', is_flag=True, help='use OCR to auto fill captcha')
@click.option('--print-cookie', is_flag=True, help='print the cookie for advanced use')
@click.option('-d', '--delay', default=1, type=int, help='delay seconds between attempts, default is 1')
@click.option('-c', '--check-delay', default=3, type=int, help='delay seconds for open elect check, default is 3')
@click.option('-n', '--number', default=1, type=int, help='thread number per class, default is 1')
# argument
@click.argument('classtypeid', required=True, nargs=-1)
def cli(no_update, ocr, print_cookie, delay, check_delay, number, classtypeid):
    version = __version__
    echo('AutoElect by ' + __author__)
    echo('Version: ' + version)
    echo('Github: ' + __url__ + '\n')

    # TODO: remove in 1.0.0
    if not no_update and check_update():
        cmd = input('Continue without updating?(y/N)')
        if cmd != 'y':
            exit()

    # check argument
    if len(classtypeid) % 3 != 0:
        echoerror('CLASSTYPE and CLASSID should in pair!')
        exit()

    ui = UserInterface()
    if not ui.login(ocr, check_delay):
        exit()
    if print_cookie:
        ui.print_cookie()
    for i in range(0, len(classtypeid), 3):
        ui.add_elect(
            number, classtypeid[i], classtypeid[i + 1], classtypeid[i + 2], delay)
    ui.start_elect()
    cmd = threading.Thread(target=ui.get_input)
    cmd.daemon = True
    cmd.start()
    while ui.check_alive():
        sleep(0.5)
    echo('')
    echoinfo('All task finished!')


if __name__ == '__main__':
    cli()
