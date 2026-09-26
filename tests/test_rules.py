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


# ===== Rules 7 and 8 (SPEC.md §5.3) =====

def _alternate(a, b, n):
    return [a if i % 2 == 0 else b for i in range(n)]


def test_rule_7_fifteen_within():
    vals = _alternate(0.5, -0.5, 15)
    obs = imr.rule_7(_series(vals), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 7
    assert o.rule_name == imr.RULE_NAMES[7]
    assert o.direction == "within"
    assert o.points == list(range(1, 16))
    assert o.values == vals
    assert o.span == (1, 15)
    assert o.line_or_window == "-1 SD=-1.000; +1 SD=1.000"
    pairs = ", ".join(f"{p}={'0.500' if p % 2 else '-0.500'}" for p in range(1, 16))
    assert o.description == (
        "Rule 7 — Fifteen or more points within 1 SD of the mean: 15 consecutive "
        "points, 1–15, all between the -1 SD line (-1.000) and the +1 SD line "
        f"(1.000). Values: {pairs}."
    )


def test_rule_7_fourteen_nothing():
    assert imr.rule_7(_series(_alternate(0.5, -0.5, 14)), L) == []


def test_rule_7_eighteen_one_entry():
    obs = imr.rule_7(_series(_alternate(0.5, -0.5, 18)), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 19))
    assert obs[0].span == (1, 18)


def test_rule_7_e14_point_on_plus_one_splits_run():
    assert imr.rule_7(_series([0.5] * 7 + [1.0] + [0.5] * 7), L) == []


def test_rule_7_uses_point_numbers_mr_numbering():
    obs = imr.rule_7(_series(_alternate(0.5, -0.5, 15), list(range(2, 17))), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(2, 17))
    assert obs[0].span == (2, 16)
    assert "points, 2–16, all between" in obs[0].description


def test_rule_8_e8():
    vals = _alternate(1.5, -1.5, 8)
    obs = imr.rule_8(_series(vals), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 8
    assert o.rule_name == imr.RULE_NAMES[8]
    assert o.direction == "either"
    assert o.points == list(range(1, 9))
    assert o.values == vals
    assert o.span == (1, 8)
    assert o.line_or_window == "-1 SD=-1.000; +1 SD=1.000"
    assert "(4 above, 4 below)" in o.description
    assert o.description == (
        "Rule 8 — Eight or more points beyond 1 SD on either side: 8 consecutive "
        "points, 1–8, none within 1 SD (4 above, 4 below). Values: 1=1.500, "
        "2=-1.500, 3=1.500, 4=-1.500, 5=1.500, 6=-1.500, 7=1.500, 8=-1.500."
    )


def test_rule_8_seven_nothing():
    assert imr.rule_8(_series(_alternate(1.5, -1.5, 7)), L) == []


def test_rule_8_eleven_one_entry_with_counts():
    obs = imr.rule_8(_series(_alternate(1.5, -1.5, 11)), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 12))
    assert obs[0].span == (1, 11)
    assert "(6 above, 5 below)" in obs[0].description


def test_rule_8_e9_values_on_lines_nothing():
    assert imr.rule_8(_series(_alternate(1.0, -1.0, 14)), L) == []


def test_rule_8_all_one_side():
    obs = imr.rule_8(_series([1.5] * 8), L)
    assert len(obs) == 1
    assert "(8 above, 0 below)" in obs[0].description


def test_rule_8_uses_point_numbers_mr_numbering():
    obs = imr.rule_8(_series(_alternate(1.5, -1.5, 8), list(range(2, 10))), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(2, 10))
    assert obs[0].span == (2, 9)
    assert "points, 2–9, none within" in obs[0].description


# ===== Rules 3 and 4 (SPEC.md §5.5) =====

