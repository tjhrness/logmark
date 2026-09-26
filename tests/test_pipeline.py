"""Analysis pipeline tests (SPEC.md §4.6, §6.6, §7.1, §8): analyse_column, analyse,
the V10 rejection and the W01 warning."""

from datetime import datetime

import pytest

import imr

A_VALUES = [10.2, 11.5, 9.8, 10.9, 12.1, 10.4, 9.6, 11.0, 10.7, 13.9,
            10.1, 9.9, 11.3, 10.6, 10.0, 12.4, 11.8, 9.5, 10.3, 10.8,
            11.1, 9.7, 10.5, 12.0, 10.2]
B_VALUES = [5.0, 5.4, 4.8, 5.1, 5.6, 5.2, 4.9, 5.3, 5.0, 5.5,
            5.1, 4.7, 5.2, 5.8, 5.0, 5.3, 4.9, 5.4, 5.1, 5.0,
            5.6, 5.2, 4.8, 5.3, 5.1]
LINE_VALUES = [float(v) for v in range(1, 50, 2)]  # 1, 3, 5, ..., 49 (25 rows)
SAME_VALUES = [7.25] * 25


def csv_bytes(columns: dict[str, list[float]]) -> bytes:
    names = list(columns)
    rows = [",".join(names)]
    for i in range(len(columns[names[0]])):
        rows.append(",".join(repr(columns[name][i]) for name in names))
    return ("\n".join(rows) + "\n").encode("utf-8")


def run(columns: dict[str, list[float]], analysed_at=None) -> imr.AnalysisResult:
    parsed = imr.parse_csv(csv_bytes(columns), "sample.csv")
    return imr.analyse(parsed, analysed_at=analysed_at)


@pytest.fixture(scope="module")
def two_columns():
    return run({"IMR_Field_A": A_VALUES, "IMR_Field_B": B_VALUES})


def test_two_column_file_analyses_fully(two_columns):
    cols = two_columns.columns
    assert [c.name for c in cols] == ["IMR_Field_A", "IMR_Field_B"]
    assert [c.index for c in cols] == [0, 1]
    for col in cols:
        assert col.n == 25
        assert col.warning is None
        assert col.rejected_reason is None
        assert col.individuals is not None and col.moving_range is not None
        assert col.individuals.kind == "I"
        assert col.moving_range.kind == "MR"
        assert col.individuals.point_numbers == list(range(1, 26))
        assert col.moving_range.point_numbers == list(range(2, 26))
        assert col.individuals.stats.n == 25
        assert col.moving_range.stats.n == 24
        assert len(col.individuals.png) > 0
        assert len(col.moving_range.png) > 0
        assert col.individuals.png.startswith(b"\x89PNG")


def test_pattern_points_and_observation_labels(two_columns):
    for col in two_columns.columns:
        for chart, kind in ((col.individuals, "I"), (col.moving_range, "MR")):
            union = {p for o in chart.observations for p in o.points}
            assert chart.pattern_points == union
            for o in chart.observations:
                assert o.field == col.name
                assert o.chart == kind


def test_sigma_follows_moving_range_method(two_columns):
    col = two_columns.columns[0]
    mrs = [abs(A_VALUES[i] - A_VALUES[i - 1]) for i in range(1, len(A_VALUES))]
    mr_bar = sum(mrs) / len(mrs)
    assert col.individuals.stats.mr_bar == pytest.approx(mr_bar)
    assert col.individuals.stats.mean == pytest.approx(sum(A_VALUES) / len(A_VALUES))
    assert col.individuals.stats.sigma == pytest.approx(mr_bar / 1.128)
    assert col.moving_range.stats.sigma == pytest.approx(0.7557 * mr_bar)
    assert col.moving_range.stats.mean == pytest.approx(mr_bar)
    assert col.moving_range.values == pytest.approx(mrs)


