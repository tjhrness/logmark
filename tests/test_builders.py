"""Report and CSV builder tests (SPEC.md §6.7): the observations CSV."""

import csv
import io

import imr

HEADER = "field,chart,rule_no,rule_name,direction,points,values,line_or_window,description"
L = imr.lines_for(0.0, 1.0)
STATS = imr.ChartStats(n=3, mean=0.0, mr_bar=1.0, sigma=1.0, lines=L)


def obs(field, chart, rule_no, points, values, description="d", direction="above",
        line_or_window="+3 SD=3.000"):
    return imr.Observation(
        field=field, chart=chart, rule_no=rule_no, rule_name=imr.RULE_NAMES[rule_no],
        direction=direction, points=points, values=values,
        span=(points[0], points[-1]), line_or_window=line_or_window,
        description=description,
    )


def chart(kind, observations):
    return imr.ChartResult(kind=kind, point_numbers=[1, 2, 3], values=[0.0, 0.0, 0.0],
                           stats=STATS, observations=observations,
                           pattern_points=imr.pattern_points(observations), png=b"")


def column(name, index, i_obs, mr_obs, rejected_reason=None):
    if rejected_reason is not None:
        return imr.ColumnResult(name=name, index=index, n=3, warning=None,
                                rejected_reason=rejected_reason,
                                individuals=None, moving_range=None)
    return imr.ColumnResult(name=name, index=index, n=3, warning=None,
                            rejected_reason=None,
                            individuals=chart("I", i_obs), moving_range=chart("MR", mr_obs))


def rows_of(text):
    return list(csv.reader(io.StringIO(text)))


# ----- points_field -----

def test_points_field_single():
    assert imr.points_field([17]) == "17"


def test_points_field_consecutive_run():
    assert imr.points_field([14, 15, 16]) == "14-16"


def test_points_field_two_consecutive():
    assert imr.points_field([3, 4]) == "3-4"


def test_points_field_non_consecutive():
    assert imr.points_field([7, 9]) == "7,9"


def test_points_field_partly_consecutive():
    assert imr.points_field([1, 3, 4]) == "1,3,4"


# ----- build_observations_csv -----

def test_header_row_exactly():
    text = imr.build_observations_csv([])
    assert text.split("\n")[0] == HEADER


def test_no_observations_gives_header_only():
    text = imr.build_observations_csv([column("IMR_Field_A", 0, [], [])])
    assert text == HEADER + "\n"


def test_rows_column_by_column_i_before_mr_in_stored_order():
    a = column("IMR_Field_A", 0,
               [obs("IMR_Field_A", "I", 1, [4], [3.5]), obs("IMR_Field_A", "I", 2, [1, 2], [0.5, 0.5])],
               [obs("IMR_Field_A", "MR", 1, [3], [4.0])])
    b = column("IMR_Field_B", 1,
               [obs("IMR_Field_B", "I", 5, [2, 3], [2.5, 2.5])],
               [obs("IMR_Field_B", "MR", 6, [2, 3, 4, 5], [1.5, 1.5, 1.5, 1.5])])
    rows = rows_of(imr.build_observations_csv([a, b]))
    assert rows[0] == HEADER.split(",")
    assert [(r[0], r[1], r[2]) for r in rows[1:]] == [
        ("IMR_Field_A", "I", "1"),
        ("IMR_Field_A", "I", "2"),
        ("IMR_Field_A", "MR", "1"),
        ("IMR_Field_B", "I", "5"),
        ("IMR_Field_B", "MR", "6"),
    ]
    assert rows[2][3] == imr.RULE_NAMES[2]
    assert rows[5][5] == "2-5"


def test_values_three_decimals_semicolon_ascii_minus():
    c = column("IMR_Field_A", 0,
               [obs("IMR_Field_A", "I", 1, [7, 9], [41.1, -3.25], direction="below")], [])
    rows = rows_of(imr.build_observations_csv([c]))
    assert rows[1][5] == "7,9"
    assert rows[1][6] == "41.100;-3.250"
    assert "−" not in rows[1][6]


def test_description_with_commas_and_em_dash_round_trips():
    desc = "Rule 5 — Two of three points beyond 2 SD: points 1, 3 (values 2.500, 2.500); window 1–3."
    c = column("IMR_Field_A", 0,
               [obs("IMR_Field_A", "I", 5, [1, 3], [2.5, 2.5], description=desc,
                    line_or_window="+2 SD=2.000; window 1-3")], [])
    text = imr.build_observations_csv([c])
    round_tripped = rows_of(text.encode("utf-8").decode("utf-8"))
    assert round_tripped[1][8] == desc
    assert round_tripped[1][7] == "+2 SD=2.000; window 1-3"
    assert len(round_tripped[1]) == 9


def test_rejected_column_contributes_no_rows():
    good = column("IMR_Field_A", 0, [obs("IMR_Field_A", "I", 1, [4], [3.5])], [])
    bad = column("IMR_Field_B", 1, [], [], rejected_reason="Too few values.")
    rows = rows_of(imr.build_observations_csv([bad, good]))
    assert len(rows) == 2
    assert rows[1][0] == "IMR_Field_A"


def test_warnings_never_appear():
    c = column("IMR_Field_A", 0, [obs("IMR_Field_A", "I", 1, [4], [3.5])], [])
    c.warning = "WARNING TEXT"
    assert "WARNING TEXT" not in imr.build_observations_csv([c])


def test_lines_end_with_plain_newline():
    c = column("IMR_Field_A", 0, [obs("IMR_Field_A", "I", 1, [4], [3.5])], [])
    text = imr.build_observations_csv([c])
    assert "\r" not in text
    assert text.endswith("\n")


def test_e11_real_observation_row():
    series = imr.individuals_series([2.5, 0, 2.5, 2.5, 0, 0])
    found = imr.detect_all(series, L, field="IMR_Field_T", chart="I")
    c = column("IMR_Field_T", 0, found, [])
    rows = rows_of(imr.build_observations_csv([c]))
    assert rows[1:] == [[
        "IMR_Field_T", "I", "5", "Two of three points beyond 2 SD (same side)", "above",
        "1,3,4", "2.500;2.500;2.500", "+2 SD=2.000; window 1-5",
        "Rule 5 — Two of three points beyond 2 SD: points 1, 3, 4 "
        "(values 2.500, 2.500, 2.500) are above the +2 SD line (2.000); window 1–5.",
    ]]