def test_rule_3_six_rising():
    vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    obs = imr.rule_3(_series(vals), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 3
    assert o.rule_name == imr.RULE_NAMES[3]
    assert o.direction == "rising"
    assert o.points == [1, 2, 3, 4, 5, 6]
    assert o.values == vals
    assert o.span == (1, 6)
    assert o.line_or_window == ""
    assert o.description == (
        "Rule 3 — Six or more points steadily rising: 6 consecutive points, 1–6. "
        "Values: 1=0.100, 2=0.200, 3=0.300, 4=0.400, 5=0.500, 6=0.600."
    )


def test_rule_3_five_rising_nothing():
    assert imr.rule_3(_series([0.1, 0.2, 0.3, 0.4, 0.5]), L) == []


def test_rule_3_nine_rising_one_entry():
    obs = imr.rule_3(_series([0.1 * i for i in range(1, 10)]), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 10))
    assert obs[0].span == (1, 9)


def test_rule_3_six_falling():
    obs = imr.rule_3(_series([0.6, 0.5, 0.4, 0.3, 0.2, 0.1]), L)
    assert len(obs) == 1
    assert obs[0].direction == "falling"
    assert obs[0].points == [1, 2, 3, 4, 5, 6]
    assert "steadily falling: 6 consecutive points, 1–6." in obs[0].description


def test_rule_3_e4_peak_in_both():
    obs = imr.rule_3(_series([1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1]), L)
    assert [(o.direction, o.points) for o in obs] == [
        ("rising", list(range(1, 8))),
        ("falling", list(range(7, 14))),
    ]
    assert [o.span for o in obs] == [(1, 7), (7, 13)]


def test_rule_3_e5_tie_splits_run():
    assert imr.rule_3(_series([1, 2, 3, 3, 4, 5, 6, 7]), L) == []


def test_rule_3_uses_point_numbers_mr_numbering():
    obs = imr.rule_3(_series([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], list(range(2, 8))), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(2, 8))
    assert obs[0].span == (2, 7)
    assert "6 consecutive points, 2–7." in obs[0].description


def test_rule_4_e6():
    vals = _alternate(0.5, -0.5, 14)
    obs = imr.rule_4(_series(vals), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 4
    assert o.rule_name == imr.RULE_NAMES[4]
    assert o.direction == "alternating"
    assert o.points == list(range(1, 15))
    assert o.values == vals
    assert o.span == (1, 14)
    assert o.line_or_window == ""
    pairs = ", ".join(f"{p}={'0.500' if p % 2 else '-0.500'}" for p in range(1, 15))
    assert o.description == (
        "Rule 4 — Fourteen or more points alternating up and down: 14 consecutive "
        f"points, 1–14. Values: {pairs}."
    )


def test_rule_4_thirteen_nothing():
    assert imr.rule_4(_series(_alternate(0.5, -0.5, 13)), L) == []


def test_rule_4_seventeen_one_entry():
    obs = imr.rule_4(_series(_alternate(0.5, -0.5, 17)), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 18))
    assert obs[0].span == (1, 17)


def test_rule_4_e9():
    obs = imr.rule_4(_series(_alternate(1.0, -1.0, 14)), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(1, 15))


def test_rule_4_repeated_value_splits():
    # Points 10 and 11 are both -0.5; halves of 10 points each, 20 points in all.
    vals = _alternate(0.5, -0.5, 10) + _alternate(-0.5, 0.5, 10)
    assert len(vals) == 20
    assert vals[9] == vals[10]
    assert imr.rule_4(_series(vals), L) == []


def test_rule_4_two_rises_in_a_row_split():
    # -0.5 -> 0.0 -> 0.5 at points 10-12: two rises in a row; 20 points in all.
    vals = _alternate(0.5, -0.5, 10) + [0.0] + _alternate(0.5, -0.5, 9)
    assert len(vals) == 20
    assert imr.rule_4(_series(vals), L) == []


def test_rule_4_uses_point_numbers_mr_numbering():
    obs = imr.rule_4(_series(_alternate(0.5, -0.5, 14), list(range(2, 16))), L)
    assert len(obs) == 1
    assert obs[0].points == list(range(2, 16))
    assert obs[0].span == (2, 15)
    assert "14 consecutive points, 2–15." in obs[0].description