def test_identical_column_rejected_v10_other_column_proceeds():
    result = run({"IMR_Field_Same": SAME_VALUES, "IMR_Field_A": A_VALUES})
    same, other = result.columns
    assert same.rejected_reason == (
        "All 25 values in IMR_Field_Same are identical (7.250), so there is no variation "
        "to chart and no limits can be drawn for this column.")
    assert same.individuals is None and same.moving_range is None
    assert same.n == 25
    assert other.rejected_reason is None
    assert other.individuals is not None and other.moving_range is not None
    assert "IMR_Field_Same" not in result.observations_csv


def test_straight_line_is_charted_not_rejected():
    result = run({"IMR_Field_Line": LINE_VALUES})
    col = result.columns[0]
    assert col.rejected_reason is None
    rule_3 = [o for o in col.individuals.observations if o.rule_no == 3]
    assert any(o.direction == "rising" and o.points == list(range(1, 26)) for o in rule_3)
    mr_obs = col.moving_range.observations
    assert len(mr_obs) == 1
    assert mr_obs[0].rule_no == 7
    assert mr_obs[0].points == list(range(2, 26))


def test_small_sample_carries_w01_on_every_column():
    result = run({"IMR_Field_A": A_VALUES[:15], "IMR_Field_B": B_VALUES[:15]})
    for col in result.columns:
        assert col.n == 15
        assert col.warning == imr.warning_text(15)
        assert "Only 15 points" in col.warning
        assert col.rejected_reason is None
        assert col.individuals is not None and col.moving_range is not None
        assert len(col.individuals.png) > 0


def test_small_sample_still_detects_patterns():
    result = run({"IMR_Field_Line": LINE_VALUES[:15]})
    col = result.columns[0]
    assert col.warning is not None
    assert col.individuals.observations
    # 14 identical moving ranges: one short of Rule 7's fifteen, so the MR chart is quiet
    assert col.moving_range.observations == []


def test_csv_and_report_built_once_from_columns(two_columns):
    assert two_columns.observations_csv == imr.build_observations_csv(two_columns.columns)
    for col in two_columns.columns:
        assert col.name in two_columns.report_html
    assert "/download/" not in two_columns.report_html
    assert two_columns.source_filename == "sample.csv"
    assert two_columns.stem == "sample"


def test_analysed_at_timestamp_in_report():
    when = datetime(2026, 9, 26, 14, 30, 5)
    result = run({"IMR_Field_A": A_VALUES}, analysed_at=when)
    assert result.analysed_at == when
    assert "2026-09-26 14:30:05" in result.report_html
    assert imr.timestamp_text(when) == "2026-09-26 14:30:05"


def test_analysed_at_defaults_to_now():
    before = datetime.now().replace(microsecond=0)
    result = run({"IMR_Field_A": A_VALUES})
    assert result.analysed_at >= before


def test_deterministic_same_input_twice():
    first = run({"IMR_Field_A": A_VALUES, "IMR_Field_Line": LINE_VALUES})
    second = run({"IMR_Field_A": A_VALUES, "IMR_Field_Line": LINE_VALUES})
    assert first.observations_csv == second.observations_csv
    for a, b in zip(first.columns, second.columns):
        assert a.individuals.png == b.individuals.png
        assert a.moving_range.png == b.moving_range.png


# ----- Step 22 audit: performance (SPEC.md §2.3) -----

import time


def performance_csv() -> bytes:
    columns = 10
    names = [f"IMR_Field_C{c}" for c in range(columns)]
    rows = [",".join(names)]
    for i in range(100):
        rows.append(",".join(repr(50 + ((i * 7 + c * 3) % 11) / 4) for c in range(columns)))
    return ("\n".join(rows) + "\n").encode("utf-8")


def test_ten_columns_by_one_hundred_rows_is_fast_enough():
    data = performance_csv()
    start = time.perf_counter()
    parsed = imr.parse_csv(data, "perf.csv")
    parsed_at = time.perf_counter()
    result = imr.analyse(parsed)
    done = time.perf_counter()
    parse_seconds = parsed_at - start
    total_seconds = done - start
    print(f"\nperformance: parse_csv {parse_seconds:.3f} s, parse_csv + analyse {total_seconds:.3f} s")
    assert len(result.columns) == 10
    assert all(col.n == 100 and col.rejected_reason is None for col in result.columns)
    assert parse_seconds < 1.0
    assert total_seconds < 5.0
