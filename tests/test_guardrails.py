"""Guardrail tests: mechanically enforce the non-negotiable rules in CLAUDE.md."""

import dataclasses
import re
from pathlib import Path

import imr

SOURCE = (Path(__file__).resolve().parent.parent / "imr.py").read_text(encoding="utf-8")

BANNERS = [
    "# ===== SECTION 1: CONSTANTS =====",
    "# ===== SECTION 2: DATA CLASSES =====",
    "# ===== SECTION 3: PARSING AND VALIDATION =====",
    "# ===== SECTION 4: STATISTICS =====",
    "# ===== SECTION 5: RULE ENGINE =====",
    "# ===== SECTION 6: RENDERING =====",
    "# ===== SECTION 7: REPORT AND CSV BUILDERS =====",
    "# ===== SECTION 8: FLASK APP AND ROUTES =====",
    "# ===== SECTION 9: ENTRY POINT =====",
]


def number_pattern(number: str) -> re.Pattern:
    """Match a number as a standalone token: no digit or dot directly before or after."""
    return re.compile(r"(?<![\d.])" + re.escape(number) + r"(?![\d.])")


def banner_line_positions() -> list[int]:
    lines = SOURCE.splitlines()
    positions = []
    for banner in BANNERS:
        hits = [i for i, line in enumerate(lines) if line == banner]
        assert len(hits) == 1, f"banner {banner!r} found {len(hits)} times, expected once"
        positions.append(hits[0])
    return positions


def test_banners_present_once_in_order():
    positions = banner_line_positions()
    assert positions == sorted(positions)


def test_sigma_constants_values():
    assert imr.D2_CONSTANT == 1.128
    assert imr.MR_SIGMA_FACTOR == 0.7557


def test_sigma_constants_defined_once_in_section_1():
    section_2_start = SOURCE.index(BANNERS[1])
    for number in ("1.128", "0.7557"):
        hits = list(number_pattern(number).finditer(SOURCE))
        assert len(hits) == 1, f"{number} appears {len(hits)} times, expected once"
        assert hits[0].start() < section_2_start, f"{number} is not in section 1"


def test_number_pattern_ignores_longer_numbers():
    pattern = number_pattern("1.128")
    assert pattern.search("x = 1.128") is not None
    assert pattern.search("x = 11.128") is None
    assert pattern.search("x = 1.1280") is None


def test_rounded_shortcuts_absent():
    for number in ("2.66", "3.267"):
        assert number_pattern(number).search(SOURCE) is None, f"shortcut {number} found in imr.py"


def test_plain_sample_sd_words_absent():
    lowered = SOURCE.lower()
    for word in ("stdev", "pstdev", "variance"):
        assert word not in lowered, f"forbidden word {word!r} found in imr.py"


def test_no_pandas_or_numpy_import():
    for line in SOURCE.splitlines():
        stripped = line.strip()
        assert not re.match(r"(import|from)\s+pandas\b", stripped), line
        assert not re.match(r"(import|from)\s+numpy\b", stripped), line
        assert not re.match(r"import\s+.*,\s*(pandas|numpy)\b", stripped), line


def test_flask_not_imported_before_section_8():
    before = SOURCE[: SOURCE.index(BANNERS[7])]
    assert re.search(r"^\s*(import\s+flask|from\s+flask)\b", before, re.MULTILINE) is None


def test_rule_threshold_constants():
    expected = {
        "RULE_2_MIN_RUN": 9,
        "RULE_3_MIN_RUN": 6,
        "RULE_4_MIN_RUN": 14,
        "RULE_5_WINDOW": 3,
        "RULE_5_MIN_COUNT": 2,
        "RULE_6_WINDOW": 5,
        "RULE_6_MIN_COUNT": 4,
        "RULE_7_MIN_RUN": 15,
        "RULE_8_MIN_RUN": 8,
    }
    for name, value in expected.items():
        assert getattr(imr, name) == value, name


def test_rule_names():
    assert imr.RULE_NAMES == {
        1: "One point beyond 3 SD",
        2: "Nine or more points on one side of the mean",
        3: "Six or more points steadily rising or falling",
        4: "Fourteen or more points alternating up and down",
        5: "Two of three points beyond 2 SD (same side)",
        6: "Four of five points beyond 1 SD (same side)",
        7: "Fifteen or more points within 1 SD of the mean",
        8: "Eight or more points beyond 1 SD, either side",
    }


def test_other_constants():
    assert imr.ON_LINE_TOLERANCE == 1e-9
    assert imr.IMR_PREFIX == "IMR_Field"
    assert imr.MAX_UPLOAD_BYTES == 10 * 1024 * 1024
    assert imr.MIN_DATA_ROWS == 3
    assert imr.WARN_BELOW_POINTS == 20
    assert imr.MAX_BAD_CELLS_LISTED == 20
    assert imr.DECIMALS == 3
    assert imr.FIG_MIN_WIDTH_IN == 10.0
    assert imr.FIG_WIDTH_PER_POINT_IN == 0.2
    assert imr.FIG_HEIGHT_IN == 4.5
    assert imr.FIG_DPI == 100
    assert imr.TICK_EVERY_POINT_UP_TO == 50
    assert imr.PORT_CANDIDATES == range(5000, 5011)
    assert imr.LINE_KS == (-3, -2, -1, 0, 1, 2, 3)


