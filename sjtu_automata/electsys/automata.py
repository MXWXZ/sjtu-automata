import time
import re
import requests
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed
from urllib.parse import unquote

from sjtu_automata.utils import re_search, get_aspxparam

# WARNING!
# YOU MUST OBEY THE CALL STEP TO AVOID ERROR!

'''
Check elect available
STEP 0

@param      session: login session
@param      round: elect round, 1 for 1st, 2 for 2nd, 3 for 3rd
@return     True for available
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def CheckAvailable(session, round):
    # get param
    request = session.get(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc='+str(round))
    viewstate, viewstate_generator, event_validation = get_aspxparam(
        request.text)

    # post
    data = {'__VIEWSTATE': viewstate, '__VIEWSTATEGENERATOR': viewstate_generator,
            '__EVENTVALIDATION': event_validation, 'CheckBox1': 'on', 'btnContinue': '继续'}
    request = session.post(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc='+str(round), data=data)

    if '目前该轮选课未开放' in request.text or '你目前不能进行该轮选课' in request.text:
        return False
    elif '推荐课表' in request.text:
        return True
    else:
        raise Exception(
            "Unhandled state! Contact us at https://github.com/MXWXZ/AutoElect.\n" + request.text)

# TODO: Add XinShengYanTaoKe support


def _GetClassTypeUrl(classtype):
    if classtype == 1:
        return 'speltyRequiredCourse.aspx'
    elif classtype == 2:
        return 'speltyLimitedCourse.aspx'
    elif classtype == 3:
        return 'speltyCommonCourse.aspx'
    elif classtype == 4:
        return 'outSpeltyEP.aspx'
    else:
        raise Exception('classtype error! Unsupport classtype='+str(classtype))


def _GetClassTypeFullUrl(classtype):
    return 'http://electsys.sjtu.edu.cn/edu/student/elect/'+_GetClassTypeUrl(classtype)


def _GetPostParam(text):
    ret = {}
    ret['__VIEWSTATE'], ret['__VIEWSTATEGENERATOR'], ret['__EVENTVALIDATION'] = get_aspxparam(
        text)
    return ret


def _GetGetParam(text):

    ret = re_search(r'method="post" action=".*?aspx\?(.*?)"',
                    text).replace('&amp;', '&')
    if not ret:
        raise RequestException
    return dict(item.split("=") for item in ret.split("&"))


def _GetNextParam(text):
    return _GetPostParam(text), _GetGetParam(text)


'''
View class type page
STEP 1

@param      session: login session
@param      round: elect round, 1 for 1st, 2 for 2nd, 3 for 3rd
@param      classtype: elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan
@return     POST param for next step
            page text
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def ViewPage(session, round, classtype):
    request = session.get(_GetClassTypeFullUrl(classtype))
    if '过载' in request.text:   # may cause error
        raise RequestException

    return _GetPostParam(request.text),request.text


'''
View class type page
STEP 2

@param      session: login session
@param      round: elect round, MUST BE SAME AS ViewPage
@param      classtype: elect class type, MUST BE SAME AS ViewPage
@param      classid: elect class id, e.g. AV001
@param      postparam: ViewPage return post param
@return     POST param for next step
            GET param for next step
            page text
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def ViewArrange(session, round, classtype, classid, postparam):
    postparam['myradiogroup'] = classid
    if classtype == 1:
        postparam['SpeltyRequiredCourse1$lessonArrange'] = '课程安排'
    request = session.post(_GetClassTypeFullUrl(classtype), data=postparam)
    if '过载' in request.text:   # may cause error
        raise RequestException

    ret1, ret2 = _GetNextParam(request.text)
    # Don't delete these code, or you will fucking waste 2 hours
    # you must transfer the encoding manually here
    # or the submit check WILL BE failed!
    if classtype == 1:
        ret2['xklx'] = '必修'
    elif classtype == 2:
        ret2['xklx'] = '限选'
    elif classtype == 3:
        ret2['xklx'] = '通识'
    elif classtype == 4:
        ret2['xklx'] = '通选'
    else:
        raise Exception('classtype error! Unsupport classtype='+str(classtype))
    return ret1, ret2, request.text


'''
Select lesson
Step 3

@param      session: login session
@param      round: elect round, MUST BE SAME AS ViewPage
@param      teacherid: elect teacher id
@param      postparam: ViewArrange return post param
@param      getparam: ViewArrange return get param
@return     POST param for next step
            GET param for next step
            page text
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def SelectLesson(session, round, teacherid, postparam, getparam):
    postparam['myradiogroup'] = teacherid
    postparam['LessonTime1$btnChoose'] = '选定此教师'

    request = session.post(
        'http://electsys.sjtu.edu.cn/edu/lesson/viewLessonArrange.aspx', params=getparam, data=postparam)
    if '过载' in request.text:   # may cause error
        raise RequestException

    return _GetNextParam(request.text)+request.text


'''
Submit, need to relogin
Step 4

@param      session: login session
@param      round: elect round, MUST BE SAME AS ViewPage
@param      classtype: elect class type, MUST BE SAME AS ViewPage
@param      postparam: SelectLesson return post param
@param      getparam: SelectLesson return get param
@return     page text
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def Submit(session, round, classtype, postparam, getparam):
    postparam['SpeltyRequiredCourse1$Button1'] = '选课提交'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'}
    request = session.post(_GetClassTypeFullUrl(classtype),
                           params=getparam, data=postparam, headers=headers)
    if '过载' in request.text:   # may cause error
        raise RequestException
    # logout
    return request.text


'''
Elect lesson interface, need to relogin after this
@param      session: login session
@param      round: elect round, 1 for 1st, 2 for 2nd, 3 for 3rd
@param      classtype: elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan
@param      classid: elect class id, e.g. AV001
@param      teacherid: elect teacher id
'''


def ElectLesson(session, round, classtype, classid, teacherid):
    postparam, text = ViewPage(session, round, classtype)
    postparam, getparam, text = ViewArrange(
        session, round, classtype, classid, postparam)
    time.sleep(2)   # seems query time check, just wait a while...
    postparam, getparam, text = SelectLesson(
        session, round, teacherid, postparam, getparam)
    Submit(session, round, classtype, postparam, getparam)



'''
List class teacher
STEP 1

@param      session: login session
@param      round: elect round, 1 for 1st, 2 for 2nd, 3 for 3rd
@param      classtype: elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan
@param      classid: elect class id, e.g. AV001
@return     teacher-id dict
'''


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def ListTeacher(session, round, classtype, classid):
    postparam,text = ViewPage(session, round, classtype)
    postparam,getparam,text=ViewArrange(session,round,classtype,classid,postparam)
    res=re.finditer(r'name=\'myradiogroup\' value=([0-9]*?)>.*?<td.*?>(.*?)</td>',text,re.S)    # requests response is differen with browser
    ret={}
    for i in res:
        ret[i.group(1)]=i.group(2)
    return ret