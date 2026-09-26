"""Report and CSV builder tests (SPEC.md §6.7): the observations CSV."""

import base64
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


# ----- HTML builders (SPEC.md §6.1, §6.3-6.6, §7.3) -----

HTML_VALUES = [10.0, 12.0, 11.0, 13.0, 9.0, 11.5]
NEG_VALUES = [-1.0, 1.0, -0.5, 0.5, -1.5, 1.5]


def real_chart(kind, values, observations=None):
    """A ChartResult with real statistics and a real PNG from render_chart."""
    observations = observations or []
    if kind == "I":
        series, stats = imr.individuals_series(values), imr.i_chart_stats(values)
        hide = None
    else:
        series, stats = imr.moving_range_series(values), imr.mr_chart_stats(values)
        hide = imr.lines_below_zero(stats)
    pts = imr.pattern_points(observations)
    png = imr.render_chart(series, stats, pts, f"{kind} chart", "Value", len(values), hide_ks=hide)
    return imr.ChartResult(kind=kind, point_numbers=series.point_numbers, values=series.values,
                           stats=stats, observations=observations, pattern_points=pts, png=png)


def html_column(name="IMR_Field_A", index=0, values=HTML_VALUES, warning=None,
                rejected_reason=None, i_obs=None, mr_obs=None):
    if rejected_reason is not None:
        return imr.ColumnResult(name=name, index=index, n=len(values), warning=None,
                                rejected_reason=rejected_reason,
                                individuals=None, moving_range=None)
    return imr.ColumnResult(name=name, index=index, n=len(values), warning=warning,
                            rejected_reason=None,
                            individuals=real_chart("I", values, i_obs),
                            moving_range=real_chart("MR", values, mr_obs))


ROW_LABELS_I = ["Points", "Mean", "Average moving range (MR-bar)", "Sigma (MR-bar / 1.128)",
                "+3 SD", "+2 SD", "+1 SD", "-1 SD", "-2 SD", "-3 SD", "Patterns detected"]
ROW_LABELS_MR = ROW_LABELS_I[:3] + ["Sigma (0.7557 x MR-bar)"] + ROW_LABELS_I[4:]


def table_rows(table_html):
    """Split a table into its <tr> chunks."""
    return table_html.split("<tr")[1:]


def row_for(table_html, label):
    matches = [r for r in table_rows(table_html) if f">{label}<" in r]
    assert len(matches) == 1, label
    return matches[0]


def test_warning_text():
    assert imr.warning_text(12) == (
        "Only 12 points. Control limits based on fewer than 20 points are unreliable; "
        "treat every pattern below as indicative.")


def test_summary_table_i_labels_in_order_and_values():
    ch = real_chart("I", HTML_VALUES)
    text = imr.build_summary_table_html(ch)
    assert text.lstrip().startswith("<table")
    positions = [text.index(f">{label}<") for label in ROW_LABELS_I]
    assert positions == sorted(positions)
    s = ch.stats
    assert imr.fmt(s.mean) in row_for(text, "Mean")
    assert imr.fmt(s.mr_bar) in row_for(text, "Average moving range (MR-bar)")
    assert imr.fmt(s.sigma) in row_for(text, "Sigma (MR-bar / 1.128)")
    for k, label in [(3, "+3 SD"), (2, "+2 SD"), (1, "+1 SD"),
                     (-1, "-1 SD"), (-2, "-2 SD"), (-3, "-3 SD")]:
        assert imr.fmt(s.lines[k]) in row_for(text, label)
    assert ">6<" in row_for(text, "Points")
    assert ">0<" in row_for(text, "Patterns detected")
    assert "Sigma (0.7557 x MR-bar)" not in text


def test_summary_table_mr_labels_and_below_zero_rows():
    ch = real_chart("MR", HTML_VALUES)
    assert imr.lines_below_zero(ch.stats) == [-3, -2]
    text = imr.build_summary_table_html(ch)
    positions = [text.index(f">{label}<") for label in ROW_LABELS_MR]
    assert positions == sorted(positions)
    assert "Sigma (MR-bar / 1.128)" not in text
    assert ">5<" in row_for(text, "Points")
    assert imr.fmt(ch.stats.mr_bar) in row_for(text, "Mean")
    assert text.count("(below 0, not drawn)") == 2
    assert f"{imr.fmt(ch.stats.lines[-2])} (below 0, not drawn)" in row_for(text, "-2 SD")
    assert f"{imr.fmt(ch.stats.lines[-3])} (below 0, not drawn)" in row_for(text, "-3 SD")
    assert "below 0" not in row_for(text, "-1 SD")


def test_summary_table_i_chart_negative_lines_never_marked():
    ch = real_chart("I", NEG_VALUES)
    assert ch.stats.lines[-1] < 0
    assert "below 0" not in imr.build_summary_table_html(ch)


def test_summary_table_counts_patterns():
    found = [obs("IMR_Field_A", "I", 1, [4], [13.0]), obs("IMR_Field_A", "I", 2, [1, 2], [1.0, 1.0])]
    text = imr.build_summary_table_html(real_chart("I", HTML_VALUES, found))
    assert ">2<" in row_for(text, "Patterns detected")