EXPECTED_FIELDS = {
    "Series": ["point_numbers", "values"],
    "Observation": [
        "field", "chart", "rule_no", "rule_name", "direction", "points",
        "values", "span", "line_or_window", "description",
    ],
    "ChartStats": ["n", "mean", "mr_bar", "sigma", "lines"],
    "ChartResult": [
        "kind", "point_numbers", "values", "stats", "observations", "pattern_points", "png",
    ],
    "ColumnResult": [
        "name", "index", "n", "warning", "rejected_reason", "individuals", "moving_range",
    ],
    "AnalysisResult": [
        "source_filename", "stem", "analysed_at", "columns", "report_html", "observations_csv",
    ],
    "ValidationIssue": ["code", "severity", "message"],
    "ParsedColumn": ["name", "index", "values"],
    "ParsedFile": ["source_filename", "stem", "n_rows", "columns"],
}


def test_dataclass_fields():
    for class_name, field_names in EXPECTED_FIELDS.items():
        cls = getattr(imr, class_name)
        assert dataclasses.is_dataclass(cls), class_name
        assert [f.name for f in dataclasses.fields(cls)] == field_names, class_name


def test_validation_errors():
    assert issubclass(imr.ValidationErrors, Exception)
    issues = [
        imr.ValidationIssue("F01", "F", "First problem."),
        imr.ValidationIssue("C02", "C", "Second problem."),
    ]
    error = imr.ValidationErrors(issues)
    assert error.issues == issues
    text = str(error)
    assert "First problem." in text
    assert "Second problem." in text


def test_never_binds_to_all_interfaces():
    assert "0.0.0.0" not in SOURCE


# ----- Step 22 audit: further mechanical checks of CLAUDE.md -----

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


def import_lines() -> list[tuple[int, str]]:
    return [(i, line.strip()) for i, line in enumerate(SOURCE.splitlines())
            if re.match(r"\s*(import|from)\s+\w", line)]


def imported_top_level_modules() -> set[str]:
    modules = set()
    for _, line in import_lines():
        match = re.match(r"from\s+([\w.]+)\s+import\b", line)
        if match:
            modules.add(match.group(1).split(".")[0])
            continue
        for part in re.match(r"import\s+(.+)", line).group(1).split(","):
            modules.add(part.strip().split()[0].split(".")[0])
    return modules


def test_application_is_one_python_file_at_the_root():
    assert sorted(p.name for p in REPO_ROOT.glob("*.py")) == ["imr.py"]


def test_flask_imported_only_inside_section_8():
    lines = SOURCE.splitlines()
    start, end = banner_line_positions()[7], banner_line_positions()[8]
    flask_lines = [i for i, line in import_lines() if re.match(r"(import|from)\s+flask\b", line)]
    assert flask_lines, "Flask is never imported"
    assert all(start < i < end for i in flask_lines), [lines[i] for i in flask_lines]


def test_only_standard_library_flask_and_matplotlib_imported():
    allowed = set(sys.stdlib_module_names) | {"flask", "matplotlib"}
    assert imported_top_level_modules() <= allowed, imported_top_level_modules() - allowed


def test_matplotlib_agg_backend_chosen_before_pyplot():
    assert 'matplotlib.use("Agg")' in SOURCE
    assert SOURCE.index('matplotlib.use("Agg")') < SOURCE.index("import matplotlib.pyplot")


def test_no_network_client_modules_imported():
    forbidden = {"urllib", "http", "requests", "httpx", "ftplib", "smtplib", "ssl"}
    assert imported_top_level_modules().isdisjoint(forbidden)


def test_only_url_is_the_local_address_in_section_9():
    section_9 = banner_line_positions()[8]
    lines = SOURCE.splitlines()
    for i, line in enumerate(lines):
        for match in re.finditer(r"https?://[^\s\"'{]*", line):
            assert match.group(0) == "http://127.0.0.1:", line
            assert i > section_9, line


def test_server_binds_to_localhost_only():
    hosts = re.findall(r"host\s*[:=]\s*(?:str\s*=\s*)?\"([^\"]*)\"", SOURCE)
    assert hosts and set(hosts) == {"127.0.0.1"}


def test_writes_no_files():
    assert re.search(r"(?<![\w.])open\(", SOURCE) is None
    for forbidden in (".write_text(", ".write_bytes(", "os.remove", "shutil", "tempfile",
                      "NamedTemporaryFile", "mkdir("):
        assert forbidden not in SOURCE, forbidden
    for call in re.findall(r"savefig\(([^,]+),", SOURCE):
        assert call.strip() == "buf", call


def test_no_unicode_minus_sign():
    assert "−" not in SOURCE


def test_mr_chart_runs_every_rule_not_just_rule_1():
    # A straight line gives constant moving ranges: Rule 7 must fire on the MR chart.
    values = [float(v) for v in range(1, 40, 2)]
    parsed = imr.ParsedFile("f.csv", "f", len(values), [imr.ParsedColumn("IMR_Field_L", 0, values)])
    column = imr.analyse(parsed).columns[0]
    assert {o.rule_no for o in column.moving_range.observations} == {7}
