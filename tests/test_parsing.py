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


# ----- parse_number (SPEC.md §3.3) -----

@pytest.mark.parametrize("text, expected", [
    ("12.5", 12.5),
    ("  12.5  ", 12.5),
    ("-3.2e2", -320.0),
    (".5", 0.5),
    ("5.", 5.0),
    ("+7", 7.0),
    ("0", 0.0),
])
def test_parse_number_accepts_plain_numbers(text, expected):
    assert imr.parse_number(text) == expected


@pytest.mark.parametrize("text", [
    "", "  ", "1,234", "$5", "5%", "abc", "nan", "NaN", "inf", "-Infinity",
    "1e", "--1",
])
def test_parse_number_rejects_everything_else(text):
    assert imr.parse_number(text) is None


# ----- parse_csv -----

def test_parse_csv_good_file_keeps_imr_columns_in_file_order():
    data = (
        b"Notes,IMR_Field_B,Other,IMR_Field_A\n"
        b"a,1.5,x,10\n"
        b"b,2,y,-20\n"
        b"c,3e1,z,30.25\n"
        b"d,4,w,0\n"
    )
    parsed = imr.parse_csv(data, "C:\\data\\My Line 1.csv")
    assert isinstance(parsed, imr.ParsedFile)
    assert parsed.source_filename == "C:\\data\\My Line 1.csv"
    assert parsed.stem == "My_Line_1"
    assert parsed.n_rows == 4
    assert [c.name for c in parsed.columns] == ["IMR_Field_B", "IMR_Field_A"]
    assert [c.index for c in parsed.columns] == [0, 1]
    assert parsed.columns[0].values == [1.5, 2.0, 30.0, 4.0]
    assert parsed.columns[1].values == [10.0, -20.0, 30.25, 0.0]
    assert all(isinstance(v, float) for c in parsed.columns for v in c.values)


def test_parse_csv_ignores_garbage_in_non_imr_columns():
    data = (
        b'Notes,IMR_Field_A\n'
        b'"hello, world",1\n'
        b',2\n'
        b'nan,3\n'
        b'"1,234 $5 5%",4\n'
    )
    parsed = imr.parse_csv(data, "notes.csv")
    assert parsed.n_rows == 4
    assert parsed.columns[0].values == [1.0, 2.0, 3.0, 4.0]


def test_v08_blank_cell_names_column_row_and_point():
    # A blank line in a one-column file is a ragged row (V07), so a second column
    # is used to get a genuinely blank cell.
    data = b"IMR_Field_A,Label\n1,a\n,b\n3,c\n4,d\n"
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(data, "f.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V08"]
    assert issues[0].severity == "F"
    assert issues[0].message == (
        'Column IMR_Field_A, row 3 (point 2) contains "", which is not a '
        "number. Every cell in an IMR_Field column must be a plain number."
    )


@pytest.mark.parametrize("bad", [b"nan", b'"1,234"'])
def test_v08_rejects_nan_and_thousands_separator(bad):
    data = b"IMR_Field_A,Label\n1,a\n" + bad + b",b\n3,c\n"
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(data, "f.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V08"]
    shown = bad.decode().strip('"')
    assert f'contains "{shown}"' in issues[0].message
    assert "row 3 (point 2)" in issues[0].message


def test_v08_several_bad_cells_reported_column_by_column():
    data = (
        b"IMR_Field_A,IMR_Field_B\n"
        b"1,x\n"
        b"abc,2\n"
        b"3,y\n"
        b"$4,4\n"
    )
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(data, "f.csv")
    messages = [issue.message for issue in exc.value.issues]
    assert codes(exc.value.issues) == ["V08"] * 4
    assert messages[0].startswith('Column IMR_Field_A, row 3 (point 2) contains "abc"')
    assert messages[1].startswith('Column IMR_Field_A, row 5 (point 4) contains "$4"')
    assert messages[2].startswith('Column IMR_Field_B, row 2 (point 1) contains "x"')
    assert messages[3].startswith('Column IMR_Field_B, row 4 (point 3) contains "y"')


def test_v08_lists_twenty_cells_then_a_summary():
    body = b"".join(b"bad\n" for _ in range(25))
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(b"IMR_Field_A\n" + body, "f.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V08"] * 21
    assert "row 2 (point 1)" in issues[0].message
    assert "row 21 (point 20)" in issues[19].message
    assert issues[20].message == "… and 5 more cells that are not numbers."


def test_v09_two_data_rows_rejected():
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(b"IMR_Field_A\n1\n2\n", "f.csv")
    issues = exc.value.issues
    assert codes(issues) == ["V09"]
    assert issues[0].severity == "F"
    assert issues[0].message == (
        f"Only 2 data rows found; at least {imr.MIN_DATA_ROWS} are needed. "
        "Add more rows — 20 or more gives reliable limits."
    )


def test_exactly_three_data_rows_accepted():
    parsed = imr.parse_csv(b"IMR_Field_A\n1\n2\n3\n", "f.csv")
    assert parsed.n_rows == 3
    assert parsed.columns[0].values == [1.0, 2.0, 3.0]


def test_v05_and_v09_reported_together():
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(b"Label\nx\n", "f.csv")
    assert codes(exc.value.issues) == ["V05", "V09"]
    assert "Only 1 data rows found" in exc.value.issues[1].message


def test_v02_propagates_from_parse_csv_unchanged():
    with pytest.raises(imr.ValidationErrors) as exc:
        imr.parse_csv(b"IMR_Field_A\n1\n2\n3\n", "data.txt")
    issues = exc.value.issues
    assert codes(issues) == ["V02"]
    assert issues[0].severity == "F"


# ----- Step 22 audit: cell-level acceptance inside a whole file (SPEC.md §12.5) -----

def test_parse_csv_accepts_padded_and_exponent_cells():
    data = b"IMR_Field_A,Label\n 12.5 ,a\n-3.2e2,b\n  7  ,c\n"
    parsed = imr.parse_csv(data, "f.csv")
    assert parsed.columns[0].values == [12.5, -320.0, 7.0]


def test_parse_csv_with_bom_keeps_first_column_name():
    data = b"\xef\xbb\xbfIMR_Field_A,Label\n1,a\n2,b\n3,c\n"
    parsed = imr.parse_csv(data, "f.csv")
    assert [c.name for c in parsed.columns] == ["IMR_Field_A"]


def test_parse_csv_lower_case_prefix_column_is_not_charted():
    data = b"IMR_Field_A,imr_field_x\n1,junk\n2,junk\n3,junk\n"
    parsed = imr.parse_csv(data, "f.csv")
    assert [c.name for c in parsed.columns] == ["IMR_Field_A"]
