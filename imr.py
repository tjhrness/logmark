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


def fmt(x: float) -> str:
    """Display a number to exactly DECIMALS places, never as "-0.000". Display only."""
    text = f"{x:.{DECIMALS}f}"
    if text.startswith("-") and float(text) == 0:
        text = text[1:]
    return text



# ===== SECTION 5: RULE ENGINE =====


# ===== SECTION 6: RENDERING =====


# ===== SECTION 7: REPORT AND CSV BUILDERS =====


# ===== SECTION 8: FLASK APP AND ROUTES =====


# ===== SECTION 9: ENTRY POINT =====

if __name__ == "__main__":
    print("IMR Control Chart Tool: the server is not built yet. Run pytest.")
