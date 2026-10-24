"""Homework 1: Functions."""
def square(x):
    
from operator import add, sub
# 使用add sub函数，伏笔这一块

def a_plus_abs_b(a, b):
    """Return a+abs(b), but without calling abs.

    >>> a_plus_abs_b(2, 3)
    5
    >>> a_plus_abs_b(2, -3)
    5
    >>> a_plus_abs_b(-1, 4)
    3
    >>> a_plus_abs_b(-1, -4)
    3
    """
    if b < 0:
        f = sub
    else:
        f = add
    return f(a, b)
# 小于0时使用sub函数，即a-b；大于0用add，即a+b。这样就能出绝对值和。


def two_of_three(i, j, k):
    """Return m*m + n*n, where m and n are the two smallest members of the
    positive numbers i, j, and k.

    >>> two_of_three(1, 2, 3)
    5
    >>> two_of_three(5, 3, 1)
    10
    >>> two_of_three(10, 2, 8)
    68
    >>> two_of_three(5, 5, 5)
    50
    """
    return square(min(i, j, k)) + square(middle(i, j, k)) # 没什么好说的。最小数加第二个数的square

def largest_factor(n):
    """Return the largest factor of n that is smaller than n.

    >>> largest_factor(15) # factors are 1, 3, 5
    5
    >>> largest_factor(80) # factors are 1, 2, 4, 5, 8, 10, 16, 20, 40
    40
    >>> largest_factor(13) # factors are 1, 13
    1
    """
    if n >1:
        for i in range(n-1,0,-1): # 从刚好小于n的整数开始推，一路推到0除非条件到达而中断，步长为-1
            if n%i == 0: # 表示n可以被i整除
                return i        



def hailstone(n):
    """Print the hailstone sequence starting at n and return its length.

    >>> a = hailstone(10)
    10
    5
    16
    8
    4
    2
    1
    >>> a
    7
    >>> b = hailstone(1)
    1
    >>> b
    1
    """
    length = 1 # 一开始假定第一步
    print(n)
    while n != 1: #如果n不等于1，就继续循环
        if n % 2 == 0: # 如果n是偶数
            n = n // 2
        else:
            n = 3 * n + 1 # 如果n是奇数，按照题目进行
        print(n)
        length += 1 # 每次操作后步长+1
    return length       # 返回步长  
