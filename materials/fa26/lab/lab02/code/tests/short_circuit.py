from pytest_grader import points


@points(0)
def short_circuit():
    """What Would Python Display?

    >>> True and 13
    LOCKED: 94781a15be513f8c
    >>> False or 0
    LOCKED: 601ca93c3b2d3336
    >>> not 10
    LOCKED: c18163fdd1c3cc07
    >>> not None
    LOCKED: 6c532d8e3291926f

    >>> True and 1 / 0
    LOCKED: f755aa6285a6cbf9
    >>> True or 1 / 0
    LOCKED: d327d1e29f6ca69a
    >>> -1 and 1 > 0
    LOCKED: 0952ca4c28342a49
    >>> -1 or 5
    LOCKED: fd551e3eddc5af76
    >>> (1 + 1) and 1
    LOCKED: 313cce3e550e4c25
    >>> print(3) or ""
    LOCKED: 2ed8d051da3fa7dd
    LOCKED: 22ec249d903ff858

    >>> def f(x):
    ...     if x == 0:
    ...         return "zero"
    ...     elif x > 0:
    ...         return "positive"
    ...     else:
    ...         return ""
    >>> 0 or f(1)
    LOCKED: fd8ea5d89ef20ff9
    >>> f(0) or f(-1)
    LOCKED: c2346bd7d83f204a
    >>> f(0) and f(-1)
    LOCKED: e3e603bfd9f89970
    """
