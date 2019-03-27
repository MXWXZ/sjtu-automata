from requests.exceptions import RequestException


class AutomataError(Exception):
    """
    Base exception class.
    """

class RetryRequest(RequestException):
    """
    retry request function.
    """