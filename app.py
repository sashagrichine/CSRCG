
import base64
import random
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Pre-CanSkate Progress Report",
    page_icon="⛸️",
    layout="centered"
)

EXCEL_FILE = (
    Path(__file__).resolve().parent
    / "report_card_database.xlsx"
)

st.title("Pre-CanSkate Progress Report Generator")
st.caption("Create personalized skating progress reports.")


# --------------------------------------------------
# AUTOMATIC SEASON
# --------------------------------------------------

def get_current_season():
    today = date.today()
    month = today.month

    if month in [9, 10, 11, 12]:
        season = "Fall"
    elif month in [1, 2, 3]:
        season = "Winter"
    elif month in [4, 5, 6]:
        season = "Spring"
    else:
        season = "Summer"

    return f"{season} {today.year}"


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "report_editor" not in st.session_state:
    st.session_state.report_editor = ""

if "report_ready" not in st.session_state:
    st.session_state.report_ready = False


# --------------------------------------------------
# LOAD EXCEL DATABASE
# --------------------------------------------------

try:
    skills = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Skills"
    )

    positive = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Positive Phrases"
    )

    improvements = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Improvement Phrases"
    )

    templates = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Open and Close Phrases"
    )

except (FileNotFoundError, ValueError, OSError) as error:
    st.error(f"Unable to load the Excel database: {error}")
    st.stop()


# Clean column names
for sheet in [skills, positive, improvements, templates]:
    sheet.columns = sheet.columns.astype(str).str.strip()


# Verify required columns
required_columns = [
    (
        skills,
        ["Skill ID", "Skill Name", "Report Name"],
        "Skills"
    ),
    (
        positive,
        ["Skill ID", "Report Detail"],
        "Positive Phrases"
    ),
    (
        improvements,
        ["Skill ID", "Report Instruction"],
        "Improvement Phrases"
    ),
    (
        templates,
        ["Type", "Template"],
        "Open and Close Phrases"
    )
]

for sheet, columns, sheet_name in required_columns:
    missing = [
        column
        for column in columns
        if column not in sheet.columns
    ]

    if missing:
        st.error(
            f"Missing columns in {sheet_name}: "
            + ", ".join(missing)
        )
        st.stop()


# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------

def get_skill_id(skill_name):
    matches = skills.loc[
        skills["Skill Name"] == skill_name,
        "Skill ID"
    ].dropna()

    if matches.empty:
        st.error(f"Skill not found: {skill_name}")
        st.stop()

    return str(matches.iloc[0]).strip()


def get_report_name(skill_id):
    matches = skills.loc[
        skills["Skill ID"].astype(str).str.strip() == skill_id,
        "Report Name"
    ].dropna()

    if matches.empty:
        st.error(f"Missing Report Name for {skill_id}")
        st.stop()

    return str(matches.iloc[0]).strip()


def get_templates(template_type):
    choices = templates.loc[
        templates["Type"].astype(str).str.strip()
        == template_type,
        "Template"
    ].dropna().astype(str).str.strip().tolist()

    choices = [choice for choice in choices if choice]

    if not choices:
        st.error(f"No {template_type} templates found.")
        st.stop()

    return choices


def combine_items(items):
    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return items[0] + " and " + items[1]

    return ", ".join(items[:-1]) + " and " + items[-1]


def get_positive_feedback(skill_name):
    skill_id = get_skill_id(skill_name)
    report_name = get_report_name(skill_id)

    choices = positive.loc[
        positive["Skill ID"].astype(str).str.strip()
        == skill_id,
        "Report Detail"
    ].dropna().astype(str).str.strip().tolist()

    choices = [choice for choice in choices if choice]

    if not choices:
        st.error(f"No positive feedback for {skill_name}")
        st.stop()

    detail = random.choice(choices).rstrip(".")

    return f"{report_name} {detail}"


def get_improvement_feedback(skill_name):
    skill_id = get_skill_id(skill_name)

    choices = improvements.loc[
        improvements["Skill ID"].astype(str).str.strip()
        == skill_id,
        "Report Instruction"
    ].dropna().astype(str).str.strip().tolist()

    choices = [choice for choice in choices if choice]

    if not choices:
        st.error(f"No improvement feedback for {skill_name}")
        st.stop()

    return random.choice(choices).rstrip(".") + "."


# --------------------------------------------------
# ENCOURAGING IMPROVEMENT WORDING
# --------------------------------------------------

