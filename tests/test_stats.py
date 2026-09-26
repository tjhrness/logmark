"""Statistics tests (SPEC.md §4.1, §4.2, §4.5).

Expected values are computed independently here, with the literal 1.128 where needed,
never with imr's own constants, so a wrong constant in imr.py would be caught.
"""

import statistics

import pytest

import imr


# ----- moving_ranges -----

def test_moving_ranges_values():
    assert imr.moving_ranges([1, 4, 2, 2, 9]) == [3, 2, 0, 7]


def test_moving_ranges_length_is_n_minus_one():
    values = [1, 4, 2, 2, 9, 3, 8]
    assert len(imr.moving_ranges(values)) == len(values) - 1


def test_moving_ranges_one_value_raises():
    with pytest.raises(ValueError):
        imr.moving_ranges([5.0])


def test_moving_ranges_negatives():
    assert imr.moving_ranges([-1.5, 2.0, -0.5]) == [3.5, 2.5]


# ----- mean_of -----

@pytest.mark.parametrize(
    "values",
    [
        [1, 2, 3, 4, 10],
        [0.1, 0.2, 0.35, 1.25],
        [-4, -2.5, -10, -0.5],
        [3.2, -1.5, 0.0, 7.75, 2.1],
    ],
)
def test_mean_of_matches_statistics_mean(values):
    assert imr.mean_of(values) == pytest.approx(statistics.mean(values))


# ----- lines_for -----

def test_lines_for_seven_lines():
    lines = imr.lines_for(10.0, 2.0)
    assert sorted(lines) == [-3, -2, -1, 0, 1, 2, 3]
    expected = {-3: 4, -2: 6, -1: 8, 0: 10, 1: 12, 2: 14, 3: 16}
    for k, value in expected.items():
        assert lines[k] == pytest.approx(value)


# ----- i_chart_stats -----

def test_i_chart_stats_simple_series():
    stats = imr.i_chart_stats([10, 12, 9, 11, 13])
    assert stats.n == 5
    assert stats.mean == pytest.approx(11.0)
    assert stats.mr_bar == pytest.approx(2.25)
    assert stats.sigma == pytest.approx(2.25 / 1.128)
    assert stats.sigma == pytest.approx(1.994681, abs=1e-6)
    assert stats.lines[3] == pytest.approx(16.984043, abs=1e-6)
    assert stats.lines[-3] == pytest.approx(5.015957, abs=1e-6)
    assert sorted(stats.lines) == [-3, -2, -1, 0, 1, 2, 3]
    for k in (-3, -2, -1, 0, 1, 2, 3):
        assert stats.lines[k] == pytest.approx(11.0 + k * 2.25 / 1.128)


def test_i_chart_stats_mixed_decimals_and_negatives():
    stats = imr.i_chart_stats([3.2, -1.5, 0.0, 7.75, 2.1])
    expected_mr_bar = (4.7 + 1.5 + 7.75 + 5.65) / 4
    assert stats.mr_bar == pytest.approx(expected_mr_bar)
    assert stats.sigma == pytest.approx(expected_mr_bar / 1.128)
    assert stats.mean == pytest.approx(statistics.mean([3.2, -1.5, 0.0, 7.75, 2.1]))


def test_i_chart_sigma_is_not_the_plain_sample_sd():
    values = [10.0] * 10 + [20.0] * 10
    stats = imr.i_chart_stats(values)
    assert stats.mr_bar == pytest.approx(10 / 19)
    assert stats.sigma < statistics.stdev(values) / 5


def test_i_chart_stats_identical_values_give_zero_sigma():
    stats = imr.i_chart_stats([5, 5, 5, 5])
    assert stats.mr_bar == 0.0
    assert stats.sigma == 0.0
    assert all(stats.lines[k] == 5.0 for k in (-3, -2, -1, 0, 1, 2, 3))


# ----- fmt -----

@pytest.mark.parametrize(
    "value, text",
    [
        (42.3, "42.300"),
        (-0.5, "-0.500"),
        (1 / 3, "0.333"),
        (2.00049, "2.000"),
        (2.0006, "2.001"),
        (0, "0.000"),
        (-0.0, "0.000"),
    ],
)
def test_fmt(value, text):
    assert imr.fmt(value) == text


def test_fmt_tiny_negative_does_not_print_negative_zero():
    assert imr.fmt(-0.0001) == "0.000"


# ----- chart series (Step 3) -----

def test_individuals_series():
    series = imr.individuals_series([1, 4, 2, 2, 9])
    assert series.point_numbers == [1, 2, 3, 4, 5]
    assert series.values == [1, 4, 2, 2, 9]


def test_moving_range_series_numbered_from_two():
    series = imr.moving_range_series([1, 4, 2, 2, 9])
    assert series.values == [3, 2, 0, 7]
    assert series.point_numbers == [2, 3, 4, 5]


def test_moving_range_series_one_value_raises():
    with pytest.raises(ValueError):
        imr.moving_range_series([5.0])


# ----- mr_chart_stats (Step 3) -----

def test_mr_chart_stats_simple_series():
    stats = imr.mr_chart_stats([1, 4, 2, 2, 9])
    assert stats.n == 4
    assert stats.mean == pytest.approx(3.0)
    assert stats.mr_bar == pytest.approx(3.0)
    assert stats.sigma == pytest.approx(0.7557 * 3.0)
    assert stats.sigma == pytest.approx(2.2671, abs=1e-4)
    expected = {3: 9.8013, 1: 5.2671, -1: 0.7329, -2: -1.5342, -3: -3.8013}
    for k, value in expected.items():
        assert stats.lines[k] == pytest.approx(value, abs=1e-4)
    assert sorted(stats.lines) == [-3, -2, -1, 0, 1, 2, 3]


MIXED_TEN = [3.2, -1.5, 0.0, 7.75, 2.1, -4.3, 5.5, 1.25, -0.8, 6.0]


def test_mr_chart_shares_mr_bar_with_i_chart():
    assert imr.mr_chart_stats(MIXED_TEN).mr_bar == pytest.approx(imr.i_chart_stats(MIXED_TEN).mr_bar)


def test_mr_chart_upper_limit_matches_textbook_d4():
    stats = imr.mr_chart_stats(MIXED_TEN)
    assert stats.mr_bar > 0
    assert abs(stats.lines[3] - 3.267 * stats.mr_bar) <= 0.0002 * stats.mr_bar


def test_mr_chart_lower_lines():
    stats = imr.mr_chart_stats(MIXED_TEN)
    assert imr.lines_below_zero(stats) == [-3, -2]
    assert stats.lines[-1] > 0


def test_straight_line_is_not_degenerate():
    values = [1, 3, 5, 7, 9, 11]
    assert imr.moving_ranges(values) == [2, 2, 2, 2, 2]
    assert imr.mr_chart_stats(values).sigma == pytest.approx(0.7557 * 2)
    assert imr.i_chart_stats(values).sigma == pytest.approx(2 / 1.128)


def test_mr_chart_stats_identical_values_give_zero_sigma():
    stats = imr.mr_chart_stats([5, 5, 5])
    assert stats.mr_bar == 0.0
    assert stats.sigma == 0.0


def test_lines_below_zero_none_on_positive_i_chart():
    assert imr.lines_below_zero(imr.i_chart_stats([50, 51, 49, 50, 52])) == []
