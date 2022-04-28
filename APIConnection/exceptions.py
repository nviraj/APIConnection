"""
    Exceptions: custom exceptions for library
"""


class FBException(Exception):
    """
    Wrapper for custom FB library exceptions
    """

    pass


class FBLoginFailed(FBException):
    """
    Unable to login to fb
    """

    pass


class FBTimeOut(FBException):

    pass


class TTDException(Exception):
    pass


class TwitterTimeout(Exception):
    pass


class MissingArgumentException(Exception):
    pass