def make_first_improvement_encouraging(sentence):
    sentence = sentence.rstrip(".")

    # These replacements produce natural -ing forms
    # after "Continue working on".
    replacements = {
        "Practise ": "practising ",
        "Work on ": "",
        "Develop ": "developing ",
        "Improve ": "improving ",
        "Build ": "building "
    }

    for prefix, replacement in replacements.items():
        if sentence.startswith(prefix):
            remainder = sentence[len(prefix):]

            if prefix == "Work on ":
                # "Work on balancing..." becomes
                # "Continue working on balancing..."
                return (
                    "Continue working on "
                    + remainder[0].lower()
                    + remainder[1:]
                    + "."
                )

            # "Improve your balance..." becomes
            # "Continue working on improving your balance..."
            return (
                "Continue working on "
                + replacement
                + remainder[0].lower()
                + remainder[1:]
                + "."
            )

    return sentence + "."


def format_date(value):
    return f"{value.strftime('%B')} {value.day}, {value.year}"


# --------------------------------------------------
# PDF FONT SETUP
# --------------------------------------------------

def register_pdf_font():
    """
    Try to use a Unicode font for skating symbols,
    curly apostrophes and accented names.
    """

    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(
                    TTFont("ReportFont", font_path)
                )
                return "ReportFont"
            except Exception:
                continue

    return "Helvetica"


def register_signature_font():
    """
    Try to use a handwriting-style font for typed signatures.
    Falls back to italic Times if none is installed.
    """

    font_paths = [
        "/System/Library/Fonts/Supplemental/Brush Script.ttf",
        "/System/Library/Fonts/Supplemental/Apple Chancery.ttf",
        "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(
                    TTFont("SignatureFont", font_path)
                )
                return "SignatureFont"
            except Exception:
                continue

    return "Times-Italic"


# --------------------------------------------------
# CREATE ONE-PAGE PDF
# --------------------------------------------------

