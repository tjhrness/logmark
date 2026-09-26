"""IMR Control Chart Tool: a personal, single-user, local web application that
takes an uploaded CSV file and draws an Individuals (I) chart and a Moving Range
(MR) chart for every column whose header starts with IMR_Field, applies all eight
Nelson rules to both charts and writes out every detected pattern. Run it with
"python imr.py" and test it with "pytest".
"""

import base64
import csv
import dataclasses
import html
import io
import re
import socket
import statistics
import sys
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ===== SECTION 1: CONSTANTS =====

# Nelson rule thresholds (standard values; never exposed in the interface, never changed).
RULE_2_MIN_RUN = 9
RULE_3_MIN_RUN = 6
RULE_4_MIN_RUN = 14
RULE_5_WINDOW = 3
RULE_5_MIN_COUNT = 2
RULE_6_WINDOW = 5
RULE_6_MIN_COUNT = 4
RULE_7_MIN_RUN = 15
RULE_8_MIN_RUN = 8

ON_LINE_TOLERANCE = 1e-9

IMR_PREFIX = "IMR_Field"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MIN_DATA_ROWS = 3
WARN_BELOW_POINTS = 20
MAX_BAD_CELLS_LISTED = 20

DECIMALS = 3

FIG_MIN_WIDTH_IN = 10.0
FIG_WIDTH_PER_POINT_IN = 0.2
FIG_HEIGHT_IN = 4.5
FIG_DPI = 100
TICK_EVERY_POINT_UP_TO = 50

PORT_CANDIDATES = range(5000, 5011)

LINE_KS = (-3, -2, -1, 0, 1, 2, 3)

# I-chart sigma = average moving range / D2_CONSTANT (SPEC.md §4.2)
D2_CONSTANT = 1.128
# MR-chart sigma = MR_SIGMA_FACTOR x average moving range (SPEC.md §4.3)
MR_SIGMA_FACTOR = 0.7557

RULE_NAMES: dict[int, str] = {
    1: "One point beyond 3 SD",
    2: "Nine or more points on one side of the mean",
    3: "Six or more points steadily rising or falling",
    4: "Fourteen or more points alternating up and down",
    5: "Two of three points beyond 2 SD (same side)",
    6: "Four of five points beyond 1 SD (same side)",
    7: "Fifteen or more points within 1 SD of the mean",
    8: "Eight or more points beyond 1 SD, either side",
}


# ===== SECTION 2: DATA CLASSES =====

@dataclass
class Series:
    point_numbers: list[int]
    values: list[float]


@dataclass
class Observation:
    field: str
    chart: str
    rule_no: int
    rule_name: str
    direction: str
    points: list[int]
    values: list[float]
    span: tuple[int, int]
    line_or_window: str
    description: str


@dataclass
class ChartStats:
    n: int
    mean: float  # centre line: the plain mean on the I chart, the average moving range on the MR chart
    mr_bar: float
    sigma: float
    lines: dict[int, float]


@dataclass
class ChartResult:
    kind: str
    point_numbers: list[int]
    values: list[float]
    stats: ChartStats
    observations: list[Observation]
    pattern_points: set[int]
    png: bytes


@dataclass
class ColumnResult:
    name: str
    index: int
    n: int
    warning: str | None
    rejected_reason: str | None
    individuals: ChartResult | None
    moving_range: ChartResult | None


@dataclass
class AnalysisResult:
    source_filename: str
    stem: str
    analysed_at: datetime
    columns: list[ColumnResult]
    report_html: str
    observations_csv: str


@dataclass
class ValidationIssue:
    code: str
    severity: str  # "F", "C" or "W"
    message: str


@dataclass
class ParsedColumn:
    name: str
    index: int  # 0-based position among the charted columns, in file order
    values: list[float]


@dataclass
class ParsedFile:
    source_filename: str
    stem: str
    n_rows: int
    columns: list[ParsedColumn]


