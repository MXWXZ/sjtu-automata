import getopt
import sys

from protocol import *


class UserInterface:
    def __init__(self):
        self.xklc = 1    # 1 for 1st(INVALID), 2 for 2nd, 3 for 3rd
        self.session = None  # login session

    def ShowHelp(self):
        print('Usage: python autoelect.py [-OPTIONS]\n')
        print('  -h, --help     show this help')
        print('  -r, --rob      2nd elect')
        print('      --fish     3rd elect')

    def SolveParam(self, argv):
        if not argv:
            print(
                'Usage: python autoelect.py [-OPTIONS]\nUse "python autoelect.py -h" for help.')
            exit()
        try:
            opts, argvs = getopt.getopt(argv, 'hr', ['help', 'rob', 'fish'])
        except getopt.GetoptError:
            print('Invalid param!\nUse "python autoelect.py -h" for help.')
            exit(1)

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.ShowHelp()
                exit()
            elif opt in ('-r', '--rob'):
                self.xklc = 2
            elif opt == '--fish':
                self.xklc = 3

        # check
        if self.xklc == 1:
            print('Please select mode(-r/--fish)!')
            exit()

    def Login(self):
        self.session = Login()

    def CheckAvailable(self):
        return CheckAvailable(self.session, self.xklc)


def main():
    try:
        ui = UserInterface()
        ui.SolveParam(sys.argv[1:])
        ui.Login()
        print(ui.CheckAvailable())
    except:
        print('Network Error! Try again!')
        exit()


if __name__ == '__main__':
    main()
