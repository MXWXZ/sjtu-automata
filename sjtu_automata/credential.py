from time import sleep
from time import time
from getpass import getpass

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed

from sjtu_automata.autocaptcha import autocaptcha
from sjtu_automata.utils import (re_search, get_timestamp)
from sjtu_automata.utils.exceptions import (RetryRequest, AutomataError)


def _create_session():
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    # session.verify = False    # WARNING! Only use it in Debug mode!
    return session


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _get_login_page(session, url):
    # return page text
    req = session.get(url)
    # if last login exists, it will go to error page. so ignore it
    if '<form id="form-input" method="post" action="ulogin">' in req.text:
        return req.text
    else:
        raise RetryRequest  # make it retry


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _bypass_captcha(session, url, useocr):
    # return captcha code
    captcha = session.get(url)
    with open('captcha.jpeg', 'wb') as f:
        f.write(captcha.content)

    if useocr:
        code = autocaptcha('captcha.jpeg')
        if not code.isalpha():
            code = '1234'   # cant recongnize, go for next round
    else:
        img = Image.open('captcha.jpeg')
        img.show()
        code = input('Input the code(captcha.jpeg): ')

    return code


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _login(session, sid, returl, se, client, username, password, code, uuid):
    # return 0 suc, 1 wrong credential, 2 code error, 3 30s ban
    data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
            'pass': password, 'captcha': code, 'v': '', 'uuid': uuid}
    req = session.post(
        'https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)

    # result
    # be careful return english version website in english OS
    if '请正确填写验证码' in req.text or 'wrong captcha' in req.text:
        return 2
    elif '请正确填写你的用户名和密码' in req.text or 'wrong username or password' in req.text:
        return 1
    elif '30秒后' in req.text:  # 30s ban
        return 3
    elif '<i class="fa fa-gear" aria-hidden="true" id="wdyy_szbtn">':
        return 0
    else:
        raise AutomataError


def login(url, useocr=False):
    """Call this function to login.

    Captcha picture will be stored in captcha.jpeg.
    WARNING: From 0.2.0, username and password will not be allowed to pass as params, all done by this function itself.

    Args:
        url: string, direct login url
        useocr=False: bool, True to use ocr to autofill captcha

    Returns:
        requests login session.
    """
    while True:
        username = input('Username: ')
        password = getpass('Password(no echo): ')

        while True:
            session = _create_session()
            req = _get_login_page(session, url)
            captcha_id = re_search(r'img.src = \'captcha\?(.*)\'', req)
            if not captcha_id:
                print('Captcha not found! Retrying...')
                sleep(3)
                continue
            captcha_id += get_timestamp()
            captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?' + captcha_id
            code = _bypass_captcha(session, captcha_url, useocr)

            sid = re_search(r'sid" value="(.*?)"', req)
            returl = re_search(r'returl" value="(.*?)"', req)
            se = re_search(r'se" value="(.*?)"', req)
            client = re_search(r'client" value="(.*?)"', req)
            uuid = re_search(r'captcha\?uuid=(.*?)&t=', req)
            if not (sid and returl and se and uuid):
                print('Params not found! Retrying...')
                sleep(3)
                continue

            res = _login(session, sid, returl, se, client,
                         username, password, code, uuid)

            if res == 2:
                if not useocr:
                    print('Wrong captcha! Try again!')
                continue
            elif res == 1:
                print('Wrong username or password! Try again!')
                break
            elif res == 3:
                print('Opps! You are banned for 30s...Waiting...')
                sleep(30)
                continue
            else:
                return session