class ValidationErrors(Exception):
    """Raised with every validation issue found in an upload."""

    def __init__(self, issues: list[ValidationIssue]):
        super().__init__(issues)
        self.issues = issues

    def __str__(self) -> str:
        return "\n".join(issue.message for issue in self.issues)


# ===== SECTION 3: PARSING AND VALIDATION =====

_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def sanitise_name(text: str) -> str:
    """Replace every character outside A-Z a-z 0-9 _ - with "_" (SPEC.md §6.6)."""
    return _UNSAFE_NAME_CHARS.sub("_", text)


def stem_of(filename: str) -> str:
    """The filename without directory or final extension, sanitised (SPEC.md §6.6)."""
    base = re.split(r"[\\/]", filename)[-1]
    if "." in base:
        base = base.rsplit(".", 1)[0]
    return sanitise_name(base)


def _fatal(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(code, "F", message)


def read_table(
    data: bytes, filename: str
) -> tuple[list[str], list[list[str]], list[ValidationIssue]]:
    """Turn uploaded bytes into (header, data_rows, issues) (SPEC.md §3.1, §3.2, §7.1).

    V02-V04 stop everything and are raised. V05-V07 are returned with the rows so
    that the cell checks can still run and every problem is reported in one go.
    """
    if not filename.lower().endswith(".csv"):
        raise ValidationErrors([_fatal(
            "V02",
            f"{filename} is not a .csv file. "
            "Only comma-separated .csv files are accepted.",
        )])
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationErrors([_fatal(
            "V03",
            f"{filename} is larger than 10 MB. "
            "This tool is built for files of a few hundred rows.",
        )])
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationErrors([_fatal(
            "V04",
            f"{filename} could not be read as UTF-8 text. "
            'Re-save it from Excel as "CSV UTF-8" and try again.',
        )]) from None

    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=","))
    # Blank lines after the last data row are left behind by Excel and editors.
    while rows and not rows[-1]:
        rows.pop()

    issues: list[ValidationIssue] = []
    header = [cell.strip() for cell in rows[0]] if rows else []
    data_rows = rows[1:]

    imr_names = [name for name in header if name.startswith(IMR_PREFIX)]
    if not imr_names:
        present = ", ".join(header) if header else "(none)"
        issues.append(_fatal(
            "V05",
            f"No column starting with {IMR_PREFIX} was found. "
            f"Columns present: {present}. "
            f"Rename the columns to chart so they start with {IMR_PREFIX}.",
        ))

    seen: set[str] = set()
    reported: set[str] = set()
    for name in imr_names:
        if name in seen and name not in reported:
            reported.add(name)
            issues.append(_fatal(
                "V06",
                f"Column name {name} appears more than once. "
                f"Make every {IMR_PREFIX} column name unique.",
            ))
        seen.add(name)

    ragged = [
        (row_number, len(row))
        for row_number, row in enumerate(data_rows, start=2)
        if len(row) != len(header)
    ]
    for row_number, cell_count in ragged[:MAX_BAD_CELLS_LISTED]:
        issues.append(_fatal(
            "V07",
            f"Row {row_number} has {cell_count} cells but the header has "
            f"{len(header)}. Fix the row (a stray comma or a missing value "
            "is the usual cause).",
        ))
    if len(ragged) > MAX_BAD_CELLS_LISTED:
        issues.append(_fatal(
            "V07",
            f"… and {len(ragged) - MAX_BAD_CELLS_LISTED} more rows "
            "with the wrong number of cells.",
        ))

    return header, data_rows, issues


# ===== SECTION 4: STATISTICS =====

def mean_of(values: list[float]) -> float:
    """Ordinary arithmetic mean."""
    return statistics.mean(values)


def moving_ranges(values: list[float]) -> list[float]:
    """|x_i - x_(i-1)| for i = 2 ... N: N - 1 numbers (SPEC.md §4.1)."""
    if len(values) < 2:
        raise ValueError("At least 2 values are needed to compute moving ranges.")
    return [abs(values[i] - values[i - 1]) for i in range(1, len(values))]


