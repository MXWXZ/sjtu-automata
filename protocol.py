import re
import getpass

import requests
from requests.adapters import HTTPAdapter
from PIL import Image

'''
Call this function to login
return: login session

For security reasons, we will NOT ask or save for your name or password on other places
'''


def Login():
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    # session.verify=False    WARNING! Only use it in Debug mode and add # before this!

    username = input('Username: ')
    password = getpass.getpass('Password(no echo): ')

    # get page
    while True:
        request = session.get('http://electsys.sjtu.edu.cn/edu/login.aspx')
        if '请重新登陆' not in request.text:
            break

    while True:
        captcha_id = re.search(
            r'src="captcha\?([0-9]*)"', request.text).group(1)
        captcha = session.get(
            'https://jaccount.sjtu.edu.cn/jaccount/captcha?'+captcha_id)
        try:
            fp = open('code.png', 'wb')
            fp.write(captcha.content)
            fp.close()
        except:
            print('Captcha save Error!')
            return

        # Because I'm lasy and for user-friendly reasons, no auto captcha feature
        # support.
        img = Image.open('code.png')
        img.show()
        code = input('Input the code: ')

        # login
        sid = re.search(r'sid" value="(.*)"', request.text).group(1)
        returl = re.search(r'returl" value="(.*)"', request.text).group(1)
        se = re.search(r'se" value="(.*)"', request.text).group(1)
        data = {'sid': sid, 'returl': returl, 'se': se, 'user': username,
                'pass': password, 'captcha': code}
        request = session.post(
            'https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)

        # result
        if '请正确填写验证码' in request.text or 'wrong captcha' in request.text:
            print('Wrong captcha! Try again!')
        elif '请正确填写你的用户名和密码' in request.text or 'wrong username or password' in request.text:
            print('Wrong username or password! Try again!')
            username = input('Username: ')
            password = getpass.getpass('Password(no echo): ')
        else:
            print('Login successful!')
            return session


'''
Check elect available
session: login session
xklc: 1 for 1st(INVALID), 2 for 2nd, 3 for 3rd
return: True for available
'''


def CheckAvailable(session, xklc):
    # No use for 1st select
    if xklc == 1:
        return False

    # get param
    request = session.get(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc='+str(xklc))
    viewstate = re.search(
        r'id="__VIEWSTATE" value="(.*)"', request.text).group(1)
    viewstate_generator = re.search(
        r'id="__VIEWSTATEGENERATOR" value="(.*)"', request.text).group(1)
    event_validation = re.search(
        r'id="__EVENTVALIDATION" value="(.*)"', request.text).group(1)

    # post
    data = {'__VIEWSTATE': viewstate, '__VIEWSTATEGENERATOR': viewstate_generator,
            '__EVENTVALIDATION': event_validation, 'CheckBox1': 'on', 'btnContinue': r'%E7%BB%A7%E7%BB%AD'}
    request = session.post(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc='+str(xklc), data=data)
    if '目前该轮选课未开放' in request.text:
        return False
    else:
        return True


if __name__ == '__main__':
    print('Do NOT execute this file!')
