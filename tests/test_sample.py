"""Bundled sample dataset tests (SPEC.md §11.1-11.3): sample/sample_imr.csv charts
nine columns, each IMR_Field_RuleK triggers Rule K on its I chart, and
IMR_Field_Clean triggers nothing on either chart."""

import csv
import io
import re
from pathlib import Path

import pytest

import imr

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "sample" / "sample_imr.csv"

EXPECTED_COLUMNS = [f"IMR_Field_Rule{k}" for k in range(1, 9)] + ["IMR_Field_Clean"]

TWO_DECIMALS_RE = re.compile(r"^-?\d+(\.\d{1,2})?$")


@pytest.fixture(scope="module")
def parsed():
    return imr.parse_csv(SAMPLE_PATH.read_bytes(), "sample_imr.csv")


@pytest.fixture(scope="module")
def result(parsed):
    return imr.analyse(parsed)


def column(result, name):
    return next(col for col in result.columns if col.name == name)


def test_nine_charted_columns_in_order(parsed, result):
    assert [col.name for col in parsed.columns] == EXPECTED_COLUMNS
    assert [col.name for col in result.columns] == EXPECTED_COLUMNS
    assert "Notes" not in [col.name for col in result.columns]
    assert parsed.n_rows == 40


def test_no_column_rejected_or_warned(result):
    for col in result.columns:
        assert col.rejected_reason is None, col.name
        assert col.warning is None, col.name
        assert col.n == 40


@pytest.mark.parametrize("k", range(1, 9))
def test_rule_column_triggers_its_rule_on_i_chart(result, k):
    col = column(result, f"IMR_Field_Rule{k}")
    assert any(obs.rule_no == k for obs in col.individuals.observations)


def test_clean_column_triggers_nothing(result):
    col = column(result, "IMR_Field_Clean")
    assert col.individuals.observations == []
    assert col.moving_range.observations == []


def test_file_is_utf8_without_bom():
    data = SAMPLE_PATH.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    data.decode("utf-8")


def test_charted_values_have_at_most_two_decimals():
    text = SAMPLE_PATH.read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], rows[1:]
    assert len(body) == 40
    charted = [i for i, name in enumerate(header) if name.startswith(imr.IMR_PREFIX)]
    assert len(charted) == 9
    for row in body:
        for i in charted:
            assert TWO_DECIMALS_RE.match(row[i]), (header[i], row[i])


# ----- acceptance test: the answer key (SPEC.md §11.4, §12.8) -----

ANSWER_KEY_PATH = SAMPLE_PATH.parent / "sample_answer_key.csv"

CSV_HEADER = ["field", "chart", "rule_no", "rule_name", "direction", "points", "values",
              "line_or_window", "description"]


def read_rows(text):
    return list(csv.reader(io.StringIO(text)))


def test_observations_csv_matches_answer_key_row_for_row(result):
    key_rows = read_rows(ANSWER_KEY_PATH.read_text(encoding="utf-8"))
    tool_rows = read_rows(result.observations_csv)
    assert len(tool_rows) == len(key_rows)
    for i, (tool_row, key_row) in enumerate(zip(tool_rows, key_rows)):
        assert tool_row == key_row, f"row {i} differs"


def test_answer_key_shape():
    key_rows = read_rows(ANSWER_KEY_PATH.read_text(encoding="utf-8"))
    assert key_rows[0] == CSV_HEADER
    body = key_rows[1:]
    assert {row[2] for row in body} >= {str(k) for k in range(1, 9)}
    assert not any(row[0] == "IMR_Field_Clean" for row in body)
