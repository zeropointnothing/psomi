class DuplicateError(BaseException):
    """
    The resource already exists.
    """
    pass

class NotFoundError(BaseException):
    """
    The requested resource could not be found.
    """
    pass