# IMR Control Chart Tool

## What it does

You upload a CSV file and the tool draws two control charts for every column
whose header starts with `IMR_Field`:

- an **Individuals (I) chart** – each value in time order, and
- a **Moving Range (MR) chart** – the size of the jump from each value to the next.

It then checks both charts against all eight Nelson rules and writes out, in
plain sentences, every pattern it finds. Everything runs on your own computer.
Nothing is sent over the internet and the tool works with the machine offline.

## One-time setup

You need Python 3.11. Open a Command Prompt in the tool's folder and type:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The first line makes a private Python environment in a folder called `.venv`,
the second switches it on, and the third installs the three things the tool
needs (Flask, matplotlib and pytest). You only do this once.

(On a Mac or Linux machine the second line is `source .venv/bin/activate`.)

## Running the tool

Each time, open a Command Prompt in the tool's folder and type:

```
.venv\Scripts\activate
python imr.py
```

The console shows a line like
`IMR Control Chart Tool is running at http://127.0.0.1:5000/ - keep this window open; press Ctrl+C to stop.`
and your web browser opens the upload page by itself about a second later.
If it does not, copy that address into the browser.

**Keep the console window open while you use the tool** – closing it stops the
tool. When you are finished, click in the console and press **Ctrl+C**.

The tool tries port 5000 first and moves on to 5001 … 5010 if something else
is using it. If all eleven are busy it says so; close the other program and
try again.

## Preparing your CSV file

- Save it as a `.csv` file (comma-separated, from Excel "CSV UTF-8" is fine). Maximum size 10 MB.
- **Row 1 is the header row.** Every row below it is one point.
- **Row order is time order.** The first data row is point 1, the next is point 2, and so on. The tool never sorts.
- **Columns to chart must have a header starting with `IMR_Field`** – exactly those capitals, for example `IMR_Field_Weight`. `imr_field_weight` or `Weight_IMR_Field` are not charted.
- **Every cell in an `IMR_Field` column must be a plain number** – for example `12`, `-3.5` or `0.25`. Not allowed:
  - blank cells,
  - commas as thousands separators (`1,234` – write `1234`),
  - `%` signs, currency symbols or any text.
- Every row must have the same number of cells as the header row.
- All other columns are ignored, so they can hold dates, notes or anything else.
- You need **at least 3 rows** of data; **20 or more** is recommended. With fewer than 20 the tool still works but shows a warning, because the lines are less reliable.
- Two `IMR_Field` columns may not have exactly the same header.
- A column in which every value is the same cannot be charted (there is no variation, so no lines can be drawn). Its section says so, and the other columns are charted as normal.

If anything is wrong with the file, the page lists every problem it found,
says where it is, and what to change.

## Reading the results

Each `IMR_Field` column gets its own section: the I chart, its summary table and
its observations, then the MR chart, its summary table and its observations.

**The seven lines on each chart**

| Line | Look |
|---|---|
| Mean (the centre line) | black, dotted |
| +1 SD and -1 SD | red, dotted |
| +2 SD and -2 SD | red, dotted |
| +3 SD and -3 SD | red, solid |

On the MR chart the -2 SD and -3 SD lines always fall below zero; a moving
range can never be negative, so those lines are not drawn (the summary table
still shows their values, marked "below 0, not drawn").

**The points**

- Black circle – an ordinary point.
- **Red triangle – a point caught by at least one Nelson rule.**
- Every point has its number printed just above it.

**The MR chart starts at point 2.** A moving range needs two values, so the
first one belongs to point 2 (the jump from point 1 to point 2). The two
charts are lined up so the same number sits in the same place on both.

**The observations** – under each chart, a numbered list of every pattern
found, saying which rule, which direction, which points, their values and the
line or window involved. If nothing is found it says
"No Nelson patterns detected."

**The summary table** – the number of points, the mean, the average moving
range (MR-bar), sigma, the value of each of the six SD lines, and how many
patterns were found. Numbers are shown to 3 decimal places.

## A note on the method

Sigma (the size of one "SD" step) is worked out from the **average moving
range** (MR-bar), not from an ordinary standard deviation:

- **I chart:** centre = the mean of the values; sigma = average moving range ÷ 1.128.
- **MR chart:** centre = the average moving range; sigma = 0.7557 × average moving range.

This is the standard IMR method, so the lines match Minitab or JMP to the
precision of these constants. They will **not** match a plain Excel
`STDEV.S` calculation, and that is expected.

All eight Nelson rules are run on the MR chart as well as the I chart. This is
a deliberate choice. On the MR chart, a Rule 1 point (beyond +3 SD) is a real
signal, but patterns from Rules 2 to 8 are **"worth a look" rather than "act
on it"**: moving ranges overlap (each value is used in two of them), so these
patterns appear there more often by chance.

## Downloads

After an analysis you can download:

1. **The report** – the whole results page as one HTML file (charts included) that opens in any browser, even offline. Name: `{your file}_IMR_report.html`.
2. **Each chart as a PNG picture** – the link under each chart. Name: `{your file}_{column}_I.png` or `..._MR.png`.
3. **The observations as a CSV file** – every pattern, for every column and both charts, one per row, ready to open in Excel. Name: `{your file}_observations.csv`.

## Nothing is saved

The tool writes no files and keeps no history. The results of the last
analysis stay in memory only until you upload another file or close the
console window. Download anything you want to keep.

## Running the tests

With the environment switched on (`.venv\Scripts\activate`), type:

```
pytest
```

A final line such as `324 passed` means everything is working.
