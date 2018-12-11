import re
import requests
from requests.adapters import HTTPAdapter
from PIL import Image
from .autocaptcha import GetCode

'''
Call this function to login
Captcha picture will be stored in code.png

@param      url: direct login url
@param      username: login username
@param      password: login password
@param      useocr=False: True to use ocr to autofill captcha
@return     login session, None for wrong login
'''


def Login(url, username, password, useocr=False):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    # session.verify=False    WARNING! Only use it in Debug mode!

    # get page
    while True:
        request = session.get(url)
        if '<form id="form-input" method="post" action="ulogin">' in request.text:    # if last login exists, it will go to error page. so ignore it
            break

    while True:
        captcha_id = re.search(
            r'src="captcha\?([0-9]*)"', request.text).group(1)
        captcha = session.get(
            'https://jaccount.sjtu.edu.cn/jaccount/captcha?'+captcha_id)

        fp = open('captcha.jpeg', 'wb')
        fp.write(captcha.content)
        fp.close()

        if useocr:
            code = GetCode('captcha.jpeg')
            if not code.isalpha():
                code = '1234'   # cant recongnize, go for next round
        else:
            img = Image.open('captcha.jpeg')
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
        # be careful return english version website in english OS
        if '请正确填写验证码' in request.text or 'wrong captcha' in request.text:
            if not useocr:
                print('Wrong captcha! Try again!')
        elif '请正确填写你的用户名和密码' in request.text or 'wrong username or password' in request.text:
            return None
        elif 'frame src="../newsboard/newsinside.aspx"':
            print('Login successful!')
            return session
        else:
            raise Exception("Unhandled state! Contact us at https://github.com/MXWXZ/AutoElect.\n" + request.text)
