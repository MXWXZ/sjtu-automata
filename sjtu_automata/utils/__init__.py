import re
from sjtu_automata.utils.exceptions import RetryRequest


def re_search(retext, text):
    """Regular expression search.

    Prevent exception when re.search cant find one,
    Only returns the first group.

    Args:
        retext: string, regular expression.
        text: string, text want to search.

    Returns:
        string, the matched group, None when not find.
    """
    tmp = re.search(retext, text)
    if tmp:
        return tmp.group(1)
    else:
        return None


def get_aspxparam(text):
    """Get aspx view param.

    Split __VIEWSTATE/__VIEWSTATEGENERATOR/__EVENTVALIDATION from text.

    Args:
        text: string, text want to split.

    Returns:
        dict, 3 params and values.

    Raises:
        RetryRequest: cant find at least one of aspx param in page text.
    """
    ret = {}
    ret['__VIEWSTATE'] = re_search(r'id="__VIEWSTATE" value="(.*?)"', text)
    ret['__VIEWSTATEGENERATOR'] = re_search(
        r'id="__VIEWSTATEGENERATOR" value="(.*?)"', text)
    ret['__EVENTVALIDATION'] = re_search(
        r'id="__EVENTVALIDATION" value="(.*?)"', text)
    for key, value in ret.items():
        if not value:
            raise RetryRequest
    return ret
