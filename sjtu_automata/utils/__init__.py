import re
from time import time

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

def get_timestamp():
    """13 lengths timestamp.
    Returns:
        current timestamp.
    """
    return str(round(time() * 1000))