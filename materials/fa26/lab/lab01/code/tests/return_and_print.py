from pytest_grader import points


@points(0)
def return_and_print():
    """What Would Python Display?

    >>> def welcome():
    ...     print('Go')
    ...     return 'hello'
    ...
    >>> def cal():
    ...     print('Bears')
    ...     return 'world'
    ...
    >>> welcome()
    LOCKED: 3bdedbc8526767b1
    LOCKED: 56802e347b6f1f20
    >>> print(welcome(), cal())
    LOCKED: 71e5e96add40aad3
    LOCKED: 24d2655a5849bd2c
    LOCKED: 175f96f77d946a91
    """
