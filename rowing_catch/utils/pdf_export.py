"""PDF Report export utility.

Generates a multi-page PDF document containing figures using fpdf2.
"""

import io
from collections.abc import Sequence

import matplotlib.figure
from fpdf import FPDF

from rowing_catch.plot_transformer.annotations import AnnotationEntry


def generate_development_report(
    figures: list[tuple[str, matplotlib.figure.Figure, Sequence[AnnotationEntry]]],
    data_label: str,
) -> bytes:
    """Generate a PDF report containing the development analysis.

    Args:
        figures: A list of tuples containing (section_title, matplotlib Figure object, annotations).
        data_label: The label of the currently processed data for the PDF title.

    Returns:
        The generated PDF document as a byte string.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add a cover page
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 40, 'Development Analysis Report', new_x='LMARGIN', new_y='NEXT', align='C')

    pdf.set_font('Helvetica', '', 14)
    pdf.cell(0, 10, f'Data Source: {data_label}', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(
        0,
        10,
        'This report was automatically generated from the Rowing Catch Development Analytics pipeline. '
        'It contains detailed kinematics, rhythm consistency, handle-seat coordination, and trajectory analysis.',
    )

    def sanitize_text(text: str) -> str:
        if not isinstance(text, str):
            return text
        replacements = {
            '–': '-',  # en-dash
            '—': '-',  # em-dash
            '−': '-',  # minus
            '°': ' deg',
            '’': "'",
            '‘': "'",
            '”': '"',
            '“': '"',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Iterate over charts and append to PDF
    for title, fig, annotations in figures:
        pdf.add_page()

        # Add section title
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, sanitize_text(title), new_x='LMARGIN', new_y='NEXT', align='L')
        pdf.ln(5)

        # Write matplotlib Figure to memory
        buf = io.BytesIO()
        # High DPI for clear PDF rendering
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)

        # Define an appropriate width for the chart to fit on an A4 page. FPDF default units are mm.
        # A4 width is 210mm. If we leave some margin, a width of ~180mm is suitable.
        try:
            pdf.image(buf, x=15, w=180)
        except Exception as e:
            # Fallback if image saving fails (unlikely)
            pdf.set_font('Helvetica', 'I', 11)
            pdf.cell(0, 10, sanitize_text(f'Failed to render chart: {e}'), new_x='LMARGIN', new_y='NEXT', align='L')

        if annotations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, 'Annotations', new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', '', 10)

            for ann in annotations:
                # Top row: Ref and Description
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(15, 6, sanitize_text(ann.label), align='L')
                pdf.set_font('Helvetica', '', 10)
                pdf.multi_cell(0, 6, sanitize_text(ann.description))

                # Bottom row: Coach tip (if any)
                if getattr(ann, 'coach_tip', ''):
                    pdf.set_x(15 + 15)  # Indent past the ref label
                    pdf.set_font('Helvetica', 'I', 9)
                    pdf.set_text_color(100, 100, 100)  # grey
                    pdf.multi_cell(0, 5, sanitize_text(f'Coach Tip: {ann.coach_tip}'))
                    pdf.set_text_color(0, 0, 0)

                pdf.ln(3)

    # Ensure output as standard string-like bytes
    return bytes(pdf.output())
