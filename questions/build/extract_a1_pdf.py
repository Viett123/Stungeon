"""Read the Das Leben A1 Vokabeln PDFs into rows (a one-off helper; vocab_a1.py was made from its output).

The class lists are tables with the columns:
    rn | unit number | article | noun | plural of noun | adjective | adverb | verb | english | tiếng việt | comments
pdftotext mixes the columns up, so this reads every word with its position on the page
and puts it in the column whose header is above it.

Needs PyMuPDF, which the game does not use:   pip install pymupdf
Run:  python extract_a1_pdf.py "<folder with the Vokabeln PDFs>" rows.json
"""
import glob
import json
import sys

import pymupdf

COLUMNS = ["article", "noun", "plural", "adj", "adv", "verb", "en", "vi", "comment"]
HEADERS = ("noun", "plural", "adjective", "adverb", "verb", "english", "tiếng", "comments")


def page_rows(page, file_name):
    words = page.get_text("words")                 # (x0, y0, x1, y1, text, ...)
    head = {}
    for w in words:
        if w[1] < 80 and w[4] in HEADERS:
            head.setdefault(w[4], w[0])            # the first "noun" is the noun column
    # Where each column starts. Articles are printed left of their header, so they start earlier.
    starts = [head["noun"] - 62, head["noun"] - 2, head["plural"] - 2, head["adjective"] - 2,
              head["adverb"] - 2, head["verb"] - 2, head["english"] - 2, head["tiếng"] - 2, head["comments"] - 2]
    lines = {}
    for w in words:
        if w[1] >= 80:                             # below the header row
            lines.setdefault(round(w[1]), []).append(w)
    rows = []
    for y in sorted(lines):
        cells = {name: [] for name in ["rn", "unit"] + COLUMNS}
        for w in sorted(lines[y], key=lambda w: w[0]):
            x = w[0]
            if x < 100:
                column = "rn"
            elif x < starts[0]:
                column = "unit"
            else:
                column = COLUMNS[max(i for i, start in enumerate(starts) if x >= start)]
            cells[column].append(w[4])
        row = {name: " ".join(parts) for name, parts in cells.items()}
        row["file"] = file_name
        rows.append(row)
    return rows


def main(folder, out):
    rows = []
    for path in sorted(glob.glob(folder + "/*.pdf")):
        name = path.replace("\\", "/").split("/")[-1]
        for page in pymupdf.open(path):
            rows += page_rows(page, name)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=0)
    print(len(rows), "rows")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
