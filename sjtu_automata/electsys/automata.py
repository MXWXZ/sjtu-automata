import re
import requests

'''
Check elect available
session: login session
xklc: 1 for 1st, 2 for 2nd, 3 for 3rd
return: True for available
'''


def CheckAvailable(session, xklc):
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

    if '目前该轮选课未开放' in request.text or '你目前不能进行该轮选课' in request.text:
        return False
    elif '推荐课表' in request.text:
        return True
    else:
        raise Exception("Unhandled state! Contact us at https://github.com/MXWXZ/AutoElect.\n" + request.text)
