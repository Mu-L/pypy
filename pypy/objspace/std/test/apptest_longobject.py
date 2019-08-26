from pytest import raises
import sys
import math
import operator

def test_trunc():
    assert math.trunc(1L) == 1L
    assert math.trunc(-1L) == -1L

def test_add():
    x = 123L
    assert int(x + 12443L) == 123 + 12443
    x = -20
    assert x + 2 + 3L + True == -14L

def test_sub():
    assert int(58543L - 12332L) == 58543 - 12332
    assert int(58543L - 12332) == 58543 - 12332
    assert int(58543 - 12332L) == 58543 - 12332
    x = 237123838281233L
    assert x * 12 == x * 12L

def test_mul():
    x = 363L
    assert x * 2 ** 40 == x << 40

def test_truediv():
    exec "from __future__ import division; a = 31415926L / 10000000L"
    assert a == 3.1415926

def test_floordiv():
    x = 31415926L
    a = x // 10000000L
    assert a == 3L

def test_int_floordiv():
    x = 3000L
    a = x // 1000
    assert a == 3L

    x = 3000L
    a = x // -1000
    assert a == -3L

    x = 3000L
    raises(ZeroDivisionError, "x // 0")

    n = sys.maxint+1
    assert n / int(-n) == -1L

def test_numerator_denominator():
    assert (1L).numerator == 1L
    assert (1L).denominator == 1L
    assert (42L).numerator == 42L
    assert (42L).denominator == 1L

def test_compare():
    Z = 0
    ZL = 0L

    assert Z == ZL
    assert not (Z != ZL)
    assert ZL == Z
    assert not (ZL != Z)
    assert Z <= ZL
    assert not (Z < ZL)
    assert ZL <= ZL
    assert not (ZL < ZL)

    for BIG in (1L, 1L << 62, 1L << 9999):
        assert not (Z == BIG)
        assert Z != BIG
        assert not (BIG == Z)
        assert BIG != Z
        assert not (ZL == BIG)
        assert ZL != BIG
        assert Z <= BIG
        assert Z < BIG
        assert not (BIG <= Z)
        assert not (BIG < Z)
        assert ZL <= BIG
        assert ZL < BIG
        assert not (BIG <= ZL)
        assert not (BIG < ZL)
        assert not (Z <= -BIG)
        assert not (Z < -BIG)
        assert -BIG <= Z
        assert -BIG < Z
        assert not (ZL <= -BIG)
        assert not (ZL < -BIG)
        assert -BIG <= ZL
        assert -BIG < ZL
        #
        assert not (BIG <  int(BIG))
        assert     (BIG <= int(BIG))
        assert     (BIG == int(BIG))
        assert not (BIG != int(BIG))
        assert not (BIG >  int(BIG))
        assert     (BIG >= int(BIG))
        #
        assert     (BIG <  int(BIG)+1)
        assert     (BIG <= int(BIG)+1)
        assert not (BIG == int(BIG)+1)
        assert     (BIG != int(BIG)+1)
        assert not (BIG >  int(BIG)+1)
        assert not (BIG >= int(BIG)+1)
        #
        assert not (BIG <  int(BIG)-1)
        assert not (BIG <= int(BIG)-1)
        assert not (BIG == int(BIG)-1)
        assert     (BIG != int(BIG)-1)
        assert     (BIG >  int(BIG)-1)
        assert     (BIG >= int(BIG)-1)
        #
        assert not (int(BIG) <  BIG)
        assert     (int(BIG) <= BIG)
        assert     (int(BIG) == BIG)
        assert not (int(BIG) != BIG)
        assert not (int(BIG) >  BIG)
        assert     (int(BIG) >= BIG)
        #
        assert not (int(BIG)+1 <  BIG)
        assert not (int(BIG)+1 <= BIG)
        assert not (int(BIG)+1 == BIG)
        assert     (int(BIG)+1 != BIG)
        assert     (int(BIG)+1 >  BIG)
        assert     (int(BIG)+1 >= BIG)
        #
        assert     (int(BIG)-1 <  BIG)
        assert     (int(BIG)-1 <= BIG)
        assert not (int(BIG)-1 == BIG)
        assert     (int(BIG)-1 != BIG)
        assert not (int(BIG)-1 >  BIG)
        assert not (int(BIG)-1 >= BIG)

