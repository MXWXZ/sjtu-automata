from requests.exceptions import RequestException


class AutomataError(Exception):
    """
    Base exception class.
    """


class ParamError(AutomataError):
    """
    Param not correct.
    """


class PageLoadError(AutomataError, RequestException):
    """
    Loaded page is not expected.
    """

class UnhandledStateError(AutomataError, RequestException):
    """
    Unhandled page state.
    """

class RetryRequest(RequestException):
    """
    retry request function.
    """