def lines_for(centre: float, sigma: float) -> dict[int, float]:
    """The seven lines centre + k x sigma, for k in LINE_KS."""
    return {k: centre + k * sigma for k in LINE_KS}


def i_chart_stats(values: list[float]) -> ChartStats:
    """Individuals-chart statistics (SPEC.md §4.2): sigma = MR-bar / D2_CONSTANT.

    Identical values give mr_bar = sigma = 0.0 and seven lines on the mean; the caller
    decides what a zero sigma means.
    """
    mean = mean_of(values)
    mr_bar = mean_of(moving_ranges(values))
    sigma = mr_bar / D2_CONSTANT
    return ChartStats(n=len(values), mean=mean, mr_bar=mr_bar, sigma=sigma, lines=lines_for(mean, sigma))


def individuals_series(values: list[float]) -> Series:
    """The I-chart series: points 1 ... N."""
    return Series(point_numbers=list(range(1, len(values) + 1)), values=list(values))


def moving_range_series(values: list[float]) -> Series:
    """The MR-chart series: points 2 ... N, aligned with the I chart. There is no MR point 1."""
    return Series(point_numbers=list(range(2, len(values) + 1)), values=moving_ranges(values))


def mr_chart_stats(values: list[float]) -> ChartStats:
    """Moving Range chart statistics from the ORIGINAL column values (SPEC.md §4.3).

    Centred on MR-bar, sigma = MR_SIGMA_FACTOR x MR-bar. Identical values give
    mr_bar = sigma = 0.0; the caller decides what a zero sigma means.
    """
    mrs = moving_ranges(values)
    mr_bar = mean_of(mrs)
    sigma = MR_SIGMA_FACTOR * mr_bar
    return ChartStats(n=len(mrs), mean=mr_bar, mr_bar=mr_bar, sigma=sigma, lines=lines_for(mr_bar, sigma))


def lines_below_zero(stats: ChartStats) -> list[int]:
    """The k values, ascending, whose line is strictly below 0 (computed, but not drawn)."""
    return sorted(k for k, value in stats.lines.items() if value < 0)


def fmt(x: float) -> str:
    """Display a number to exactly DECIMALS places, never as "-0.000". Display only."""
    text = f"{x:.{DECIMALS}f}"
    if text.startswith("-") and float(text) == 0:
        text = text[1:]
    return text



# ===== SECTION 5: RULE ENGINE =====

# Zone predicates (SPEC.md §5.1). Every rule compares values with lines or neighbours
# only through these. Comparisons are strict; a value on a line belongs to neither side.

def on_line(v: float, line_value: float) -> bool:
    """True when v is exactly on the line, within ON_LINE_TOLERANCE scaled by the line."""
    return abs(v - line_value) <= ON_LINE_TOLERANCE * max(1, abs(line_value))


def above_mean(v: float, lines: dict[int, float]) -> bool:
    return v > lines[0] and not on_line(v, lines[0])


def below_mean(v: float, lines: dict[int, float]) -> bool:
    return v < lines[0] and not on_line(v, lines[0])


def beyond_above(v: float, lines: dict[int, float], k: int) -> bool:
    """True when v is strictly above the +k SD line (k = 1, 2, 3)."""
    return v > lines[k] and not on_line(v, lines[k])


def beyond_below(v: float, lines: dict[int, float], k: int) -> bool:
    """True when v is strictly below the -k SD line (k = 1, 2, 3; k is positive)."""
    return v < lines[-k] and not on_line(v, lines[-k])


def within_1(v: float, lines: dict[int, float]) -> bool:
    return (lines[-1] < v < lines[1]
            and not on_line(v, lines[-1]) and not on_line(v, lines[1]))