def create_pdf(
    skater_name,
    coach_name,
    season,
    passed_skills,
    comments,
    signed_date,
    signature_text,
    signature_bytes
):
    buffer = BytesIO()

    # Letter-sized paper, suitable for Canadian printing
    page_width = 612
    page_height = 792

    pdf = canvas.Canvas(
        buffer,
        pagesize=(page_width, page_height)
    )

    font_name = register_pdf_font()

    dark = colors.HexColor("#253047")
    blue = colors.HexColor("#262EAE")
    muted = colors.HexColor("#657084")
    line_colour = colors.HexColor("#D9DFE8")

    left = 48
    right = page_width - 48
    content_width = right - left

    # Header
    pdf.setFillColor(blue)
    pdf.rect(
        0,
        page_height - 16,
        page_width,
        16,
        fill=1,
        stroke=0
    )

    pdf.setFillColor(dark)
    pdf.setFont(font_name, 18)

    pdf.drawCentredString(
        page_width / 2,
        736,
        "Pre-CanSkate Progress Report"
    )

    pdf.setFillColor(muted)
    pdf.setFont(font_name, 10)

    pdf.drawCentredString(
        page_width / 2,
        716,
        "Skating Skills Assessment"
    )

    # Skater and coach information
    pdf.setFillColor(dark)
    pdf.setFont(font_name, 10)

    pdf.drawString(left, 678, "Skater:")
    pdf.drawString(left + 48, 678, skater_name)

    pdf.drawString(340, 678, "Coach:")
    pdf.drawString(385, 678, coach_name)

    pdf.drawString(left, 655, "Season / Date:")
    pdf.drawString(left + 95, 655, season)

    # Divider
    pdf.setStrokeColor(line_colour)
    pdf.line(left, 638, right, 638)

    # Skills checklist
    pdf.setFillColor(blue)
    pdf.setFont(font_name, 12)
    pdf.drawString(left, 615, "Skills Checklist")

    pdf.setFillColor(muted)
    pdf.setFont(font_name, 9)
    pdf.drawString(
        left,
        599,
        "Checked skills have been marked as passed."
    )

    skill_names = skills["Skill Name"].dropna().tolist()

    y = 572

    for skill_name in skill_names:
        checked = skill_name in passed_skills

        # Checkbox outline
        pdf.setStrokeColor(blue if checked else muted)
        pdf.setLineWidth(1)
        pdf.rect(
            left + 2,
            y - 2,
            12,
            12,
            fill=0,
            stroke=1
        )

        # Draw tick mark
        if checked:
            pdf.setStrokeColor(blue)
            pdf.setLineWidth(2)

            path = pdf.beginPath()
            path.moveTo(left + 4, y + 3)
            path.lineTo(left + 7, y)
            path.lineTo(left + 12, y + 8)

            pdf.drawPath(path, stroke=1)

        pdf.setFillColor(dark)
        pdf.setFont(font_name, 10)
        pdf.drawString(left + 25, y, skill_name)

        y -= 27

    # Divider under checklist
    pdf.setStrokeColor(line_colour)
    pdf.line(left, y + 8, right, y + 8)

    # Comments heading
    comments_heading_y = y - 15

    pdf.setFillColor(blue)
    pdf.setFont(font_name, 12)
    pdf.drawString(
        left,
        comments_heading_y,
        "Coach's Comments"
    )

    # Preserve paragraph breaks from the editor
    # and escape text for ReportLab's Paragraph.
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", comments.strip())
        if paragraph.strip()
    ]

    # Available space ends above the signature section.
    comments_top = comments_heading_y - 18
    comments_bottom = 112
    available_height = comments_top - comments_bottom

    def build_paragraphs(font_size):
        style = ParagraphStyle(
            "Comments",
            fontName=font_name,
            fontSize=font_size,
            leading=font_size * 1.35,
            textColor=dark,
            spaceAfter=0
        )

        built = []
        total_height = 0

        for paragraph_text in paragraphs:
            safe_text = escape(paragraph_text).replace(
                "\n", "<br/>"
            )

            paragraph = Paragraph(safe_text, style)
            _, height = paragraph.wrap(
                content_width,
                available_height
            )

            built.append((paragraph, height))
            total_height += height + 9

        return built, total_height

    # Fit comments by reducing font size if necessary
    paragraph_items = []
    total_height = 0

    for font_size in [10, 9, 8, 7]:
        paragraph_items, total_height = build_paragraphs(
            font_size
        )

        if total_height <= available_height:
            break

    # Never silently cut off a long report.
    if total_height > available_height:
        raise ValueError(
            "The comments are too long for one page. "
            "Please shorten them before downloading."
        )

    current_y = comments_top

    for paragraph, height in paragraph_items:
        paragraph.drawOn(
            pdf,
            left,
            current_y - height
        )

        current_y -= height + 9

    # Signature section
    pdf.setStrokeColor(line_colour)
    pdf.line(left, 99, right, 99)

    pdf.setStrokeColor(muted)
    pdf.line(left, 55, 255, 55)
    pdf.line(335, 55, right, 55)

    # Date signed, written just above the date line
    pdf.setFillColor(dark)
    pdf.setFont(font_name, 11)
    pdf.drawString(
        left + 4,
        61,
        format_date(signed_date)
    )

    # Typed signature, written in a script font on the signature line
    if signature_text:
        script_font = register_signature_font()

        signature_size = 26

        while (
            signature_size > 10
            and pdfmetrics.stringWidth(
                signature_text, script_font, signature_size
            ) > right - 335 - 8
        ):
            signature_size -= 1

        pdf.setFillColor(blue)
        pdf.setFont(script_font, signature_size)
        pdf.drawString(339, 61, signature_text)

    # Drawn signature image, sitting on the signature line
    elif signature_bytes:
        try:
            pdf.drawImage(
                ImageReader(BytesIO(signature_bytes)),
                335,
                58,
                width=right - 335,
                height=36,
                preserveAspectRatio=True,
                anchor="sw",
                mask="auto"
            )
        except Exception:
            raise ValueError(
                "The drawn signature could not be read. "
                "Please clear it and draw it again."
            )

    pdf.setFillColor(muted)
    pdf.setFont(font_name, 9)

    pdf.drawString(
        left,
        41,
        "Date"
    )

    pdf.drawString(
        335,
        41,
        "Coach's Signature"
    )

    pdf.setTitle("Pre-CanSkate Progress Report")
    pdf.setAuthor(coach_name)

    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()


# --------------------------------------------------
# SKATER AND COACH INFORMATION
# --------------------------------------------------

st.subheader("Skater Information")

def format_name(raw_name):
    """
    Tidy a typed name: single spaces, and a capital letter at the
    start of every word and after hyphens or apostrophes.
    Other letters are left as typed, so "McDonald" stays "McDonald".
    """

    return re.sub(
        r"(^|[\s\-'’])([^\W\d_])",
        lambda match: match.group(1) + match.group(2).upper(),
        " ".join(raw_name.split())
    )


def is_full_name(name):
    # First and last name: at least two words.
    return len(name.split()) >= 2


def tidy_name_field(key):
    st.session_state[key] = format_name(st.session_state[key])


