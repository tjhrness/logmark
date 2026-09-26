"""File-level parsing and validation tests (SPEC.md §3.1, §3.2, §6.6, §7.1 V02-V07)."""

import pytest

import imr


def codes(issues):
    return [issue.code for issue in issues]


# ----- well-formed file -----

def test_well_formed_file_with_bom():
    data = b"\xef\xbb\xbfIMR_Field_A,Label\n1,x\n2,y\n3,z\n"
    header, rows, issues = imr.read_table(data, "good.csv")
    assert header == ["IMR_Field_A", "Label"]
    assert rows == [["1", "x"], ["2", "y"], ["3", "z"]]
    assert issues == []


# ----- V02 -----

def test_v02_wrong_extension_is_raised():
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.read_table(b"IMR_Field_A\n1\n2\n3\n", "data.txt")
    issues = exc.value.issues
    assert codes(issues) == ["V02"]
    assert issues[0].severity == "F"
    assert issues[0].message == (
        "data.txt is not a .csv file. Only comma-separated .csv files are accepted."
    )


def test_upper_case_extension_is_accepted():
    header, rows, issues = imr.read_table(b"IMR_Field_A\n1\n2\n3\n", "DATA.CSV")
    assert header == ["IMR_Field_A"]
    assert issues == []


# ----- V03 -----

def test_v03_too_large_is_raised():
    data = b"a" * (imr.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.read_table(data, "big.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V03"]
    assert issues[0].severity == "F"
    assert "big.csv" in issues[0].message
    assert "10 MB" in issues[0].message


# ----- V04 -----

def test_v04_not_utf8_is_raised():
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.read_table(b"IMR_Field_A\n\xff\xfe\n", "bad.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V04"]
    assert issues[0].severity == "F"
    assert "bad.csv" in issues[0].message
    assert "CSV UTF-8" in issues[0].message


# ----- V05 -----

def test_v05_no_matching_header_lists_columns():
    header, rows, issues = imr.read_table(b"Sales,Cost\n1,2\n3,4\n", "f.csv")
    assert codes(issues) == ["V05"]
    assert issues[0].severity == "F"
    assert "Columns present: Sales, Cost." in issues[0].message
    assert rows == [["1", "2"], ["3", "4"]]


def test_v05_empty_file():
    header, rows, issues = imr.read_table(b"", "empty.csv")
    assert header == []
    assert rows == []
    assert codes(issues) == ["V05"]
    assert "(none)" in issues[0].message


def test_v05_prefix_is_case_sensitive():
    header, rows, issues = imr.read_table(b"imr_field_x\n1\n2\n3\n", "f.csv")
    assert codes(issues) == ["V05"]


def test_padded_header_is_stripped_and_accepted():
    header, rows, issues = imr.read_table(b" IMR_Field_A ,B\n1,2\n", "f.csv")
    assert header == ["IMR_Field_A", "B"]
    assert issues == []


# ----- V06 -----

def test_v06_duplicate_imr_column():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,IMR_Field_A\n1,2\n3,4\n", "f.csv"
    )
    assert codes(issues) == ["V06"]
    assert issues[0].severity == "F"
    assert issues[0].message == (
        "Column name IMR_Field_A appears more than once. "
        "Make every IMR_Field column name unique."
    )


def test_duplicate_non_imr_column_is_fine():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,Note,Note\n1,a,b\n2,c,d\n", "f.csv"
    )
    assert issues == []


# ----- V07 -----

def test_v07_names_row_with_extra_cell():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,B\n1,2\n3,4,5\n6,7\n", "f.csv"
    )
    assert codes(issues) == ["V07"]
    assert issues[0].message == (
        "Row 3 has 3 cells but the header has 2. "
        "Fix the row (a stray comma or a missing value is the usual cause)."
    )


def test_v07_blank_line_between_rows_is_a_ragged_row():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,B\n1,2\n\n6,7\n", "f.csv"
    )
    assert codes(issues) == ["V07"]
    assert "Row 3 has 0 cells" in issues[0].message
    assert len(rows) == 3


def test_blank_lines_at_end_are_ignored():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,B\n1,2\n3,4\n\n\r\n\n", "f.csv"
    )
    assert rows == [["1", "2"], ["3", "4"]]
    assert issues == []


def test_v07_lists_twenty_rows_then_a_summary():
    body = b"".join(b"1,2,3\n" for _ in range(25))
    header, rows, issues = imr.read_table(b"IMR_Field_A,B\n" + body, "f.csv")
    assert codes(issues) == ["V07"] * 21
    assert "Row 2 has 3 cells" in issues[0].message
    assert "Row 21 has 3 cells" in issues[19].message
    assert issues[20].message == (
        "… and 5 more rows with the wrong number of cells."
    )


# ----- combined -----
# V05 (no IMR_Field header) and V06 (a duplicated IMR_Field header) cannot both be
# true of one file, so the "all together" check is made with the two combinations
# that can occur: V06 with V07, and V05 with V07.

def test_v06_and_v07_returned_together_with_rows():
    header, rows, issues = imr.read_table(
        b"IMR_Field_A,IMR_Field_A\n1,2\n3\n", "f.csv"
    )
    assert set(codes(issues)) == {"V06", "V07"}
    assert rows == [["1", "2"], ["3"]]
    assert all(issue.severity == "F" for issue in issues)


def test_v05_and_v07_returned_together_with_rows():
    header, rows, issues = imr.read_table(b"Sales,Cost\n1,2\n3\n", "f.csv")
    assert set(codes(issues)) == {"V05", "V07"}
    assert rows == [["1", "2"], ["3"]]
    assert all(issue.severity == "F" for issue in issues)


# ----- filenames (SPEC.md §6.6) -----

def test_sanitise_name():
    assert imr.sanitise_name("Sales (EU) %") == "Sales__EU___"
    assert imr.sanitise_name("ok_Name-1") == "ok_Name-1"


def test_stem_of_windows_path():
    assert imr.stem_of("C:\\data\\Q3 data.csv") == "Q3_data"


def test_stem_of_plain_name():
    assert imr.stem_of("Q3 data.csv") == "Q3_data"