def outside_1(v: float, lines: dict[int, float]) -> bool:
    return beyond_above(v, lines, 1) or beyond_below(v, lines, 1)


def diff_sign(a: float, b: float) -> str:
    """Sign of the step from a (earlier) to b (later): "+", "-", or "0" when equal."""
    if abs(a - b) <= ON_LINE_TOLERANCE * max(1, abs(a), abs(b)):
        return "0"
    return "+" if b > a else "-"


def diff_signs(values: list[float]) -> list[str]:
    """The n - 1 signs between adjacent values."""
    return [diff_sign(values[i], values[i + 1]) for i in range(len(values) - 1)]


# Formatting helpers shared by every rule (SPEC.md §5.5). Numbers go through fmt();
# signs and line names use the ASCII hyphen-minus, spans in descriptions the en dash.

def line_name(k: int) -> str:
    """ "Mean" for 0, otherwise "+1 SD" ... "-3 SD"."""
    if k == 0:
        return "Mean"
    return f"{'+' if k > 0 else '-'}{abs(k)} SD"


def fmt_pairs(points: list[int], values: list[float]) -> str:
    """ "14=3.100, 15=2.900"."""
    return ", ".join(f"{p}={fmt(v)}" for p, v in zip(points, values))


def fmt_points(points: list[int]) -> str:
    return ", ".join(str(p) for p in points)


def fmt_values(values: list[float]) -> str:
    return ", ".join(fmt(v) for v in values)


def fmt_span(a: int, b: int) -> str:
    """Point span for descriptions, with an en dash: "1–12"."""
    return f"{a}–{b}"


# Rules. Each reports point numbers from series.point_numbers, never list positions.

