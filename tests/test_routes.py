"""Route tests (SPEC.md §2.2, §6.1, §7.1 V01, §7.3, §7.4, §9.3): the upload page and
POST /analyze, driven through Flask's test client."""

import csv
import io

import pytest

import imr

A_VALUES = ["10.2", "11.5", "9.8", "10.9", "12.1", "10.4", "9.6", "11.0", "10.7", "13.9",
            "10.1", "9.9", "11.3", "10.6", "10.0", "12.4", "11.8", "9.5", "10.3", "10.8",
            "11.1", "9.7", "10.5", "12.0", "10.2"]
B_VALUES = ["5.0", "5.4", "4.8", "5.1", "5.6", "5.2", "4.9", "5.3", "5.0", "5.5",
            "5.1", "4.7", "5.2", "5.8", "5.0", "5.3", "4.9", "5.4", "5.1", "5.0",
            "5.6", "5.2", "4.8", "5.3", "5.1"]
NOTES = [f"note {i}" for i in range(1, 26)]


def make_csv(first: str, second: str) -> bytes:
    rows = [f"{first},{second},Notes"]
    for a, b, n in zip(A_VALUES, B_VALUES, NOTES):
        rows.append(f"{a},{b},{n}")
    return ("\n".join(rows) + "\n").encode("utf-8")


GOOD_CSV = make_csv("IMR_Field_Weight", "IMR_Field_Length")
OTHER_CSV = make_csv("IMR_Field_Pressure", "IMR_Field_Temperature")


def two_problem_csv() -> bytes:
    lines = GOOD_CSV.decode("utf-8").splitlines()
    lines[3] = "abc,5.1,note 3"         # bad cell: row 4, point 3
    lines[6] = "10.4,5.2,note 6,extra"  # ragged row: row 7 has 4 cells
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture
def client():
    imr.reset_state()
    app = imr.create_app()
    yield app.test_client()
    imr.reset_state()


