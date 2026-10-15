
import streamlit as st


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="About - Pre-CanSkate Report Generator",
    page_icon="⛸️",
    layout="centered"
)

st.page_link(
    "app.py",
    label="Back to the report generator",
    icon="⛸️"
)

st.title("About this project")

st.link_button(
    "View the source on GitHub",
    "https://github.com/sashagrichine/CSRCG"
)


# --------------------------------------------------
# WHAT IT IS
# --------------------------------------------------

st.subheader("What it is")

st.write(
    "The Pre-CanSkate Progress Report Generator is a small web app "
    "that builds a personalized, one-page progress report (PDF) for "
    "a young figure skater."
)

st.write(
    "Coaches often write an individual report card for every skater "
    "by hand. That means repeating a lot of similar wording while "
    "still trying to make each report feel personal. This app "
    "handles the assembly: the coach ticks the skills a skater has "
    "passed, picks a few strengths and areas to improve, and gets a "
    "ready-to-edit set of comments and a printable report in a few "
    "clicks."
)


# --------------------------------------------------
# HOW TO USE IT
# --------------------------------------------------

st.subheader("How to use it")

st.markdown(
    """
1. Enter the skater's and the coach's full names (first and last).
2. Check the season, which is filled in automatically and can be
   replaced with an exact date. Choose the date signed.
3. Add the coach's signature: type it, draw it with a mouse or
   finger, or leave the line blank to sign the printed page.
4. Tick the skills the skater has passed.
5. Choose one or more strength skills and one or more improvement
   skills.
6. Click **Generate Comments**.
7. Read the comments and edit them as needed.
8. Click **Download PDF Report**.
"""
)


# --------------------------------------------------
# FEATURES
# --------------------------------------------------

st.subheader("Features")

st.markdown(
    """
- **Full names required.** Skater and coach names need a first and
  last name, and are tidied automatically (extra spaces removed,
  each word capitalized).
- **First name only in the comments.** The comment text uses only
  the skater's first name.
- **Phrase variety.** Openers, strengths, improvements and closers
  are picked at random from a bank of phrases, so reports for
  different skaters do not all read the same.
- **Editable before download.** The coach can change any of the
  generated text before the PDF is made.
- **Always one page.** Comment text shrinks from 10 pt down to 7 pt
  to fit. If it still does not fit, the app shows an error rather
  than cutting text off.
- **No contradictions.** A skill cannot be both a strength and an
  improvement; the app warns about this.
"""
)


# --------------------------------------------------
# HOW THE WORDING WORKS
# --------------------------------------------------

st.subheader("How the wording works")

st.write(
    "All report wording lives in an Excel workbook, not in the "
    "code. It has four sheets:"
)

st.markdown(
    """
- **Skills:** the checklist, in order, and the short phrase used
  for each skill inside sentences.
- **Positive Phrases:** wording used when a skill is a strength.
- **Improvement Phrases:** wording used when a skill is an area to
  improve.
- **Open and Close Phrases:** the opening and closing sentences of
  each report.
"""
)

st.write(
    "Because the wording is data, it can be changed in a "
    "spreadsheet without writing any code."
)


# --------------------------------------------------
# BUILT WITH
# --------------------------------------------------

st.subheader("Built with")

st.markdown(
    """
- Python
- Streamlit, including custom components v2 for the signature pad
- pandas and openpyxl for reading the spreadsheet
- ReportLab for creating the PDF
"""
)


# --------------------------------------------------
# PRIVACY
# --------------------------------------------------

st.subheader("Privacy")

st.write(
    "The PDF is generated in memory and handed straight to your "
    "browser for download. The app's code does not save skater "
    "names, comments or signatures to a file or a database."
)


# --------------------------------------------------
# LIMITATIONS
# --------------------------------------------------

st.subheader("Limitations")

st.markdown(
    """
- The script-style font for typed signatures looks best on macOS.
  On other systems the app falls back to italic Times.
- There is no automated test suite yet.
"""
)
