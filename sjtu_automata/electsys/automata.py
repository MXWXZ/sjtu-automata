import html
import re
from time import sleep

import requests
from requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, wait_fixed

from sjtu_automata.__version__ import __url__
from sjtu_automata.utils import get_aspxparam, re_search
from sjtu_automata.utils.exceptions import (AutomataError, ParamError,
                                            RetryRequest, UnhandledStateError)


@retry(retry=retry_if_exception_type(RequestException), wait=wait_fixed(3))
def _request(session, method, url, params=None, data=None, verify=True):
    """Request with params.

    Easy to use requests and auto retry.

    Args:
        session: requests session, login session.
        method: string, 'POST' OR 'GET'.
        url: string, post url.
        params=None: dict, get param.
        data=None: dict, post param.
        verify=True: bool, True to verify returned aspxparam

    Returns:
        requests request.
        dict, aspx param, None if verify is False.

    Raises:
        AutomataError: method param error.
    """
    if method not in ['POST', 'GET'] or not session:
        raise AutomataError

    req = session.request(method, url, params=params, data=data)
    if '过载' in req.text:   # retry when overload error
        raise RetryRequest
    elif '过期' in req.text:
        print('Credential expired! Please relogin!')
        exit()

    if verify:
        return req, get_aspxparam(req.text)
    else:
        return req, None


def check_round(round):
    # round: int, elect round [1,3]
    if round not in [1, 2, 3]:
        raise ParamError
    return round


def check_classtype(classtype):
    # classtype: int, elect class type, [1,4]
    # TODO: Add classtype 5
    if classtype not in [1, 2, 3, 4]:
        raise ParamError
    return classtype


def check_round_available(session, round):
    """Check elect round available.

    You should always call this after login, and you only need to call it once.

    Args:
        session: requests session, login session.
        round: int, elect round, 1 for 1st, 2 for 2nd, 3 for 3rd.

    Returns:
        bool, True for available.
        requests request
        dict, aspx param.

    Raises:
        UnhandledStateError: unhandled page state.
    """
    check_round(round)

    req, data = _request(
        session, 'GET', 'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=%d' % round)
    data['CheckBox1'] = 'on'
    data['btnContinue'] = '继续'

    req, data = _request(session, 'POST',
                         'http://electsys.sjtu.edu.cn/edu/student/elect/electwarning.aspx?xklc=%d' % round, data=data)

    if '目前该轮选课未开放' in req.text or '你目前不能进行该轮选课' in req.text:
        return False, req, None
    elif '推荐课表' in req.text:
        return True, req, data
    else:
        raise UnhandledStateError

# TODO: Add XinShengYanTaoKe support


def _get_classtype_url(classtype):
    # classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
    # TODO: Add classtype 5
    text = ['', 'speltyRequiredCourse.aspx', 'speltyLimitedCourse.aspx',
            'speltyCommonCourse.aspx', 'outSpeltyEP.aspx', '']

    return text[check_classtype(classtype)]


def _get_classtype_fullurl(classtype):
    # classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
    return 'http://electsys.sjtu.edu.cn/edu/student/elect/'+_get_classtype_url(classtype)


def _parse_param(text):
    ret = re_search(r'method="post" action=".*?aspx\?(.*?)"',
                    text)
    if not ret:
        raise ParamError

    ret = html.unescape(ret).replace('%', '\\').encode(
        'utf-8').decode('unicode_escape')
    ret = ret.replace('+', ' ')    # special for fucking 'h1904     '
    return dict(item.split("=") for item in ret.split("&"))


