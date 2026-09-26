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


# ===== Formatting helpers and Rule 1 (SPEC.md §5.5) =====

def _series(values, point_numbers=None):
    if point_numbers is None:
        point_numbers = list(range(1, len(values) + 1))
    return imr.Series(point_numbers=point_numbers, values=values)


def test_line_name_all_seven():
    assert imr.line_name(0) == "Mean"
    assert imr.line_name(1) == "+1 SD"
    assert imr.line_name(2) == "+2 SD"
    assert imr.line_name(3) == "+3 SD"
    assert imr.line_name(-1) == "-1 SD"
    assert imr.line_name(-2) == "-2 SD"
    assert imr.line_name(-3) == "-3 SD"


def test_fmt_pairs():
    assert imr.fmt_pairs([14, 15], [3.1, 2.9]) == "14=3.100, 15=2.900"


def test_fmt_points():
    assert imr.fmt_points([1, 3, 4]) == "1, 3, 4"


def test_fmt_values():
    assert imr.fmt_values([2.5, 2.5]) == "2.500, 2.500"


def test_fmt_span_uses_en_dash():
    assert imr.fmt_span(1, 12) == "1–12"


def test_rule_1_e1():
    obs = imr.rule_1(_series([0.0, 0.0, 3.5]), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 1
    assert o.rule_name == imr.RULE_NAMES[1]
    assert o.direction == "above"
    assert o.points == [3]
    assert o.values == [3.5]
    assert o.span == (3, 3)
    assert o.line_or_window == "+3 SD=3.000"
    assert o.description == (
        "Rule 1 — One point beyond 3 SD: point 3 (value 3.500) "
        "is above the +3 SD line (3.000)."
    )


def test_rule_1_below():
    obs = imr.rule_1(_series([-3.5]), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.direction == "below"
    assert o.line_or_window == "-3 SD=-3.000"
    assert o.description.endswith("is below the -3 SD line (-3.000).")
    assert o.description == (
        "Rule 1 — One point beyond 3 SD: point 1 (value -3.500) "
        "is below the -3 SD line (-3.000)."
    )


def test_rule_1_exactly_on_line_does_not_fire():
    assert imr.rule_1(_series([3.0]), L) == []
    assert imr.rule_1(_series([-3.0]), L) == []


def test_rule_1_just_beyond_line_fires():
    assert len(imr.rule_1(_series([3.0 + 1e-6]), L)) == 1


def test_rule_1_consecutive_points_are_separate():
    obs = imr.rule_1(_series([3.5, 3.5, 0.0, -3.5]), L)
    assert [o.points for o in obs] == [[1], [2], [4]]
    assert [o.direction for o in obs] == ["above", "above", "below"]


def test_rule_1_uses_point_numbers_not_positions():
    obs = imr.rule_1(_series([0.0, 0.0, 3.5], point_numbers=[2, 3, 4]), L)
    assert len(obs) == 1
    assert obs[0].points == [4]
    assert obs[0].span == (4, 4)
    assert "point 4 " in obs[0].description


def test_rule_1_copies_field_and_chart():
    obs = imr.rule_1(_series([3.5, -3.5]), L, field="IMR_Field_X", chart="MR")
    assert all(o.field == "IMR_Field_X" and o.chart == "MR" for o in obs)


def test_rule_1_field_and_chart_default_empty():
    obs = imr.rule_1(_series([3.5]), L)
    assert obs[0].field == "" and obs[0].chart == ""


# ===== Maximal runs and Rule 2 (SPEC.md §5.3) =====

def test_maximal_runs_example():
    labels = ["A", "A", None, "B", "B", "B", "A"]
    assert imr.maximal_runs(labels) == [("A", 0, 1), ("B", 3, 5), ("A", 6, 6)]


def test_maximal_runs_empty():
    assert imr.maximal_runs([]) == []


def test_maximal_runs_all_none():
    assert imr.maximal_runs([None, None]) == []


def test_maximal_runs_single_run():
    assert imr.maximal_runs(["A"] * 4) == [("A", 0, 3)]


def test_rule_2_exactly_nine_above():
    obs = imr.rule_2(_series([0.5] * 9), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 2
    assert o.rule_name == imr.RULE_NAMES[2]
    assert o.direction == "above"
    assert o.points == list(range(1, 10))
    assert o.values == [0.5] * 9
    assert o.span == (1, 9)
    assert o.line_or_window == "mean=0.000"
    assert o.description == (
        "Rule 2 — Nine or more points on one side of the mean: 9 consecutive "
        "points above the mean (0.000), points 1–9. Values: 1=0.500, 2=0.500, "
        "3=0.500, 4=0.500, 5=0.500, 6=0.500, 7=0.500, 8=0.500, 9=0.500."
    )


def test_rule_2_eight_points_nothing():
    assert imr.rule_2(_series([0.5] * 8), L) == []


def test_rule_2_e2_twelve_points_one_entry():
    obs = imr.rule_2(_series([0.5] * 12), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 13))
    assert obs[0].span == (1, 12)
    assert obs[0].direction == "above"


def test_rule_2_nine_below():
    obs = imr.rule_2(_series([-0.5] * 9), L)
    assert len(obs) == 1
    assert obs[0].direction == "below"
    assert "9 consecutive points below the mean (0.000)" in obs[0].description


def test_rule_2_e3_point_on_mean_splits_run():
    assert imr.rule_2(_series([0.5] * 5 + [0.0] + [0.5] * 5), L) == []


def test_rule_2_two_separate_runs_in_point_order():
    obs = imr.rule_2(_series([0.5] * 9 + [-0.5] * 9), L)
    assert len(obs) == 2
    assert obs[0].direction == "above" and obs[0].span == (1, 9)
    assert obs[1].direction == "below" and obs[1].span == (10, 18)


def test_rule_2_uses_point_numbers_mr_numbering():
    obs = imr.rule_2(_series([0.5] * 9, list(range(2, 11))), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(2, 11))
    assert obs[0].span == (2, 10)
    assert "points 2–10." in obs[0].description
