from pytest_grader import points


@points(0)
def hof_wwpd():
    """What Would Python Display?

    >>> def cake():
    ...    print('beets')
    ...    def pie():
    ...        print('sweets')
    ...        return 'cake'
    ...    return pie
    >>> chocolate = cake()
    LOCKED: 7afec45eba61631a
    >>> chocolate  # doctest: +ELLIPSIS
    LOCKED: 0143cc1609a02d62
    >>> chocolate()
    LOCKED: 32e92a463c4cba33
    LOCKED: dea7546c99e5a3a2
    >>> more_chocolate, more_cake = chocolate(), cake
    LOCKED: 2929ccfd9db5ded8
    >>> more_chocolate
    LOCKED: c07b79f92ec1c871
    >>> def snake(x, y):
    ...    if cake == more_cake:
    ...        return chocolate
    ...    else:
    ...        return x + y
    >>> snake(10, 20)  # doctest: +ELLIPSIS
    LOCKED: 78e471e3ab9224cd
    >>> snake(10, 20)()
    LOCKED: acd291c4aa8ca25e
    LOCKED: 2711ced6d3b5e393
    >>> cake = 'cake'
    >>> snake(10, 20)
    LOCKED: b220658539aa268e
    """