def rule_1(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """One point beyond 3 SD. Every such point is its own observation."""
    out = []
    for p, v in zip(series.point_numbers, series.values):
        for direction, k, beyond in (("above", 3, beyond_above),
                                     ("below", -3, beyond_below)):
            if not beyond(v, lines, 3):
                continue
            name = line_name(k)
            out.append(Observation(
                field=field, chart=chart, rule_no=1, rule_name=RULE_NAMES[1],
                direction=direction, points=[p], values=[v], span=(p, p),
                line_or_window=f"{name}={fmt(lines[k])}",
                description=(f"Rule 1 — {RULE_NAMES[1]}: point {p} "
                             f"(value {fmt(v)}) is {direction} the {name} line "
                             f"({fmt(lines[k])})."),
            ))
    return out


def maximal_runs(labels: list) -> list[tuple[object, int, int]]:
    """Every maximal run of equal adjacent labels as (label, start, end), end inclusive.
    A None label never forms a run and always separates runs."""
    runs = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            if labels[start] is not None:
                runs.append((labels[start], start, i - 1))
            start = i
    return runs


def rule_2(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Nine or more points on one side of the mean. One observation per maximal run."""
    labels = ["A" if above_mean(v, lines) else "B" if below_mean(v, lines) else None
              for v in series.values]
    out = []
    for label, s, e in maximal_runs(labels):
        if e - s + 1 < RULE_2_MIN_RUN:
            continue
        direction = "above" if label == "A" else "below"
        points = series.point_numbers[s:e + 1]
        values = series.values[s:e + 1]
        out.append(Observation(
            field=field, chart=chart, rule_no=2, rule_name=RULE_NAMES[2],
            direction=direction, points=points, values=values,
            span=(points[0], points[-1]),
            line_or_window=f"mean={fmt(lines[0])}",
            description=(f"Rule 2 — {RULE_NAMES[2]}: {len(points)} consecutive "
                         f"points {direction} the mean ({fmt(lines[0])}), points "
                         f"{fmt_span(points[0], points[-1])}. "
                         f"Values: {fmt_pairs(points, values)}."),
        ))
    return out


def _trend_observation(series: Series, rule_no: int, direction: str,
                       s: int, e: int, description_head: str,
                       field: str, chart: str) -> Observation:
    """Observation for Rules 3 and 4: differences s..e cover points s..e+1."""
    points = series.point_numbers[s:e + 2]
    values = series.values[s:e + 2]
    return Observation(
        field=field, chart=chart, rule_no=rule_no, rule_name=RULE_NAMES[rule_no],
        direction=direction, points=points, values=values,
        span=(points[0], points[-1]), line_or_window="",
        description=(f"Rule {rule_no} — {description_head}: {len(points)} consecutive "
                     f"points, {fmt_span(points[0], points[-1])}. "
                     f"Values: {fmt_pairs(points, values)}."),
    )


def rule_3(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Six or more points steadily rising or falling. Works on neighbour differences;
    lines is unused. A run of m differences spans m + 1 points; a tie ends a run."""
    labels = [None if sign == "0" else sign for sign in diff_signs(series.values)]
    out = []
    for sign, s, e in maximal_runs(labels):
        if e - s + 2 < RULE_3_MIN_RUN:
            continue
        direction = "rising" if sign == "+" else "falling"
        out.append(_trend_observation(
            series, 3, direction, s, e,
            f"Six or more points steadily {direction}", field, chart))
    return out


def rule_4(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Fourteen or more points alternating up and down. Works on neighbour differences;
    lines is unused. A segment of m differences spans m + 1 points; a tie or two
    differences of the same sign in a row ends a segment."""
    signs = diff_signs(series.values)
    segments = []
    start = None
    for i, sign in enumerate(signs):
        if sign == "0":
            if start is not None:
                segments.append((start, i - 1))
            start = None
        elif start is None:
            start = i
        elif sign == signs[i - 1]:
            segments.append((start, i - 1))
            start = i
    if start is not None:
        segments.append((start, len(signs) - 1))
    out = []
    for s, e in segments:
        if e - s + 2 < RULE_4_MIN_RUN:
            continue
        out.append(_trend_observation(
            series, 4, "alternating", s, e,
            "Fourteen or more points alternating up and down", field, chart))
    return out


def window_observations(series: Series, lines: dict[int, float], k: int,
                        width: int, min_count: int, rule_no: int,
                        field: str = "", chart: str = "") -> list[Observation]:
    """Rules 5 and 6 (SPEC.md §5.4). Each side is scanned on its own: a window of
    `width` positions qualifies when at least `min_count` of them are beyond the
    ±k SD line; qualifying windows that share a position merge into one span.
    Only the flagged points inside a span are listed."""
    heads = {5: "Two of three points beyond 2 SD", 6: "Four of five points beyond 1 SD"}
    n = len(series.values)
    out = []
    for direction, line_k, beyond in (("above", k, beyond_above),
                                      ("below", -k, beyond_below)):
        flags = [beyond(v, lines, k) for v in series.values]
        spans = []
        for s in range(n - width + 1):
            if sum(flags[s:s + width]) < min_count:
                continue
            e = s + width - 1
            if spans and s <= spans[-1][1]:
                spans[-1][1] = e
            else:
                spans.append([s, e])
        name = line_name(line_k)
        for s, e in spans:
            idx = [i for i in range(s, e + 1) if flags[i]]
            points = [series.point_numbers[i] for i in idx]
            values = [series.values[i] for i in idx]
            a, b = series.point_numbers[s], series.point_numbers[e]
            out.append(Observation(
                field=field, chart=chart, rule_no=rule_no,
                rule_name=RULE_NAMES[rule_no], direction=direction,
                points=points, values=values, span=(a, b),
                line_or_window=f"{name}={fmt(lines[line_k])}; window {a}-{b}",
                description=(f"Rule {rule_no} — {heads[rule_no]}: points "
                             f"{fmt_points(points)} (values {fmt_values(values)}) "
                             f"are {direction} the {name} line "
                             f"({fmt(lines[line_k])}); window {fmt_span(a, b)}."),
            ))
    out.sort(key=lambda o: o.points[0])
    return out


def rule_5(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Two of three points beyond 2 SD, same side."""
    return window_observations(series, lines, 2, RULE_5_WINDOW, RULE_5_MIN_COUNT,
                               5, field, chart)


def rule_6(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Four of five points beyond 1 SD, same side."""
    return window_observations(series, lines, 1, RULE_6_WINDOW, RULE_6_MIN_COUNT,
                               6, field, chart)


def _one_sd_band(lines: dict[int, float]) -> str:
    """line_or_window text shared by Rules 7 and 8."""
    return f"-1 SD={fmt(lines[-1])}; +1 SD={fmt(lines[1])}"


def rule_7(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Fifteen or more points within 1 SD of the mean. One observation per maximal run."""
    labels = [True if within_1(v, lines) else None for v in series.values]
    out = []
    for _, s, e in maximal_runs(labels):
        if e - s + 1 < RULE_7_MIN_RUN:
            continue
        points = series.point_numbers[s:e + 1]
        values = series.values[s:e + 1]
        out.append(Observation(
            field=field, chart=chart, rule_no=7, rule_name=RULE_NAMES[7],
            direction="within", points=points, values=values,
            span=(points[0], points[-1]),
            line_or_window=_one_sd_band(lines),
            description=(f"Rule 7 — {RULE_NAMES[7]}: {len(points)} consecutive "
                         f"points, {fmt_span(points[0], points[-1])}, all between "
                         f"the -1 SD line ({fmt(lines[-1])}) and the +1 SD line "
                         f"({fmt(lines[1])}). Values: {fmt_pairs(points, values)}."),
        ))
    return out


def rule_8(series: Series, lines: dict[int, float],
           field: str = "", chart: str = "") -> list[Observation]:
    """Eight or more points beyond 1 SD, either side. One observation per maximal run."""
    labels = [True if outside_1(v, lines) else None for v in series.values]
    out = []
    for _, s, e in maximal_runs(labels):
        if e - s + 1 < RULE_8_MIN_RUN:
            continue
        points = series.point_numbers[s:e + 1]
        values = series.values[s:e + 1]
        n_above = sum(1 for v in values if beyond_above(v, lines, 1))
        n_below = sum(1 for v in values if beyond_below(v, lines, 1))
        out.append(Observation(
            field=field, chart=chart, rule_no=8, rule_name=RULE_NAMES[8],
            direction="either", points=points, values=values,
            span=(points[0], points[-1]),
            line_or_window=_one_sd_band(lines),
            description=(f"Rule 8 — Eight or more points beyond 1 SD on either side: "
                         f"{len(points)} consecutive points, "
                         f"{fmt_span(points[0], points[-1])}, none within 1 SD "
                         f"({n_above} above, {n_below} below). "
                         f"Values: {fmt_pairs(points, values)}."),
        ))
    return out


RULE_FUNCTIONS = (rule_1, rule_2, rule_3, rule_4, rule_5, rule_6, rule_7, rule_8)


def detect_all(series: Series, lines: dict[int, float],
               field: str = "", chart: str = "") -> list[Observation]:
    """Run all eight rules; order by (rule_no, first listed point), stable for ties."""
    out = []
    for rule in RULE_FUNCTIONS:
        out.extend(rule(series, lines, field=field, chart=chart))
    return sorted(out, key=lambda o: (o.rule_no, o.points[0]))


def pattern_points(observations: list[Observation]) -> set[int]:
    """Every point caught by any rule, each counted once."""
    return {p for o in observations for p in o.points}



# ===== SECTION 6: RENDERING =====


# ===== SECTION 7: REPORT AND CSV BUILDERS =====


# ===== SECTION 8: FLASK APP AND ROUTES =====


# ===== SECTION 9: ENTRY POINT =====

if __name__ == "__main__":
    print("IMR Control Chart Tool: the server is not built yet. Run pytest.")
