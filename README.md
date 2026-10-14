# Skating Report Cards

A Streamlit app that generates one-page Pre-CanSkate progress report PDFs.
Coaches enter skater details, tick passed skills, pick strengths and
improvement areas, edit the generated comments, and download the PDF.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Content

All phrases live in `report_card_database.xlsx` (sheets: Skills, Positive
Phrases, Improvement Phrases, Open and Close Phrases). Edit the spreadsheet to
change wording, with no code changes needed.
