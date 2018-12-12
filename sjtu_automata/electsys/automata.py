import re
import time

import requests
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed

from sjtu_automata.__version__ import __url__
from sjtu_automata.utils import get_aspxparam, re_search
from sjtu_automata.utils.exceptions import ParamError, UnhandledStateError, RetryRequest

# WARNING!
# YOU MUST OBEY THE CALL STEP TO AVOID ERROR!


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def check_round(session, round):
    """Check elect round available.

    STEP 0 [ONCE]
    You should always call this after login, and you only need to call it once.

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.

    Returns:
        bool, True for available
    """
    req = session.get(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=%d' % round)

    data = get_aspxparam(req.text)
    data['CheckBox1'] = 'on'
    data['btnContinue'] = '继续'
    req = session.post(
        'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=%d' % round, data=data)

    if '目前该轮选课未开放' in req.text or '你目前不能进行该轮选课' in req.text:
        return False
    elif '推荐课表' in req.text:
        return True
    else:
        raise UnhandledStateError

# TODO: Add XinShengYanTaoKe support


def _check_classtype(classtype):
    # classtype: int, elect class type, [1,4]
    if classtype in [1, 2, 3, 4]:
        return classtype
    else:
        raise ParamError('Unsupport param: classtype=%d' % classtype)


def _get_classtype_url(classtype):
    # classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
    text = ['', 'speltyRequiredCourse.aspx', 'speltyLimitedCourse.aspx',
            'speltyCommonCourse.aspx', 'outSpeltyEP.aspx']

    return text[_check_classtype(classtype)]


def _get_classtype_fullurl(classtype):
    # classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
    return 'http://electsys.sjtu.edu.cn/edu/student/elect/'+_get_classtype_url(classtype)


def _get_get_param(text):
    ret = re_search(r'method="post" action=".*?aspx\?(.*?)"',
                    text).replace('&amp;', '&')
    if not ret:
        raise ParamError
    return dict(item.split("=") for item in ret.split("&"))


def _get_next_param(text):
    return get_aspxparam(text), _get_get_param(text)


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def view_page(session, round, classtype):
    """View classtype page.

    STEP 1

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.

    Returns:
        dict, post param for next step.
        string, page text.
    """
    req = session.get(_get_classtype_fullurl(classtype))
    if '过载' in req.text:   # retry when overload error
        raise RetryRequest

    return get_aspxparam(req.text), req.text


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def view_arrange(session, round, classtype, classid, postparam):
    """View class arrange page.

    STEP 2

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
        classid: string, elect class id, e.g. AV001.
        postparam: dict, view_page return post param.

    Returns:
        dict, post param for next step.
        dict, get param for next step.
        string, page text.
    """
    data = postparam
    data['myradiogroup'] = classid
    if classtype == 1:
        data['SpeltyRequiredCourse1$lessonArrange'] = '课程安排'
    req = session.post(_get_classtype_fullurl(classtype), data=data)
    if '过载' in req.text:   # retry when overload error
        raise RetryRequest

    ret1, ret2 = _get_next_param(req.text)

    # Don't delete these code, or you will waste fucking 2 hours
    # you must transfer the encoding manually here
    # or the submit check WILL BE failed!
    text = ['', '必修', '限选', '通识', '通选']
    ret2['xklx'] = text[_check_classtype(classtype)]

    return ret1, ret2, req.text


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def select_class(session, round, teacherid, postparam, getparam):
    """Select lesson.

    Step 3

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        teacherid: int, elect teacher id.
        postparam: dict, view_arrange return post param.
        getparam: dict, view_arrange return get param.

    Returns:
        dict, post param for next step.
        dict, get param for next step.
        string, page text.
    """
    data = postparam
    data['myradiogroup'] = teacherid
    data['LessonTime1$btnChoose'] = '选定此教师'

    req = session.post(
        'http://electsys.sjtu.edu.cn/edu/lesson/viewLessonArrange.aspx', params=getparam, data=data)
    if '过载' in req.text:   # retry when overload error
        raise RetryRequest

    ret1, ret2 = _get_next_param(req.text)
    return ret1, ret2, req.text


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def submit(session, round, classtype, postparam, getparam):
    """Submit, need to relogin.

    Step 4

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
        postparam: dict, select_class return post param.
        getparam: dict, select_class return get param.

    Returns:
        string, page text.
    """
    data = postparam
    data['SpeltyRequiredCourse1$Button1'] = '选课提交'

    req = session.post(_get_classtype_fullurl(
        classtype), params=getparam, data=data)
    if '过载' in req.text:   # retry when overload error
        raise RetryRequest
    # logout
    return req.text


def elect_lesson(session, round, classtype, classid, teacherid):
    """Elect lesson interface, need to relogin after this.

    Simplified API, not support progress.

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
        classid: string, elect class id, e.g. AV001.
        teacherid: int, elect teacher id.
    """
    postparam, text = view_page(session, round, classtype)
    postparam, getparam, text = view_arrange(
        session, round, classtype, classid, postparam)
    time.sleep(2)   # seems query time check, lets have a rest...
    postparam, getparam, text = select_class(
        session, round, teacherid, postparam, getparam)
    submit(session, round, classtype, postparam, getparam)


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def list_teacher(session, round, classtype, classid):
    """List class teacher.

    STEP 1

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan.
        classid: string, elect class id, e.g. AV001.

    Returns:
        dict, ret[id]=name
    """
    postparam, text = view_page(session, round, classtype)
    postparam, getparam, text = view_arrange(
        session, round, classtype, classid, postparam)

    # requests response is different with browser
    res = re.finditer(
        r'name=\'myradiogroup\' value=([0-9]*?)>.*?<td.*?>(.*?)</td>', text, re.S)
    ret = {}
    for i in res:
        ret[i.group(1)] = i.group(2)
    return ret