def upload(client, data: bytes, name: str):
    return client.post("/analyze", data={"file": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")


def page(response) -> str:
    return response.get_data(as_text=True)


def test_get_index_shows_form_and_no_results(client):
    response = client.get("/")
    assert response.status_code == 200
    body = page(response)
    assert "IMR Control Chart Tool" in body
    assert "<form" in body
    assert 'action="/analyze"' in body
    assert 'method="post"' in body.lower()
    assert 'enctype="multipart/form-data"' in body
    assert 'name="file"' in body
    assert "Analyze" in body
    assert "<section>" not in body
    assert "data:image/png;base64," not in body


def test_good_upload_shows_results(client):
    response = upload(client, GOOD_CSV, "weights.csv")
    assert response.status_code == 200
    body = page(response)
    assert "<h2>IMR_Field_Weight</h2>" in body
    assert "<h2>IMR_Field_Length</h2>" in body
    assert "weights.csv" in body
    assert '<img src="data:image/png;base64,' in body
    assert "<h2>Notes</h2>" not in body
    assert 'class="rejected"' not in body
    assert "<form" in body


def test_results_header_before_sections(client):
    body = page(upload(client, GOOD_CSV, "weights.csv"))
    result = imr.LAST_RESULT
    assert result is not None
    stamp = imr.timestamp_text(result.analysed_at)
    assert stamp in body
    assert body.index("weights.csv") < body.index("<h2>IMR_Field_Weight</h2>")
    assert body.index("<form") < body.index("<h2>IMR_Field_Weight</h2>")
    assert body.index("<h2>IMR_Field_Weight</h2>") < body.index("<h2>IMR_Field_Length</h2>")


def test_get_after_upload_still_shows_results(client):
    upload(client, GOOD_CSV, "weights.csv")
    response = client.get("/")
    assert response.status_code == 200
    body = page(response)
    assert "<h2>IMR_Field_Weight</h2>" in body
    assert "<h2>IMR_Field_Length</h2>" in body
    assert "weights.csv" in body


def test_no_file_part_is_v01(client):
    response = client.post("/analyze", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    body = page(response)
    assert "No file was selected. Choose a .csv file and click Analyze." in body
    assert "<form" in body


def test_empty_filename_is_v01(client):
    response = upload(client, b"", "")
    assert response.status_code == 400
    assert "No file was selected. Choose a .csv file and click Analyze." in page(response)


def test_txt_file_is_v02(client):
    response = upload(client, GOOD_CSV, "weights.txt")
    assert response.status_code == 400
    body = page(response)
    assert "weights.txt is not a .csv file." in body
    assert "<form" in body


def test_error_box_is_above_form(client):
    body = page(upload(client, GOOD_CSV, "weights.txt"))
    assert body.index("weights.txt is not a .csv file.") < body.index("<form")


def test_two_problems_both_listed(client):
    with pytest.raises(imr.ValidationErrors) as info:
        imr.parse_csv(two_problem_csv(), "broken.csv")
    messages = [issue.message for issue in info.value.issues]
    assert len(messages) >= 2
    response = upload(client, two_problem_csv(), "broken.csv")
    assert response.status_code == 400
    body = page(response)
    for message in messages:
        assert f"<li>{imr.html.escape(message)}</li>" in body
    assert "Row 7 has 4 cells" in body
    assert "row 4" in body


def test_failed_upload_clears_previous_results(client):
    upload(client, GOOD_CSV, "weights.csv")
    response = upload(client, GOOD_CSV, "weights.txt")
    assert response.status_code == 400
    assert "<h2>IMR_Field_Weight</h2>" not in page(response)
    assert imr.LAST_RESULT is None
    assert "<h2>IMR_Field_Weight</h2>" not in page(client.get("/"))


def test_no_file_after_good_upload_clears_results(client):
    upload(client, GOOD_CSV, "weights.csv")
    response = client.post("/analyze", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert imr.LAST_RESULT is None
    assert "<h2>IMR_Field_Weight</h2>" not in page(client.get("/"))


def test_second_upload_replaces_first(client):
    upload(client, GOOD_CSV, "weights.csv")
    response = upload(client, OTHER_CSV, "process.csv")
    assert response.status_code == 200
    body = page(response)
    assert "<h2>IMR_Field_Weight</h2>" not in body
    assert "<h2>IMR_Field_Length</h2>" not in body
    assert "weights.csv" not in body
    assert "<h2>IMR_Field_Pressure</h2>" in body
    assert "<h2>IMR_Field_Temperature</h2>" in body
    assert "process.csv" in body


def test_unexpected_error_is_500_without_details(client, monkeypatch, capsys):
    upload(client, GOOD_CSV, "weights.csv")

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(imr, "analyse", boom)
    response = upload(client, OTHER_CSV, "process.csv")
    assert response.status_code == 500
    body = page(response)
    assert ("Something went wrong while analysing process.csv. "
            "The details have been printed in the console window.") in body
    assert "RuntimeError" not in body
    assert "boom" not in body
    assert "Traceback" not in body
    assert imr.LAST_RESULT is None
    captured = capsys.readouterr()
    assert "Traceback" in captured.err
    assert "boom" in captured.err


def test_filename_is_escaped(client):
    response = upload(client, GOOD_CSV, "<b>odd</b>.txt")
    assert response.status_code == 400
    body = page(response)
    assert "<b>odd</b>" not in body
    assert "&lt;b&gt;odd&lt;/b&gt;" in body


# ----- Downloads (SPEC.md §6.6, §7.3, §9.3) -----

NOTHING_YET = "Nothing has been analysed yet. Upload a file first."
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
OBSERVATIONS_HEADER = ["field", "chart", "rule_no", "rule_name", "direction", "points",
                       "values", "line_or_window", "description"]
ALL_DOWNLOADS = ["/download/report", "/download/observations",
                 "/download/png/0/I", "/download/png/0/MR"]
MY_DATA_CSV = make_csv("IMR_Field_A", "IMR_Field (B)")


def with_flat_column_csv() -> bytes:
    rows = ["IMR_Field_A,IMR_Field (B),IMR_Field_Flat"]
    for a, b in zip(A_VALUES, B_VALUES):
        rows.append(f"{a},{b},7.5")
    return ("\n".join(rows) + "\n").encode("utf-8")


def attachment_name(response) -> str:
    disposition = response.headers["Content-Disposition"]
    assert disposition.startswith("attachment")
    return disposition.split("filename=", 1)[1].strip('"')


@pytest.mark.parametrize("path", ALL_DOWNLOADS)
def test_download_before_any_upload_is_404(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert page(response) == NOTHING_YET


def test_download_report(client):
    upload(client, MY_DATA_CSV, "My Data.csv")
    response = client.get("/download/report")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert attachment_name(response) == "My_Data_IMR_report.html"
    body = page(response)
    assert body == imr.LAST_RESULT.report_html
    assert "<form" not in body


def test_download_observations(client):
    upload(client, MY_DATA_CSV, "My Data.csv")
    response = client.get("/download/observations")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert attachment_name(response) == "My_Data_observations.csv"
    text = response.get_data().decode("utf-8")
    assert text == imr.LAST_RESULT.observations_csv
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == OBSERVATIONS_HEADER


@pytest.mark.parametrize("chart", ["I", "MR"])
def test_download_png(client, chart):
    upload(client, MY_DATA_CSV, "My Data.csv")
    response = client.get(f"/download/png/0/{chart}")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert attachment_name(response) == f"My_Data_IMR_Field_A_{chart}.png"
    data = response.get_data()
    assert data.startswith(PNG_SIGNATURE)
    column = imr.LAST_RESULT.columns[0]
    stored = column.individuals if chart == "I" else column.moving_range
    assert data == stored.png


def test_download_png_second_column_name_is_sanitised(client):
    upload(client, MY_DATA_CSV, "My Data.csv")
    response = client.get("/download/png/1/I")
    assert response.status_code == 200
    assert attachment_name(response) == "My_Data_IMR_Field__B__I.png"
    assert response.get_data() == imr.LAST_RESULT.columns[1].individuals.png


@pytest.mark.parametrize("path", ["/download/png/0/X", "/download/png/9/I"])
def test_download_png_unknown_chart_or_index_is_404(client, path):
    upload(client, MY_DATA_CSV, "My Data.csv")
    response = client.get(path)
    assert response.status_code == 404
    assert page(response).strip() != ""
    assert "Traceback" not in page(response)


def test_download_png_rejected_column_is_404(client):
    upload(client, with_flat_column_csv(), "My Data.csv")
    assert imr.LAST_RESULT.columns[2].rejected_reason is not None
    for chart in ("I", "MR"):
        response = client.get(f"/download/png/2/{chart}")
        assert response.status_code == 404
        assert page(response).strip() != ""


def test_results_page_has_download_links(client):
    body = page(upload(client, with_flat_column_csv(), "My Data.csv"))
    assert body.count('href="/download/report"') == 1
    assert body.count('href="/download/observations"') == 1
    assert "Download report (HTML)" in body
    assert "Download observations (CSV)" in body
    for i in (0, 1):
        for chart in ("I", "MR"):
            assert body.count(f'href="/download/png/{i}/{chart}"') == 1
    assert "/download/png/2/" not in body
    assert body == page(client.get("/"))


def test_page_without_results_has_no_download_links(client):
    assert "/download/" not in page(client.get("/"))


def test_downloads_are_404_after_failed_upload(client):
    upload(client, MY_DATA_CSV, "My Data.csv")
    assert client.get("/download/report").status_code == 200
    upload(client, MY_DATA_CSV, "My Data.txt")
    for path in ALL_DOWNLOADS:
        response = client.get(path)
        assert response.status_code == 404
        assert page(response) == NOTHING_YET