skater_name = st.text_input(
    "Skater name (first and last)",
    key="skater_name_input",
    on_change=tidy_name_field,
    args=("skater_name_input",)
)

if skater_name.strip() and not is_full_name(skater_name):
    st.warning("Please enter the skater's first and last name.")

coach_name = st.text_input(
    "Coach name (first and last)",
    key="coach_name_input",
    on_change=tidy_name_field,
    args=("coach_name_input",)
)

if coach_name.strip() and not is_full_name(coach_name):
    st.warning("Please enter the coach's first and last name.")

season = st.text_input(
    "Season / Date",
    value=get_current_season(),
    help=(
        "Automatically filled with the current season. "
        "You can change it to an exact date."
    )
)


# --------------------------------------------------
# SIGNATURE PAD (draw with mouse or finger)
# --------------------------------------------------

SIGNATURE_PAD_HTML = """
<div class="wrap">
  <canvas class="pad"></canvas>
  <div class="row">
    <span class="hint">Sign above the line</span>
    <button type="button" class="clear">Clear</button>
  </div>
</div>
"""

SIGNATURE_PAD_CSS = """
.wrap { font-family: inherit; }
.pad {
    display: block;
    width: 100%;
    height: 160px;
    border: 1px solid #d9dfe8;
    border-radius: 8px;
    background: #ffffff;
    touch-action: none;
    cursor: crosshair;
}
.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 13px;
    color: #657084;
}
.clear {
    border: 1px solid #d9dfe8;
    border-radius: 6px;
    background: #ffffff;
    padding: 4px 12px;
    cursor: pointer;
}
"""

SIGNATURE_PAD_JS = """
export default function(component) {
    const { parentElement, setStateValue } = component;
    const canvas = parentElement.querySelector('.pad');

    // Streamlit may call this again on reruns; set up only once.
    if (canvas.dataset.ready) {
        return;
    }
    canvas.dataset.ready = '1';

    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);

    const ctx = canvas.getContext('2d');
    ctx.scale(ratio, ratio);
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#1a2380';

    let drawing = false;
    let hasInk = false;

    const point = (event) => {
        const box = canvas.getBoundingClientRect();
        return [event.clientX - box.left, event.clientY - box.top];
    };

    canvas.addEventListener('pointerdown', (event) => {
        drawing = true;
        canvas.setPointerCapture(event.pointerId);
        const [x, y] = point(event);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + 0.01, y + 0.01);
        ctx.stroke();
        hasInk = true;
    });

    canvas.addEventListener('pointermove', (event) => {
        if (!drawing) {
            return;
        }
        const [x, y] = point(event);
        ctx.lineTo(x, y);
        ctx.stroke();
    });

    const finish = () => {
        if (!drawing) {
            return;
        }
        drawing = false;
        setStateValue('image', hasInk ? canvas.toDataURL('image/png') : '');
    };

    canvas.addEventListener('pointerup', finish);
    canvas.addEventListener('pointercancel', finish);

    parentElement.querySelector('.clear').addEventListener('click', () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hasInk = false;
        setStateValue('image', '');
    });
}
"""

signature_pad = st.components.v2.component(
    "signature_pad",
    html=SIGNATURE_PAD_HTML,
    css=SIGNATURE_PAD_CSS,
    js=SIGNATURE_PAD_JS
)


# --------------------------------------------------
# DATE AND SIGNATURE
# --------------------------------------------------

st.subheader("Date and Signature")

signed_date = st.date_input(
    "Date signed",
    value=date.today()
)

signature_method = st.radio(
    "Coach signature",
    ["Type it", "Draw it", "Sign by hand"],
    horizontal=True,
    help=(
        "Type your name in a handwriting font, draw it with your "
        "mouse or finger, or leave the line blank to sign the "
        "printed page."
    )
)

signature_text = ""
signature_bytes = None

if signature_method == "Type it":
    signature_text = st.text_input(
        "Type your signature",
        placeholder="e.g. Jane Smith"
    ).strip()

elif signature_method == "Draw it":
    st.caption("Draw your signature in the box below.")

    pad = signature_pad(
        key="signature_pad",
        on_image_change=lambda: None
    )

    if pad.image:
        signature_bytes = base64.b64decode(
            pad.image.split(",", 1)[1]
        )


# --------------------------------------------------
# SKILLS CHECKLIST
# --------------------------------------------------

st.divider()

st.subheader("Pre-CanSkate Skills Checklist")

st.write(
    "Check the skills the skater has passed. "
    "These are separate from strengths and improvements."
)

