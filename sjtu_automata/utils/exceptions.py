from requests.exceptions import RequestException


class AutomataError(Exception):
    """
    Base exception class.
    """


class ParamError(AutomataError):
    """
    Param not correct.
    """

class UnhandledStateError(AutomataError):
    """
    Unhandled page state.
    """

class RetryRequest(RequestException):
    """
    retry request function.
    """