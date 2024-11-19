"""Common functionality for converting metadata"""

from typing import Any, BinaryIO, TypeGuard


def is_file_like(the_input: Any) -> TypeGuard[BinaryIO]:
    """
    Verify whether the provided input appear to provide a "file-like object". This
    term is used ubiquitously, but not all usages are identical. In this case, we
    mean that there exist callable attributes `read`, `write`, `seek`, and `tell`.

    Note that this does not check the mode (binary/string or read/write/append),
    as it is not clear that there is any generally accessible way to do so.

    Parameters
    ----------
    the_input

    Returns
    -------
    bool
    """

    out = True
    for attribute in ["read", "write", "seek", "tell"]:
        value = getattr(the_input, attribute, None)
        out &= callable(value)
    return out


def is_real_file(the_input: BinaryIO) -> bool:
    """
    Determine if the file-like object is associated with an actual file.
    This is mainly to consider suitability for establishment of a numpy.memmap.

    Parameters
    ----------
    the_input : BinaryIO

    Returns
    -------
    bool
    """

    if not hasattr(the_input, "fileno"):
        return False
    # noinspection PyBroadException
    try:
        fileno = the_input.fileno()
        return isinstance(fileno, int) and (fileno >= 0)
    except Exception:
        return False