def test_observations_html_headings_and_descriptions():
    d1 = "Rule 1 — One point beyond 3 SD: point 4 (value 13.000) is above the +3 SD line (12.500)."
    d2 = "Rule 5 — Two of three points beyond 2 SD: points 1, 3 (values 2.500, 2.500); window 1–3."
    i_text = imr.build_observations_html(real_chart("I", HTML_VALUES,
                                                    [obs("F", "I", 1, [4], [13.0], description=d1)]))
    mr_text = imr.build_observations_html(real_chart("MR", HTML_VALUES,
                                                     [obs("F", "MR", 5, [2, 3], [1.0, 1.0], description=d2)]))
    assert "Nelson patterns detected (I chart)" in i_text
    assert "Nelson patterns detected (MR chart)" in mr_text
    assert f"<li>{d1}</li>" in i_text
    assert f"<li>{d2}</li>" in mr_text
    assert "No Nelson patterns detected." not in i_text


def test_observations_html_none():
    text = imr.build_observations_html(real_chart("I", HTML_VALUES))
    assert "Nelson patterns detected (I chart)" in text
    assert "No Nelson patterns detected." in text
    assert "<li" not in text


def test_observations_html_escapes_description():
    text = imr.build_observations_html(real_chart("I", HTML_VALUES,
                                                  [obs("F", "I", 1, [4], [13.0], description="a < b & c")]))
    assert "a &lt; b &amp; c" in text
    assert "a < b" not in text


def test_column_section_heading_images_and_order():
    text = imr.build_column_section_html(html_column())
    assert text.lstrip().startswith("<section")
    assert text.rstrip().endswith("</section>")
    assert "<h2>IMR_Field_A</h2>" in text
    assert 'alt="IMR_Field_A I chart"' in text
    assert 'alt="IMR_Field_A MR chart"' in text
    assert text.count("data:image/png;base64,") == 2
    assert "overflow-x: auto" in text
    order = [text.index("<h2>"), text.index('alt="IMR_Field_A I chart"'),
             text.index("Sigma (MR-bar / 1.128)"), text.index("Nelson patterns detected (I chart)"),
             text.index('alt="IMR_Field_A MR chart"'), text.index("Sigma (0.7557 x MR-bar)"),
             text.index("Nelson patterns detected (MR chart)")]
    assert order == sorted(order)
    assert 'class="warning"' not in text
    assert 'class="rejected"' not in text


def test_column_section_image_is_the_real_png():
    col = html_column()
    text = imr.build_column_section_html(col)
    assert "data:image/png;base64," + base64.b64encode(col.individuals.png).decode("ascii") in text
    assert "data:image/png;base64," + base64.b64encode(col.moving_range.png).decode("ascii") in text


def test_column_section_warning_before_first_image():
    col = html_column(warning=imr.warning_text(6))
    text = imr.build_column_section_html(col)
    assert 'class="warning"' in text
    assert imr.warning_text(6) in text
    assert text.index('class="warning"') < text.index("<img")


def test_column_section_rejected_shows_only_the_box():
    col = html_column(rejected_reason="Column IMR_Field_A has no numbers. Check the file.")
    text = imr.build_column_section_html(col, include_downloads=True)
    assert "<h2>IMR_Field_A</h2>" in text
    assert 'class="rejected"' in text
    assert "Column IMR_Field_A has no numbers. Check the file." in text
    assert "<img" not in text
    assert "<table" not in text
    assert "Nelson" not in text
    assert "/download/" not in text


def test_column_section_without_downloads():
    assert "/download/" not in imr.build_column_section_html(html_column(index=3))


def test_column_section_with_downloads():
    text = imr.build_column_section_html(html_column(index=3), include_downloads=True)
    assert "/download/png/3/I" in text
    assert "/download/png/3/MR" in text
    assert text.count("Download PNG") == 2
    assert text.index('alt="IMR_Field_A I chart"') < text.index("/download/png/3/I") \
        < text.index("<table")


def test_column_section_escapes_name():
    text = imr.build_column_section_html(html_column(name="IMR_Field_<A&B>"))
    assert "IMR_Field_&lt;A&amp;B&gt;" in text
    assert "<A&B>" not in text


def test_report_standalone_document():
    cols = [html_column("IMR_Field_A", 0, warning=imr.warning_text(6)),
            html_column("IMR_Field_B", 1, rejected_reason="Column IMR_Field_B has no numbers."),
            html_column("IMR_Field_C", 2)]
    text = imr.build_report_html("line3.csv", "2026-09-26 10:15", cols)
    assert text.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8">' in text
    title = text[text.index("<title>"):text.index("</title>")]
    assert "line3.csv" in title and "2026-09-26 10:15" in title
    assert "<title>IMR report — line3.csv — 2026-09-26 10:15</title>" in text
    h1 = text[text.index("<h1>"):text.index("</h1>")]
    assert "line3.csv" in h1 and "2026-09-26 10:15" in h1
    assert "<style>" in text
    assert text.count("<section") == 3
    assert text.index("IMR_Field_A") < text.index("IMR_Field_B") < text.index("IMR_Field_C")
    assert text.count("data:image/png;base64,") == 4
    assert imr.warning_text(6) in text
    assert 'class="rejected"' in text
    for forbidden in ("<form", "/download/", "<script", "<link", "http://", "https://"):
        assert forbidden not in text, forbidden
    assert text.rstrip().endswith("</html>")


def test_report_escapes_names():
    text = imr.build_report_html("a&b.csv", "2026-09-26 10:15", [html_column("IMR_Field_R&D")])
    assert "IMR_Field_R&amp;D" in text
    assert "IMR_Field_R&D" not in text
    assert "a&amp;b.csv" in text
    assert "a&b.csv" not in text