# ----- Rule 5: two of three points beyond 2 SD (window rule, §5.4) -----

def test_rule_5_e10():
    obs = imr.rule_5(_series([2.5, 0, 2.5]), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 5
    assert o.rule_name == imr.RULE_NAMES[5]
    assert o.direction == "above"
    assert o.points == [1, 3]
    assert o.values == [2.5, 2.5]
    assert o.span == (1, 3)
    assert o.line_or_window == "+2 SD=2.000; window 1-3"
    assert o.description == (
        "Rule 5 — Two of three points beyond 2 SD: points 1, 3 "
        "(values 2.500, 2.500) are above the +2 SD line (2.000); window 1–3.")


def test_rule_5_e11_overlapping_windows_merge():
    obs = imr.rule_5(_series([2.5, 0, 2.5, 2.5, 0, 0]), L)
    assert len(obs) == 1
    assert obs[0].points == [1, 3, 4]
    assert obs[0].span == (1, 5)
    assert 5 not in obs[0].points


def test_rule_5_adjacent_non_overlapping_windows_stay_separate():
    obs = imr.rule_5(_series([2.5, 2.5, 0, 0, 2.5, 2.5]), L)
    assert len(obs) == 2
    assert obs[0].points == [1, 2]
    assert obs[0].span == (1, 3)
    assert obs[1].points == [5, 6]
    assert obs[1].span == (4, 6)


def test_rule_5_threshold_minus_one_nothing():
    assert imr.rule_5(_series([2.5, 0, 0, 2.5]), L) == []


def test_rule_5_three_of_three():
    obs = imr.rule_5(_series([2.5, 2.5, 2.5]), L)
    assert len(obs) == 1
    assert obs[0].points == [1, 2, 3]


def test_rule_5_below_side():
    obs = imr.rule_5(_series([-2.5, 0, -2.5]), L)
    assert len(obs) == 1
    assert obs[0].direction == "below"
    assert obs[0].line_or_window == "-2 SD=-2.000; window 1-3"


def test_rule_5_opposite_sides_do_not_count_together():
    assert imr.rule_5(_series([2.5, -2.5, 0]), L) == []


def test_rule_5_value_on_line_not_flagged():
    assert imr.rule_5(_series([2.0, 0, 2.5]), L) == []


def test_rule_5_uses_point_numbers_mr_numbering():
    obs = imr.rule_5(imr.Series(point_numbers=[2, 3, 4], values=[2.5, 0, 2.5]), L)
    assert len(obs) == 1
    assert obs[0].points == [2, 4]
    assert obs[0].span == (2, 4)
    assert obs[0].line_or_window.endswith("window 2-4")
    assert obs[0].description.endswith("window 2–4.")


# ----- Rule 6: four of five points beyond 1 SD (window rule, §5.4) -----

def test_rule_6_e12():
    obs = imr.rule_6(_series([1.5, 1.5, 0, 1.5, 1.5]), L)
    assert len(obs) == 1
    o = obs[0]
    assert o.rule_no == 6
    assert o.rule_name == imr.RULE_NAMES[6]
    assert o.direction == "above"
    assert o.points == [1, 2, 4, 5]
    assert o.span == (1, 5)
    assert o.line_or_window == "+1 SD=1.000; window 1-5"
    assert o.description == (
        "Rule 6 — Four of five points beyond 1 SD: points 1, 2, 4, 5 "
        "(values 1.500, 1.500, 1.500, 1.500) are above the +1 SD line (1.000); "
        "window 1–5.")


def test_rule_6_three_of_five_nothing():
    assert imr.rule_6(_series([1.5, 1.5, 0, 1.5, 0]), L) == []


def test_rule_6_five_of_five():
    obs = imr.rule_6(_series([1.5] * 5), L)
    assert len(obs) == 1
    assert obs[0].points == [1, 2, 3, 4, 5]


def test_rule_6_series_shorter_than_window_nothing():
    assert imr.rule_6(_series([1.5] * 4), L) == []


# ----- detect_all and the fourteen worked examples (SPEC.md §5.8, §5.9) -----

def _summary(values):
    return [(o.rule_no, o.direction, o.points, o.span)
            for o in imr.detect_all(_series(values), L)]


def _r(a, b):
    return list(range(a, b + 1))


E4 = [1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3, 2, 1]
E7 = [0.5, -0.5] * 7 + [0.5]


def test_detect_all_e1():
    assert _summary([0, 0, 3.5]) == [(1, "above", [3], (3, 3))]


def test_detect_all_e2():
    assert _summary([0.5] * 12) == [(2, "above", _r(1, 12), (1, 12))]


def test_detect_all_e3():
    assert _summary([0.5] * 5 + [0] + [0.5] * 5) == []


def test_detect_all_e4():
    assert _summary(E4) == [
        (1, "above", [4], (4, 4)),
        (1, "above", [5], (5, 5)),
        (1, "above", [6], (6, 6)),
        (1, "above", [7], (7, 7)),
        (1, "above", [8], (8, 8)),
        (1, "above", [9], (9, 9)),
        (1, "above", [10], (10, 10)),
        (2, "above", _r(1, 13), (1, 13)),
        (3, "rising", _r(1, 7), (1, 7)),
        (3, "falling", _r(7, 13), (7, 13)),
        (5, "above", _r(3, 11), (2, 12)),
        (6, "above", _r(2, 12), (1, 13)),
        (8, "either", _r(2, 12), (2, 12)),
    ]
    rule_8 = imr.detect_all(_series(E4), L)[-1]
    assert "(11 above, 0 below)" in rule_8.description


def test_detect_all_e5():
    assert _summary([1, 2, 3, 3, 4, 5, 6, 7]) == [
        (1, "above", [5], (5, 5)),
        (1, "above", [6], (6, 6)),
        (1, "above", [7], (7, 7)),
        (1, "above", [8], (8, 8)),
        (5, "above", _r(3, 8), (2, 8)),
        (6, "above", _r(2, 8), (1, 8)),
    ]


def test_detect_all_e6():
    assert _summary([0.5, -0.5] * 7) == [(4, "alternating", _r(1, 14), (1, 14))]


def test_detect_all_e7():
    assert _summary(E7) == [
        (4, "alternating", _r(1, 15), (1, 15)),
        (7, "within", _r(1, 15), (1, 15)),
    ]


def test_detect_all_e8():
    assert _summary([1.5, -1.5] * 4) == [(8, "either", _r(1, 8), (1, 8))]
    obs = imr.detect_all(_series([1.5, -1.5] * 4), L)
    assert "(4 above, 4 below)" in obs[0].description


def test_detect_all_e9():
    assert _summary([1, -1] * 7) == [(4, "alternating", _r(1, 14), (1, 14))]


def test_detect_all_e10():
    assert _summary([2.5, 0, 2.5]) == [(5, "above", [1, 3], (1, 3))]


def test_detect_all_e11():
    assert _summary([2.5, 0, 2.5, 2.5, 0, 0]) == [(5, "above", [1, 3, 4], (1, 5))]


def test_detect_all_e12():
    assert _summary([1.5, 1.5, 0, 1.5, 1.5]) == [(6, "above", [1, 2, 4, 5], (1, 5))]


def test_detect_all_e13():
    assert _summary([0.5, -0.5] * 8) == [
        (4, "alternating", _r(1, 16), (1, 16)),
        (7, "within", _r(1, 16), (1, 16)),
    ]


def test_detect_all_e14():
    assert _summary([0.5] * 7 + [1.0] + [0.5] * 7) == [(2, "above", _r(1, 15), (1, 15))]


def test_pattern_points_e7_union_once():
    obs = imr.detect_all(_series(E7), L)
    assert all(3 in o.points for o in obs if o.rule_no in (4, 7))
    assert imr.pattern_points(obs) == set(range(1, 16))


def test_pattern_points_empty():
    assert imr.pattern_points([]) == set()


def test_detect_all_stamps_field_and_chart():
    obs = imr.detect_all(_series(E4), L, field="IMR_Field_A", chart="I")
    assert obs
    assert all(o.field == "IMR_Field_A" and o.chart == "I" for o in obs)


def test_detect_all_mr_numbering_end_to_end():
    x = [0, 3, 0, 3, 0, 3, 0, 3, 0, 3]
    mr = imr.moving_range_series(x)
    assert mr.point_numbers == _r(2, 10)
    obs = imr.detect_all(mr, L)
    assert all(2 <= p <= 10 for o in obs for p in o.points)
    rule_2 = [o for o in obs if o.rule_no == 2]
    assert len(rule_2) == 1
    assert rule_2[0].points == _r(2, 10)
    assert rule_2[0].span == (2, 10)


def test_detect_all_ordering_e4():
    obs = imr.detect_all(_series(E4), L)
    rules = [o.rule_no for o in obs]
    assert rules == sorted(rules)
    firsts = [o.points[0] for o in obs if o.rule_no == 1]
    assert firsts == sorted(firsts) and len(set(firsts)) == len(firsts)


# ===== Step 22 audit: gaps against SPEC.md §12.3 =====

def test_rule_6_below_side():
    obs = imr.rule_6(_series([-1.5, -1.5, 0, -1.5, -1.5]), L)
    assert len(obs) == 1
    assert obs[0].direction == "below"
    assert obs[0].points == [1, 2, 4, 5]
    assert obs[0].line_or_window == "-1 SD=-1.000; window 1-5"
    assert obs[0].description == (
        "Rule 6 — Four of five points beyond 1 SD: points 1, 2, 4, 5 "
        "(values -1.500, -1.500, -1.500, -1.500) are below the -1 SD line (-1.000); "
        "window 1–5.")


def test_rule_6_overlapping_windows_merge():
    # Windows 1-5 and 2-6 both qualify; window 3-7 does not.
    obs = imr.rule_6(_series([1.5, 1.5, 0, 1.5, 1.5, 1.5, 0, 0, 0]), L)
    assert len(obs) == 1
    assert obs[0].points == [1, 2, 4, 5, 6]
    assert obs[0].span == (1, 6)
    assert 3 not in obs[0].points


def test_rule_6_adjacent_non_overlapping_windows_stay_separate():
    # Only windows 1-5 and 6-10 qualify.
    obs = imr.rule_6(_series([1.5, 1.5, 1.5, 1.5, 0, 0, 1.5, 1.5, 1.5, 1.5]), L)
    assert len(obs) == 2
    assert obs[0].points == [1, 2, 3, 4]
    assert obs[0].span == (1, 5)
    assert obs[1].points == [7, 8, 9, 10]
    assert obs[1].span == (6, 10)


def test_rule_6_opposite_sides_do_not_count_together():
    assert imr.rule_6(_series([1.5, 1.5, -1.5, -1.5, 0]), L) == []


def test_rule_8_point_on_line_in_middle_splits_run():
    # Without the on-line point, eleven points beyond 1 SD fire Rule 8.
    assert len(imr.rule_8(_series(_alternate(1.5, -1.5, 11)), L)) == 1
    # A point exactly on +1 SD at position 6 leaves two runs of 5: nothing.
    vals = _alternate(1.5, -1.5, 5) + [1.0] + _alternate(-1.5, 1.5, 5)
    assert imr.rule_8(_series(vals), L) == []


def test_rule_8_point_within_one_sd_in_middle_splits_run():
    vals = _alternate(1.5, -1.5, 5) + [0.5] + _alternate(-1.5, 1.5, 5)
    assert imr.rule_8(_series(vals), L) == []


def test_rule_7_point_beyond_one_sd_in_middle_splits_run():
    vals = _alternate(0.5, -0.5, 8) + [1.5] + _alternate(0.5, -0.5, 8)
    assert imr.rule_7(_series(vals), L) == []