def test_conversion():
    class long2(long):
        pass
    x = 1L
    x = long2(x<<100)
    y = int(x)
    assert type(y) == long
    assert type(+long2(5)) is long
    assert type(long2(5) << 0) is long
    assert type(long2(5) >> 0) is long
    assert type(long2(5) + 0) is long
    assert type(long2(5) - 0) is long
    assert type(long2(5) * 1) is long
    assert type(1 * long2(5)) is long
    assert type(0 + long2(5)) is long
    assert type(-long2(0)) is long
    assert type(long2(5) // 1) is long

def test_shift():
    assert 65l >> 2l == 16l
    assert 65l >> 2 == 16l
    assert 65 >> 2l == 16l
    assert 65l << 2l == 65l * 4
    assert 65l << 2 == 65l * 4
    assert 65 << 2l == 65l * 4
    raises(ValueError, "1L << -1L")
    raises(ValueError, "1L << -1")
    raises(OverflowError, "1L << (2 ** 100)")
    raises(ValueError, "1L >> -1L")
    raises(ValueError, "1L >> -1")
    raises(OverflowError, "1L >> (2 ** 100)")

def test_pow():
    x = 0L
    assert pow(x, 0L, 1L) == 0L
    assert pow(-1L, -1L) == -1.0
    assert pow(2 ** 68, 0.5) == 2.0 ** 34
    assert pow(2 ** 68, 2) == 2 ** 136
    raises(TypeError, pow, 2l, -1, 3)
    raises(ValueError, pow, 2l, 5, 0)

    # some rpow tests
    assert pow(0, 0L, 1L) == 0L
    assert pow(-1, -1L) == -1.0

def test_int_pow():
    x = 2L
    assert pow(x, 2) == 4L
    assert pow(x, 2, 2) == 0L
    assert pow(x, 2, 3L) == 1L

def test_getnewargs():
    assert  0L .__getnewargs__() == (0L,)
    assert  (-1L) .__getnewargs__() == (-1L,)

def test_divmod():
    def check_division(x, y):
        q, r = divmod(x, y)
        pab, pba = x*y, y*x
        assert pab == pba
        assert q == x // y
        assert r == x % y
        assert x == q*y + r
        if y > 0:
            assert 0 <= r < y
        else:
            assert y < r <= 0
    for x in [-1L, 0L, 1L, 2L ** 100 - 1, -2L ** 100 - 1]:
        for y in [-105566530L, -1L, 1L, 1034522340L]:
            print "checking division for %s, %s" % (x, y)
            check_division(x, y)
            check_division(x, int(y))
            check_division(int(x), y)
    # special case from python tests:
    s1 = 33
    s2 = 2
    x = 16565645174462751485571442763871865344588923363439663038777355323778298703228675004033774331442052275771343018700586987657790981527457655176938756028872904152013524821759375058141439
    x >>= s1*16
    y = 10953035502453784575
    y >>= s2*16
    x = 0x3FE0003FFFFC0001FFFL
    y = 0x9800FFC1L
    check_division(x, y)
    raises(ZeroDivisionError, "x // 0L")
    raises(ZeroDivisionError, "x % 0L")
    raises(ZeroDivisionError, divmod, x, 0L)
    raises(ZeroDivisionError, "x // 0")
    raises(ZeroDivisionError, "x % 0")
    raises(ZeroDivisionError, divmod, x, 0)

def test_int_divmod():
    q, r = divmod(100L, 11)
    assert q == 9L
    assert r == 1L

def test_format():
    assert repr(12345678901234567890) == '12345678901234567890L'
    assert str(12345678901234567890) == '12345678901234567890'
    assert hex(0x1234567890ABCDEFL) == '0x1234567890abcdefL'
    assert oct(01234567012345670L) == '01234567012345670L'

def test_bits():
    x = 0xAAAAAAAAL
    assert x | 0x55555555L == 0xFFFFFFFFL
    assert x & 0x55555555L == 0x00000000L
    assert x ^ 0x55555555L == 0xFFFFFFFFL
    assert -x | 0x55555555L == -0xAAAAAAA9L
    assert x | 0x555555555L == 0x5FFFFFFFFL
    assert x & 0x555555555L == 0x000000000L
    assert x ^ 0x555555555L == 0x5FFFFFFFFL

def test_hash():
    # ints have the same hash as equal longs
    for i in range(-4, 14):
        assert hash(i) == hash(long(i)) == long(i).__hash__()
    # might check too much -- it's ok to change the hashing algorithm
    assert hash(123456789L) == 123456789
    assert hash(1234567890123456789L) in (
        -1895067127,            # with 32-bit platforms
        1234567890123456789)    # with 64-bit platforms

def test_math_log():
    raises(ValueError, math.log, 0L)
    raises(ValueError, math.log, -1L)
    raises(ValueError, math.log, -2L)
    raises(ValueError, math.log, -(1L << 10000))
    #raises(ValueError, math.log, 0)
    raises(ValueError, math.log, -1)
    raises(ValueError, math.log, -2)

def test_long():
    n = -sys.maxint-1
    assert long(n) == n
    assert str(long(n)) == str(n)
    a = buffer('123')
    assert long(a) == 123L

def test_huge_longs():
    x = 1L
    huge = x << 40000L
    raises(OverflowError, float, huge)
    raises(OverflowError, operator.truediv, huge, 3)
    raises(OverflowError, operator.truediv, huge, 3L)

def test_just_trunc():
    class myint(object):
        def __trunc__(self):
            return 42
    assert long(myint()) == 42

def test_override___long__():
    class mylong(long):
        def __long__(self):
            return 42L
    assert long(mylong(21)) == 42L
    class myotherlong(long):
        pass
    assert long(myotherlong(21)) == 21L

def test___long__():
    class A(object):
        def __long__(self):
            return 42
    assert long(A()) == 42L
    class B(object):
        def __int__(self):
            return 42
    raises(TypeError, long, B())

    class LongSubclass(long):
        pass
    class ReturnsLongSubclass(object):
        def __long__(self):
            return LongSubclass(42L)
    n = long(ReturnsLongSubclass())
    assert n == 42
    assert type(n) is LongSubclass

def test_trunc_returns():
    # but!: (blame CPython 2.7)
    class Integral(object):
        def __int__(self):
            return 42
    class TruncReturnsNonLong(object):
        def __trunc__(self):
            return Integral()
    n = long(TruncReturnsNonLong())
    assert type(n) is long
    assert n == 42

    class LongSubclass(long):
        pass
    class TruncReturnsNonInt(object):
        def __trunc__(self):
            return LongSubclass(42)
    n = long(TruncReturnsNonInt())
    assert n == 42
    assert type(n) is LongSubclass

def test_long_before_string():
    class A(str):
        def __long__(self):
            return 42
    assert long(A('abc')) == 42

def test_long_errors():
    raises(TypeError, long, 12, 12)
    raises(ValueError, long, 'xxxxxx?', 12)

def test_conjugate():
    assert (7L).conjugate() == 7L
    assert (-7L).conjugate() == -7L

    class L(long):
        pass

    assert type(L(7).conjugate()) is long

    class L(long):
        def __pos__(self):
            return 43
    assert L(7).conjugate() == 7L

def test_bit_length():
    assert 8L.bit_length() == 4
    assert (-1<<40).bit_length() == 41
    assert ((2**31)-1).bit_length() == 31

def test_negative_zero():
    x = eval("-0L")
    assert x == 0L

def test_mix_int_and_long():
    class IntLongMixClass(object):
        def __int__(self):
            return 42L

        def __long__(self):
            return 64

    mixIntAndLong = IntLongMixClass()
    as_long = long(mixIntAndLong)
    assert type(as_long) is long
    assert as_long == 64

def test_long_real():
    class A(long): pass
    b = A(5).real
    assert type(b) is long

def test__int__():
    class A(long):
        def __int__(self):
            return 42

    assert int(long(3)) == long(3)
    assert int(A(13)) == 42

def test_long_error_msg():
    e = raises(TypeError, long, [])
    assert str(e.value) == (
        "long() argument must be a string or a number, not 'list'")

def test_coerce():
    assert 3L.__coerce__(4L) == (3L, 4L)
    assert 3L.__coerce__(4) == (3, 4)
    assert 3L.__coerce__(object()) == NotImplemented

def test_linear_long_base_16():
    # never finishes if long(_, 16) is not linear-time
    size = 100000
    n = "a" * size
    expected = (2 << (size * 4)) // 3
    assert long(n, 16) == expected