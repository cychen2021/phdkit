from phdkit import infix


@infix
def add(x: int, y: int) -> int:
    return x + y


@infix
def concat(a: str, b: str) -> str:
    return f"{a}-{b}"


def test_infix_operator():
    assert 1 | add | 2 == 3
    assert "a" | concat | "b" == "a-b"


def test_infix_partial_left_right():
    plus_five = add.left(5)
    assert plus_five(3) == 8

    times = concat.right("end")
    # right binds the provided value as the left operand for the call
    assert times("start") == "end-start"


def test_infix_lbind_rbind_and_reverse():
    # create left-bound and right-bound objects using the infix helpers
    lb = add.left(2)
    rb = add.right(3)

    # calling them should behave as partials
    assert lb(5) == 7
    assert rb(4) == 7

    # reverse should swap sides
    assert lb.reverse(10) == add(10, 2)
    assert rb.reverse(10) == add(3, 10)

    # reprs are stable and human readable
    assert "Waiting for left side" in repr(lb) or "Waiting for right side" in repr(lb)
    assert "Waiting for left side" in repr(rb) or "Waiting for right side" in repr(rb)
