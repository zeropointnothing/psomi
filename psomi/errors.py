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

class OutOfBoundsError(BaseException):
    """
    The requested resource was out of bounds.
    """
    pass
