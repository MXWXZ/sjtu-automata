import requests
from time import sleep
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed
from PIL import Image
from .utils import re_search
from .autocaptcha import GetCode


def _CreateSession():
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    session.verify=False    # WARNING! Only use it in Debug mode!
    return session

# return page text


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _GetLoginPage(session, url):
    request = session.get(url)
    # if last login exists, it will go to error page. so ignore it
    if '<form id="form-input" method="post" action="ulogin">' in request.text:
        return request.text
    else:
        raise RequestException  # make it retry

# return captcha code


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _BypassCaptcha(session, url, useocr):
    captcha = session.get(url)
    with open('captcha.jpeg', 'wb') as f:
        f.write(captcha.content)

    if useocr:
        code = GetCode('captcha.jpeg')
        if not code.isalpha():
            code = '1234'   # cant recongnize, go for next round
    else:
        img = Image.open('captcha.jpeg')
        img.show()
        code = input('Input the code(captcha.jpeg): ')

    return code

# return 0 suc, 1 wrong credential, 2 code error, 3 30s ban


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _Login(session, sid, returl, se, username, password, code):
    data = {'sid': sid, 'returl': returl, 'se': se, 'user': username,
            'pass': password, 'captcha': code}
    request = session.post(
        'https://jaccount.sjtu.edu.cn/jaccount/ulogin', data=data)

    # result
    # be careful return english version website in english OS
    if '请正确填写验证码' in request.text or 'wrong captcha' in request.text:
        return 2
    elif '请正确填写你的用户名和密码' in request.text or 'wrong username or password' in request.text:
        return 1
    elif '30秒后' in request.text:  # 30s ban
        return 3
    elif 'frame src="../newsboard/newsinside.aspx"':
        return 0
    else:
        raise Exception(
            "Unhandled state! Contact us at https://github.com/MXWXZ/AutoElect.\n" + request.text)


'''
Call this function to login
Captcha picture will be stored in captcha.jpeg

@param      url: direct login url
@param      username: login username
@param      password: login password
@param      useocr=False: True to use ocr to autofill captcha
@return     login session, None for wrong login
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def Login(url, username, password, useocr=False):
    session = _CreateSession()
    request = _GetLoginPage(session, url)

    captcha_id = re_search(r'src="captcha\?([0-9]*)"', request)
    if not captcha_id:
        raise RequestException
    url = 'https://jaccount.sjtu.edu.cn/jaccount/captcha?'+captcha_id
    code = _BypassCaptcha(session, url, useocr)

    sid = re_search(r'sid" value="(.*?)"', request)
    returl = re_search(r'returl" value="(.*?)"', request)
    se = re_search(r'se" value="(.*?)"', request)
    if not (sid and returl and se):
        raise RequestException
    res = _Login(session, sid, returl, se, username, password, code)

    if res == 2:
        if not useocr:
            print('Wrong captcha! Try again!')
        raise RequestException
    elif res == 1:
        return None
    elif res == 3:
        print('Opps! You are banned for 30s...Waiting...')
        sleep(30)
        raise RequestException
    else:
        return session