def navpage(session, old_classtype, new_classtype, data):
    """nav from page to page.

    Nav page, auto handle diffrent param.

    Args:
        session: requests session, login session.
        old_classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
        new_classtype: int, new elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
        data: dict, post param with aspx param from last request.

    Returns:
        requests request.
        dict, aspx param.

    Raises:
        ParamError: old_classtype and new_classtype are same.
    """
    if old_classtype == new_classtype:
        raise ParamError
    check_classtype(old_classtype)
    check_classtype(new_classtype)

    # TODO: Add classtype 5
    text_class = ['', '必修课', '限选课', '通识课', '任选课', '新生研讨课']
    text_page = [[],
                 ['', '', 'SpeltyRequiredCourse1$btnXxk', 'SpeltyRequiredCourse1$btnTxk',
                     'SpeltyRequiredCourse1$btnXuanXk', 'SpeltyRequiredCourse1$btnYtk'],
                 ['', 'btnBxk', '', 'btnTxk', 'btnXuanXk', 'btnYtk'],
                 ['', 'btnBxk', 'btnXxk', '', 'btnXuanXk', 'btnYtk'],
                 ['', 'OutSpeltyEP1$btnBxk', 'OutSpeltyEP1$btnXuanXk',
                  'OutSpeltyEP1$btnTxk', '', 'OutSpeltyEP1$btnYtk'],
                 []]

    pass_data = data
    pass_data[text_page[old_classtype]
              [new_classtype]] = text_class[new_classtype]
    if old_classtype in [2, 3]:
        pass_data['__EVENTARGUMENT'] = pass_data['__LASTFOCUS'] = pass_data['__EVENTTARGET'] = ''

    req, data = _request(
        session, 'POST', _get_classtype_fullurl(old_classtype), data=pass_data)

    return req, data


def parse_renxuan(text):
    """Parse RenXuan grade and id.

    Args:
        text: string, page text

    Returns:
        string, id.
        string, grade.
    """
    ret = []
    res = re.finditer(
        r'selected="selected" value="(.*?)"', text, re.S)
    for i in res:
        ret.append(i.group(1))
    return ret[0], ret[1]


def expend_page(session, classtype, classgroup, data, extdata1=None):
    """expand page.

    Show real class info.

    Args:
        session: requests session, login session.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
        classgroup: string, class group string.
        data: dict, post param with aspx param from last request.
        extdata1: string, for RenXuan is grade.

    Returns:
        requests request.
        dict, aspx param.
    """
    check_classtype(classtype)
    pass_data = data
    if classtype in [2, 3]:
        pass_data['__EVENTARGUMENT'] = pass_data['__LASTFOCUS'] = ''
        pass_data['__EVENTTARGET'] = classgroup
        pass_data[classgroup] = 'radioButton'
    if classtype == 4:
        pass_data['OutSpeltyEP1$btnQuery'] = '查 询'
        pass_data['OutSpeltyEP1$dpNj'] = extdata1
        pass_data['OutSpeltyEP1$dpYx'] = classgroup

    req, data = _request(
        session, 'POST', _get_classtype_fullurl(classtype), data=pass_data)
    return req, data


def check_class_selected(text, classid):
    """Check if class is selected.

    Args:
        text: string, request text.
        classid: string, elect class id, e.g. AV001.

    Returns:
        bool, True for selected class. 
    """
    res = re.search(
        r'<input type=radio name=\'myradiogroup\' value='+classid+r'.*?(?:style=")?color(?::)?(?:=")?(.*?)[;"]', text, re.S)
    if res:
        return res.group(1) == 'Blue'
    else:
        return True     # do not elect if meet error


def view_arrange(session, classtype, classgroup, classid, data, extdata1=None):
    """View class arrange page.

    Args:
        session: requests session, login session.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
        classgroup: string, class group string.
        classid: string, elect class id, e.g. AV001.
        data: dict, post param with aspx param from last request.
        extdata1: string, for RenXuan is grade.

    Returns:
        requests request.
        dict, aspx param.
        dict, next get param
    """
    check_classtype(classtype)
    pass_data = data
    pass_data['myradiogroup'] = classid
    if classtype == 1:
        pass_data['SpeltyRequiredCourse1$lessonArrange'] = '课程安排'
    elif classtype in [2, 3]:
        pass_data['__EVENTARGUMENT'] = ''
        pass_data['__LASTFOCUS'] = ''
        pass_data['__EVENTTARGET'] = ''
        pass_data[classgroup] = 'radioButton'
        pass_data['lessonArrange'] = '课程安排'
    elif classtype == 4:
        pass_data['OutSpeltyEP1$lessonArrange'] = '课程安排'
        pass_data['OutSpeltyEP1$dpNj'] = extdata1
        pass_data['OutSpeltyEP1$dpYx'] = classgroup

    req, data = _request(
        session, 'POST', _get_classtype_fullurl(classtype), data=pass_data)
    params = _parse_param(req.text)

    return req, data, params


