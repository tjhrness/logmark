"""Chart rendering tests (SPEC.md §6.2, §10)."""

import struct

import matplotlib.pyplot as plt

import imr

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

VALUES_30 = [
    10.2, 9.8, 10.5, 10.1, 9.7, 10.3, 10.0, 9.9, 10.4, 10.6,
    9.6, 10.2, 10.1, 9.8, 10.0, 10.7, 9.5, 10.3, 10.2, 9.9,
    10.1, 10.4, 9.8, 10.0, 13.5, 10.2, 9.9, 10.3, 10.1, 9.7,
]


def _pixel_width(png: bytes) -> int:
    return struct.unpack(">I", png[16:20])[0]


def _i_chart(values, pattern=None):
    series = imr.individuals_series(values)
    stats = imr.i_chart_stats(values)
    if pattern is None:
        pattern = imr.pattern_points(imr.detect_all(series, stats.lines))
    return imr.render_chart(series, stats, pattern, "Col — Individuals (I) chart", "Value", len(values))


def _mr_chart(values, pattern=None, hide_ks=None):
    series = imr.moving_range_series(values)
    stats = imr.mr_chart_stats(values)
    if pattern is None:
        pattern = imr.pattern_points(imr.detect_all(series, stats.lines))
    if hide_ks is None:
        hide_ks = imr.lines_below_zero(stats)
    return imr.render_chart(series, stats, pattern, "Col — Moving Range (MR) chart",
                            "Moving range", len(values), hide_ks=hide_ks)


def _values(n):
    return [VALUES_30[i % 30] + 0.01 * i for i in range(n)]


def test_i_chart_is_png():
    png = _i_chart(VALUES_30)
    assert png.startswith(PNG_SIGNATURE)
    assert len(png) > 5000


def test_mr_chart_is_png():
    png = _mr_chart(VALUES_30)
    assert png.startswith(PNG_SIGNATURE)
    assert len(png) > 5000


def test_figure_width_inches():
    assert imr.figure_width_inches(10) == 10.0
    assert imr.figure_width_inches(50) == 10.0
    assert imr.figure_width_inches(100) == 20.0
    assert imr.figure_width_inches(150) == 30.0


def test_pixel_width_grows_with_n():
    assert _pixel_width(_i_chart(_values(100))) > _pixel_width(_i_chart(VALUES_30))


def test_every_point_a_pattern_point():
    png = _i_chart(VALUES_30, pattern=set(range(1, 31)))
    assert png.startswith(PNG_SIGNATURE)
    png = _mr_chart(VALUES_30, pattern=set(range(2, 31)))
    assert png.startswith(PNG_SIGNATURE)


def test_no_pattern_points():
    assert _i_chart(VALUES_30, pattern=set()).startswith(PNG_SIGNATURE)
    assert _mr_chart(VALUES_30, pattern=set()).startswith(PNG_SIGNATURE)


def test_three_points():
    values = [1.0, 3.0, 2.0]
    assert _i_chart(values).startswith(PNG_SIGNATURE)
    assert _mr_chart(values).startswith(PNG_SIGNATURE)


def test_mr_chart_hides_lines_below_zero():
    stats = imr.mr_chart_stats(VALUES_30)
    assert imr.lines_below_zero(stats) == [-3, -2]
    assert _mr_chart(VALUES_30, hide_ks=imr.lines_below_zero(stats)).startswith(PNG_SIGNATURE)


def test_mr_chart_hides_three_lines():
    assert _mr_chart(VALUES_30, hide_ks=[-3, -2, -1]).startswith(PNG_SIGNATURE)


def test_rendering_is_deterministic():
    assert _i_chart(VALUES_30) == _i_chart(VALUES_30)
    assert _mr_chart(VALUES_30) == _mr_chart(VALUES_30)


def test_no_figures_left_open():
    _i_chart(VALUES_30)
    _mr_chart(VALUES_30)
    assert plt.get_fignums() == []
