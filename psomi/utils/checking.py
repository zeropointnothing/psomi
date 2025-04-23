import types as typ
from inspect import getfullargspec
from typing import get_args

def enforce_annotations(func):
    """
    Decorator to enforce type annotations.

    :param func: The function to check.
    :raises TypeError: If any arguments do not match their annotations.
    """
    def wrapper(*args, **kwargs):
        annotations = getfullargspec(func).annotations
        # we don't need the return annotation
        try:
            del annotations["return"]
        except KeyError:
            pass
        types = list(annotations.values())

        for i, arg in enumerate(args[1:]) if "." in func.__qualname__ else enumerate(args):
            if arg == "return": # we don't need to check the return value or self
                continue

            # check for UnionTypes
            if isinstance(types[i], typ.UnionType):
                expected = [_.__name__ for _ in get_args(types[i])]
            else:
                expected = [types[i].__name__]

            # expected = types[i].__name__
            got = arg.__class__.__name__
            arg_for = list(annotations.keys())[i]

            if got not in expected:
                raise TypeError(f"Function '{func.__name__}'"
                f" received invalid argument type of '{got}' for arg '{arg_for}'. (expected '{" | ".join(expected)}')")
        for i, kwarg in enumerate(kwargs, start=len(args)):
            if kwarg == "return":
                continue

            if isinstance(annotations[kwarg], typ.UnionType):
                expected = [_.__name__ for _ in get_args(annotations[kwarg])]
            else:
                expected = [annotations[kwarg].__name__]

            # expected = annotations[kwarg].__name__
            got = kwargs[kwarg].__class__.__name__
            arg_for = kwarg

            if got not in expected:
                raise TypeError(f"Function '{func.__name__}'"
                f" received invalid argument type of '{got}' for kwarg '{arg_for}'. (expected '{" | ".join(expected)}')")

        return func(*args, **kwargs)
    return wrapper