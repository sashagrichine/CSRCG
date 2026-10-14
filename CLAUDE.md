# SkatingReportCards

Streamlit app that builds Pre-CanSkate progress report PDFs. Single script: `app.py`.

## Commands
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run: `streamlit run app.py`

## Architecture
- `report_card_database.xlsx` is the content source. Sheets and required columns:
  - Skills: `Skill ID`, `Skill Name`, `Report Name`
  - Positive Phrases: `Skill ID`, `Report Detail`
  - Improvement Phrases: `Skill ID`, `Report Instruction`
  - Open and Close Phrases: `Type` (Opener/Closer), `Template` (openers use `{name}`)
- `app.py` flow: load Excel -> form inputs -> "Generate Comments" assembles
  opener / strengths / improvements / closer -> editable text area -> `create_pdf` (ReportLab, US Letter).
- Skill ID is the join key between sheets. Header cells and values in the Excel
  can have trailing spaces; code strips them.

## Conventions
- Keep it a simple single-file app unless asked to split it.
- Match the existing style: sectioned with `# ----` banners, verbose spacing, no type hints.
- PDF must stay one page; comments shrink 10pt -> 7pt, then raise a ValueError.
- Wording changes belong in the Excel, not in code.
- No test suite yet. Verify changes by running the app and downloading a PDF.

## Git
- Work on branches, commit only when asked.
- Don't commit generated PDFs or personal skater data.
