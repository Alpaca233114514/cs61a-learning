from pytest_grader import points


@points(0)
def lambda_wwpd():
    """What Would Python Display?

    >>> lambda x: x  # A lambda expression with one parameter x  # doctest: +ELLIPSIS
    LOCKED: 53c7bab5b4512b4b
    >>> a = lambda x: x  # Assigning the lambda function to the name a
    >>> a(5)
    LOCKED: 1e94432faa19f8ee
    >>> (lambda: 3)()  # Using a lambda expression as an operator in a call expression
    LOCKED: bd95d29bf46358cd
    >>> b = lambda x, y: lambda: x + y  # Lambdas can return other lambdas!
    >>> c = b(8, 4)
    >>> c  # doctest: +ELLIPSIS
    LOCKED: f81fe110f3f6c014
    >>> c()
    LOCKED: 3d59e9406dbe6424
    >>> d = lambda f: f(4)  # They can have functions as arguments as well
    >>> def square(x):
    ...     return x * x
    >>> d(square)
    LOCKED: 521d3d0f9140f9a9

    >>> higher_order_lambda = lambda f: lambda x: f(x)
    >>> g = lambda x: x * x
    >>> higher_order_lambda(g)(2)
    LOCKED: 600f64a5943d0e49
    >>> call_thrice = lambda f: lambda x: f(f(f(x)))
    >>> call_thrice(lambda y: y + 2)(5)
    LOCKED: 017b1dde867f420f
    >>> print_lambda = lambda z: print(z)  # When is the return expression of a lambda expression executed?
    >>> print_lambda  # doctest: +ELLIPSIS
    LOCKED: f872f2b41f292092
    >>> one_thousand = print_lambda(1000)
    LOCKED: 884cca148583550d
    >>> print(one_thousand)  # What did the call to print_lambda return?
    LOCKED: 518c4659eeccc246
    """
