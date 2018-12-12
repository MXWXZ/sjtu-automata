import re
from requests.exceptions import RequestException


def re_search(retext, text):
    tmp = re.search(retext, text)
    if tmp:
        return tmp.group(1)
    else:
        return None


def get_aspxparam(text):
    state = re_search(r'id="__VIEWSTATE" value="(.*?)"', text)
    generator = re_search(r'id="__VIEWSTATEGENERATOR" value="(.*?)"', text)
    validation = re_search(r'id="__EVENTVALIDATION" value="(.*?)"', text)
    if not (state and generator and validation):
        raise RequestException
    return state, generator, validation