skill_names = skills["Skill Name"].dropna().tolist()

passed_skills = []

for skill_name in skill_names:
    skill_id = get_skill_id(skill_name)

    if st.checkbox(
        skill_name,
        key=f"passed_{skill_id}"
    ):
        passed_skills.append(skill_name)

st.caption(
    f"{len(passed_skills)} of {len(skill_names)} skills passed"
)


# --------------------------------------------------
# STRENGTHS AND IMPROVEMENTS
# --------------------------------------------------

st.divider()

st.subheader("Coach's Feedback")

strength_skill_names = st.multiselect(
    "Strength skills",
    skill_names
)

improvement_skill_names = st.multiselect(
    "Improvement skills",
    skill_names
)

# Warn about duplicates even before Generate is clicked
duplicate_skills = (
    set(strength_skill_names)
    & set(improvement_skill_names)
)

if duplicate_skills:
    st.warning(
        "A skill cannot be both a strength and an improvement: "
        + ", ".join(sorted(duplicate_skills))
    )


# --------------------------------------------------
# GENERATE COMMENTS
# --------------------------------------------------

if st.button(
    "Generate Comments",
    type="primary"
):

    if not is_full_name(skater_name):
        st.error("Please enter the skater's first and last name.")
        st.stop()

    if not is_full_name(coach_name):
        st.error("Please enter the coach's first and last name.")
        st.stop()

    if not season.strip():
        st.error("Please enter a season or date.")
        st.stop()

    if not strength_skill_names:
        st.error("Please select at least one strength.")
        st.stop()

    if not improvement_skill_names:
        st.error("Please select at least one improvement.")
        st.stop()

    if duplicate_skills:
        st.error(
            "Please remove duplicate skills before generating."
        )
        st.stop()

    # Generate strengths
    strength_feedback = [
        get_positive_feedback(skill_name)
        for skill_name in strength_skill_names
    ]

    positive_sentence = (
        "You did a great job "
        + combine_items(strength_feedback)
        + "."
    )

    # Generate improvements
    improvement_feedback = [
        get_improvement_feedback(skill_name)
        for skill_name in improvement_skill_names
    ]

    improvement_feedback[0] = (
        make_first_improvement_encouraging(
            improvement_feedback[0]
        )
    )

    improvement_text = " ".join(improvement_feedback)

    # Opening and closing phrases
    opener_template = random.choice(
        get_templates("Opener")
    )

    closer = random.choice(
        get_templates("Closer")
    )

    try:
        opener = opener_template.format(
            name=skater_name.split()[0]
        )
    except (KeyError, ValueError) as error:
        st.error(f"Invalid opening template: {error}")
        st.stop()

    # Assemble report
    report = (
        f"{opener}\n\n"
        f"{positive_sentence}\n\n"
        f"{improvement_text}\n\n"
        f"{closer}"
    )

    st.session_state.report_editor = report
    st.session_state.report_ready = True


# --------------------------------------------------
# EDIT AND DOWNLOAD PDF
# --------------------------------------------------

if st.session_state.report_ready:

    st.divider()

    st.subheader("Review and Edit Comments")

    st.write(
        "Review the generated comments and make any changes "
        "before downloading your report card."
    )

    edited_report = st.text_area(
        "Coach's comments",
        key="report_editor",
        height=260
    )

    if not edited_report.strip():
        st.info("Enter comments to prepare the PDF.")

    elif not is_full_name(skater_name) or not is_full_name(coach_name):
        st.info(
            "Enter the first and last name of the skater and "
            "coach to prepare the PDF."
        )

    elif not season.strip():
        st.info("Enter a season or date to prepare the PDF.")

    else:
        try:
            pdf_data = create_pdf(
                skater_name=skater_name.strip(),
                coach_name=coach_name.strip(),
                season=season.strip(),
                passed_skills=passed_skills,
                comments=edited_report,
                signed_date=signed_date,
                signature_text=signature_text,
                signature_bytes=signature_bytes
            )

            safe_name = re.sub(
                r"[^A-Za-z0-9_-]+",
                "_",
                skater_name.strip()
            ).strip("_") or "Skater"

            st.download_button(
                "Download PDF Report",
                data=pdf_data,
                file_name=(
                    f"{safe_name}_PreCanSkate_Report.pdf"
                ),
                mime="application/pdf",
                type="primary"
            )

            st.caption(
                "The PDF includes your current checklist, "
                "edited comments, season, date and signature."
            )

        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(
                f"Unable to create the PDF: {error}"
            )
