"""Rule engine tests (SPEC.md §5).

Zone predicates and difference signs (§5.1): comparisons are strict, and a value
exactly on a line (within tolerance) belongs to neither side.
"""

import imr

L = imr.lines_for(0.0, 1.0)


# ----- on the +1 / -1 lines -----

def test_plus_one_line_is_neither_within_nor_outside():
    assert not imr.within_1(1.0, L)
    assert not imr.outside_1(1.0, L)


def test_minus_one_line_is_neither_within_nor_outside():
    assert not imr.within_1(-1.0, L)
    assert not imr.outside_1(-1.0, L)


def test_tiny_offset_counts_as_on_the_line():
    v = 1.0 + 1e-12
    assert imr.on_line(v, L[1])
    assert not imr.outside_1(v, L)
    assert not imr.within_1(v, L)


def test_small_offset_above_plus_one_is_outside():
    v = 1.0 + 1e-6
    assert imr.outside_1(v, L)
    assert imr.beyond_above(v, L, 1)


def test_small_offset_below_minus_one_is_outside():
    v = -1.0 - 1e-6
    assert imr.outside_1(v, L)
    assert imr.beyond_below(v, L, 1)


# ----- the mean -----

def test_on_mean_is_neither_above_nor_below():
    assert not imr.above_mean(0.0, L)
    assert not imr.below_mean(0.0, L)


def test_half_above_mean_is_above_and_within_1():
    assert imr.above_mean(0.5, L)
    assert imr.within_1(0.5, L)


def test_half_below_mean_is_below_and_within_1():
    assert imr.below_mean(-0.5, L)
    assert imr.within_1(-0.5, L)


# ----- beyond 2 and 3 SD -----

def test_exactly_on_plus_three_is_not_beyond():
    assert not imr.beyond_above(3.0, L, 3)


def test_just_above_plus_three_is_beyond():
    assert imr.beyond_above(3.0001, L, 3)


def test_just_below_minus_three_is_beyond():
    assert imr.beyond_below(-3.0001, L, 3)


def test_two_and_a_half_is_beyond_two_not_three():
    assert imr.beyond_above(2.5, L, 2)
    assert not imr.beyond_above(2.5, L, 3)


# ----- tolerance scales with the line -----

def test_tolerance_scales_with_line_value():
    big = imr.lines_for(1000.0, 10.0)
    assert abs(big[3] - 1030.0) < 1e-9
    assert imr.on_line(1030.0 + 5e-7, big[3])
    assert not imr.beyond_above(1030.0 + 5e-7, big, 3)
    assert imr.beyond_above(1030.0 + 5e-6, big, 3)


# ----- difference signs -----

def test_diff_sign_equal_is_zero():
    assert imr.diff_sign(2, 2) == "0"


def test_diff_sign_within_tolerance_is_zero():
    assert imr.diff_sign(2, 2 + 1e-12) == "0"


def test_diff_sign_rising_and_falling():
    assert imr.diff_sign(1, 2) == "+"
    assert imr.diff_sign(2, 1) == "-"


def test_diff_signs_sequence():
    assert imr.diff_signs([1, 2, 2, 1]) == ["+", "0", "-"]


def test_diff_signs_single_value_is_empty():
    assert imr.diff_signs([5]) == []