def check_class_space(text, teacherid):
    """Check if class is full.

    Args:
        text: string, request text.
        teacherid: int, elect teacher id.

    Returns:
        bool, True for class available 

    Raises:
        RetryRequest: not find teacherid.
    """
    ret = re.search(
        r'name=\'myradiogroup\' value='+str(teacherid)+r'.*?(人数.*?)</td>', text, re.S)
    if ret:
        return ret.group(1) == '人数未满'
    else:
        raise RetryRequest


def select_teacher(session, teacherid, data, params):
    """Select teacher.

    WARNING! we will not check if this class is full!
    Please use check_class_full by yourself.

    Args:
        session: requests session, login session.
        teacherid: int, elect teacher id.
        data: dict, view_arrange return post param.
        params: dict, view_arrange return get param.

    Returns:
        requests request.
        dict, post param with aspx param from last request.
        dict, get param from last request.
    """
    pass_data = data
    pass_data['myradiogroup'] = teacherid
    pass_data['LessonTime1$btnChoose'] = '选定此教师'

    req, data = _request(
        session, 'POST', 'http://electsys.sjtu.edu.cn/edu/lesson/viewLessonArrange.aspx', params=params, data=pass_data)
    param = _parse_param(req.text)

    return req, data, param


def submit(session, classtype, data, params, extdata1=None):
    """Submit, need to relogin.

    Args:
        session: requests session, login session.
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.
        data: dict, select_class return post param.
        params: dict, select_class return get param.
        extdata1: string, for RenXuan is grade.

    Returns:
        requests request.
        bool, True for success
    """
    check_classtype(classtype)
    pass_data = data
    if classtype == 1:
        pass_data['SpeltyRequiredCourse1$Button1'] = '选课提交'
    elif classtype in [2, 3]:
        pass_data['__EVENTARGUMENT'] = ''
        pass_data['__LASTFOCUS'] = ''
        pass_data['__EVENTTARGET'] = ''
        pass_data['btnSubmit'] = '选课提交'
    elif classtype == 4:
        pass_data['OutSpeltyEP1$btnSubmit'] = '选课提交'
        pass_data['OutSpeltyEP1$dpNj'] = extdata1
        pass_data['OutSpeltyEP1$dpYx'] = '01000'

    req, data = _request(session, 'POST', _get_classtype_fullurl(
        classtype), params=params, data=pass_data, verify=False)

    # logout
    if '微调结果' in req.text:
        return req, True
    return req, False


def list_group(text, classtype):
    """List class group.

    Args:
        text: string, request text
        classtype: int, elect class type, 1 for BiXiu, 2 for XianXuan, 3 for TongShi, 4 for RenXuan, 5 for XinSheng.

    Returns:
        dict, ret[id]=name
    """
    ret = {}
    if classtype in [2, 3]:
        res = re.finditer(
            r'<input id=".*?" type="radio" name="(.*?)" value="radioButton" .*?<td.*?>(.*?)</td>', text, re.S)
    elif classtype == 4:
        res = re.finditer(
            r'<option value="([0-9]{5,}?)">(.*?)</option>', text, re.S)
    for i in res:
        ret[i.group(1)] = i.group(2).strip()
    return ret


def list_classid(text):
    """List classid.

    Args:
        text: string, request text

    Returns:
        dict, ret[id]=name
    """
    res = re.finditer(
        r'<input type=radio name=\'myradiogroup\' value=(.*?)>.*?<td.*?>(.*?)</td>', text, re.S)
    ret = {}
    for i in res:
        ret[i.group(1).strip()] = i.group(2).strip()
    return ret


def list_teacher(text):
    """List class teacher.

    Args:
        text: string, request text

    Returns:
        dict, ret[id]=name
    """
    res = re.finditer(
        r'name=\'myradiogroup\' value=([0-9]*?)(?: checked)?>.*?<td.*?>(.*?)</td>', text, re.S)
    ret = {}
    for i in res:
        ret[i.group(1)] = i.group(2)
    return ret
