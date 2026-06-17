from time import sleep
from time import time
from getpass import getpass
import re

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
    session.headers = {'Referer':'https://jaccount.sjtu.edu.cn'}
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    # session.verify = False    # WARNING! Only use it in Debug mode!
    return session


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _get_login_page(session, url):
    # return page text
    req = session.get(url)
    # if last login exists, it will go to error page. so ignore it
    if 'login-form' in req.text:
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
        code = autocaptcha('captcha.jpeg').strip()
        # SJTU captcha is 4 alphanumeric chars (letters + digits)
        if not code or len(code) < 4:
            code = '1234'   # cant recognize, go for next round
    else:
        img = Image.open('captcha.jpeg')
        img.show()
        code = input('Input the code(captcha.jpeg): ')

    return code


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _login(session, sid, returl, se, client, username, password, code, uuid):
    # return 0 suc, 1 wrong credential, 2 code error, 3 30s ban
    data = {'sid': sid, 'returl': returl, 'se': se, 'client': client, 'user': username,
            'pass': password, 'captcha': code, 'v': '', 'uuid': uuid, 'lt': 'p'}
    req = session.post(
        'https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)

    # Try JSON response first (new JAccount API format)
    try:
        result = req.json()
        errno = result.get('errno', -1)
        error_code = result.get('code', '')
        error_msg = result.get('error', '')

        if errno == 0:
            # Follow redirect URL to complete auth cookie setup
            redirect_url = result.get('url', '')
            if redirect_url:
                # JAccount may return relative URL, make it absolute
                if not redirect_url.startswith('http'):
                    redirect_url = 'https://jaccount.sjtu.edu.cn' + redirect_url
                try:
                    session.get(redirect_url)
                except RequestException:
                    pass  # redirect failed but login POST succeeded, cookies are already set
            return 0  # login success
        if error_code == 'WRONG_CAPTCHA' or '验证码' in error_msg:
            return 2  # wrong captcha
        if error_code == 'WRONG_CREDENTIAL' or '用户名' in error_msg or '密码' in error_msg:
            return 1  # wrong credential
        # fallback: check errno for other known errors
        if errno == 1:
            return 1
        raise AutomataError(f'Unexpected JSON response: {result}')
    except ValueError:
        pass  # not JSON, fallback to legacy HTML parsing

    # Legacy HTML-based detection (fallback)
    if '请正确填写验证码' in req.text or 'wrong captcha' in req.text:
        return 2
    elif '请正确填写你的用户名和密码' in req.text or 'wrong username or password' in req.text:
        return 1
    elif '30秒后' in req.text:  # 30s ban
        return 3
    elif '<i class="fa fa-gear" aria-hidden="true" id="wdyy_szbtn">' in req.text:
        return 0

    # Dump full response for debugging new JAccount page structure
    with open('jaccount_response.html', 'w', encoding='utf-8') as f:
        f.write(req.text)
    print('[Debug] Full response written to jaccount_response.html')

    # Check for common error indicators in newer JAccount pages
    if 'errno' in req.text or 'error' in req.text:
        err_match = re.search(r'"error"\s*:\s*"([^"]+)"', req.text)
        if err_match:
            raise AutomataError(f'JAccount error: {err_match.group(1)}')
    if 'login-form' in req.text or 'login-card' in req.text or 'SJTU Single Sign On' in req.text:
        # Returned to login page — likely captcha error, but could be wrong password.
        # Return 2 to retry captcha; if it loops forever, the password is probably wrong.
        print('[Debug] Returned to login page, retrying with new captcha...')
        return 2
    raise AutomataError(f'Unexpected response. Full HTML saved to jaccount_response.html. First 500 chars: {req.text[:500]}')


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

            # Extract all params first, before constructing captcha URL
            sid = re_search(r'sid: "(.*?)"', req)
            returl = re_search(r'returl:"(.*?)"', req)
            se = re_search(r'se: "(.*?)"', req)
            client = re_search(r'client: "(.*?)"', req)
            uuid = re_search(r'captcha\?uuid=(.*?)&t=', req)
            if not (sid and returl and se and uuid):
                print('Params not found! Retrying...')
                sleep(3)
                continue

            # Construct captcha URL with fresh timestamp (replace, not append)
            captcha_url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?uuid=' + uuid + '&t=' + get_timestamp()
            code = _bypass_captcha(session, captcha_url, useocr)

            res = _login(session, sid, returl, se, client,
                         username, password, code, uuid)

            if res == 2:
                print('Wrong captcha! Retrying...')
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
