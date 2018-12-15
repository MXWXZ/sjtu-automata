from time import sleep

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed

from sjtu_automata.autocaptcha import autocaptcha
from sjtu_automata.utils import re_search
from sjtu_automata.utils.exceptions import (RetryRequest,
                                            UnhandledStateError)


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
def _login(session, sid, returl, se, username, password, code):
    # return 0 suc, 1 wrong credential, 2 code error, 3 30s ban
    data = {'sid': sid, 'returl': returl, 'se': se, 'user': username,
            'pass': password, 'captcha': code,'v':''}
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
    elif 'frame src="../newsboard/newsinside.aspx"':
        return 0
    else:
        raise UnhandledStateError


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def login(url, username, password, useocr=False):
    """Call this function to login.

    Captcha picture will be stored in captcha.jpeg.

    Args:
        url: string, direct login url
        username: string, login username
        password: string, login password
        useocr=False: bool, True to use ocr to autofill captcha

    Returns:
        requests session, login session, None for wrong login
    """
    session = _create_session()
    req = _get_login_page(session, url)

    captcha_id = re_search(r'src="captcha\?([0-9]*)"', req)
    if not captcha_id:
        raise RetryRequest
    url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?'+captcha_id
    code = _bypass_captcha(session, url, useocr)

    sid = re_search(r'sid" value="(.*?)"', req)
    returl = re_search(r'returl" value="(.*?)"', req)
    se = re_search(r'se" value="(.*?)"', req)
    if not (sid and returl and se):
        raise RetryRequest
    res = _login(session, sid, returl, se, username, password, code)

    if res == 2:
        if not useocr:
            print('Wrong captcha! Try again!')
        raise RetryRequest
    elif res == 1:
        return None
    elif res == 3:
        print('Opps! You are banned for 30s...Waiting...')
        sleep(30)
        raise RetryRequest
    else:
        return session
