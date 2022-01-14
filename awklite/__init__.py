# awklite -- a little library to aid writing AWK-style scripts
#
# Copyright (C) 2022 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Awklite is a tiny support library to assist in writing AWK-style
scripts in Python. There are several features:

  * a specialised version of 'list', used for holding fields of a
    line, that can be indexed from one and not zero. In AWK, the first
    field is $1. A simple example:

        >>> f = Fields("1.0 2 three".split())
        >>> f[1], f[2], f[3]
        (1.0, 2, 'three')

  * a Namespace class that returns an Undefined type (see below) for
    variables that are not attributes of the object. This mimics AWK's
    behaviour of giving undefined variables a null value, eg:

        >>> a = Namespace()
        >>> a.foo = 10
        >>> a.foo
        10
        >>> int(a.bar)
        0

  * a new Undefined type, which mimics an undefined variable in
    AWK. This variable is 0 in an integer context, 0.0 in a float
    context, and the empty string in a string context. As soon as the
    variable is overwritten with a value, it is no longer undefined.
    Some examples to demonstrate the semantics:

        >>> ud = Undefined()
        >>> int(ud), float(ud), str(ud)
        (0, 0.0, '')
        >>> ud + 1, ud + 1.1, ud + 'hello'
        (1, 1.1, 'hello')
        >>> ud > 0
        False
        >>> ud += 1
        >>> ud
        1
"""


class Fields(list):
    """A list which uses one-based indexing."""
    def __getitem__(self, key):
        assert 0 < key <= len(self)
        return list.__getitem__(self, key - 1)


class Undefined():
    """An undefined object mimics an undefined variable in AWK."""
    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __str__(self):
        return ""

    def __add__(self, other):
        return other

    def __gt__(self, other):
        return False


class Namespace():
    """An object that returns an Undefined for undefined attributes."""

    def __getattr__(self, name):
        try:
            return super.__getattr__(self, name)
        except AttributeError:
            return Undefined()

    def clear(self):
        """Clear all variables."""
        self.__dict__.clear()
