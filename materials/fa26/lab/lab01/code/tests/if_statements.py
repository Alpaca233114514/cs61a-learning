from pytest_grader import points


@points(0)
def if_statements():
    """What Would Python Display?

    >>> def ab(c, d):
    ...     if c > 5:
    ...         print(c)
    ...     elif c > 7:
    ...         print(d)
    ...     print('foo')
    >>> ab(10, 20)
    LOCKED: 51e6685f805f3f85
    LOCKED: 0541db8aa7dab674
    >>> def bake(cake, make):
    ...     if cake == 0:
    ...         cake = cake + 1
    ...         print(cake)
    ...     if cake == 1:
    ...         print(make)
    ...     else:
    ...         return cake
    ...     return make
    >>> bake(0, 5)
    LOCKED: 35882b5ca37594e9
    LOCKED: 322e9727c3d8b467
    LOCKED: 978aada1b577a1b2
    >>> bake(1, "yum")
    LOCKED: 69ee7dd8947c9363
    LOCKED: 8404ec5c567f7039
    >>> bake(2, 3)
    LOCKED: 9a83be243dd3daad
    """
