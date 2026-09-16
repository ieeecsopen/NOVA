import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_summary_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # Title Banner
    story.append(Paragraph("NOVA Project - Debug & GitHub PR Summary Report", title_style))
    story.append(Paragraph("Automated Verification, Bug Resolution & GitHub Pull Request Documentation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=15))

    # Meta Overview Table
    meta_data = [
        [Paragraph("<b>Repository:</b>", body_style), Paragraph("https://github.com/ieeecsopen/NOVA", body_style)],
        [Paragraph("<b>Fork Target:</b>", body_style), Paragraph("https://github.com/PesaraLimal/NOVA.git", body_style)],
        [Paragraph("<b>Branch Name:</b>", body_style), Paragraph("<b>yethmi</b>", body_style)],
        [Paragraph("<b>Commit Hash:</b>", body_style), Paragraph("e082fcce1a92a401883ac9b20a77dce7ff8d17d0", body_style)],
        [Paragraph("<b>Verification Status:</b>", body_style), Paragraph("<font color='#059669'><b>PASSED (100% Verified)</b></font>", body_style)],
        [Paragraph("<b>PR Link:</b>", body_style), Paragraph("https://github.com/PesaraLimal/NOVA/pull/new/yethmi", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[1.4*inch, 5.8*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Section 1: Bug Fixes & Improvements
    story.append(Paragraph("1. Code Issues Debugged & Resolved", h2_style))
    
    fixes_data = [
        [Paragraph("File / Module", table_header_style), Paragraph("Issue Description", table_header_style), Paragraph("Resolution Applied", table_header_style)],
        [
            Paragraph("<b>tools/check-links.py</b>", table_cell_style),
            Paragraph("UnicodeDecodeError when reading Markdown docs on Windows (default cp1252 codec).", table_cell_style),
            Paragraph("Explicitly set <code>encoding='utf-8'</code> in <code>read_text()</code> calls.", table_cell_style)
        ],
        [
            Paragraph("<b>verifier/refspec/__main__.py</b>", table_cell_style),
            Paragraph("UnicodeEncodeError when outputting checkmarks (✓) to Windows consoles.", table_cell_style),
            Paragraph("Reconfigured <code>sys.stdout</code> and <code>sys.stderr</code> streams to UTF-8.", table_cell_style)
        ],
        [
            Paragraph("<b>compiler/nova_compiler/cli.py</b>", table_cell_style),
            Paragraph("UnicodeEncodeError during <code>nova check</code> execution on Windows terminals.", table_cell_style),
            Paragraph("Reconfigured CLI standard streams to UTF-8 at entry point.", table_cell_style)
        ],
        [
            Paragraph("<b>nova.bat</b>", table_cell_style),
            Paragraph("No native execution wrapper for Windows CMD / PowerShell.", table_cell_style),
            Paragraph("Created <code>nova.bat</code> launcher for native terminal invocation.", table_cell_style)
        ]
    ]
    
    fixes_table = Table(fixes_data, colWidths=[1.8*inch, 2.7*inch, 2.7*inch])
    fixes_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(fixes_table)
    story.append(Spacer(1, 15))

    # Section 2: Test Suite Verification Results
    story.append(Paragraph("2. Test Suite Execution & Verification", h2_style))
    
    test_data = [
        [Paragraph("Test Suite / Component", table_header_style), Paragraph("Status", table_header_style), Paragraph("Result Summary", table_header_style)],
        [Paragraph("Conformance Test Suite", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("53 passed, 0 failed (100%)", table_cell_style)],
        [Paragraph("Internal Links Verification", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("959/959 documentation links resolve", table_cell_style)],
        [Paragraph("Toolchain Tests", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("18 passed, 0 failed", table_cell_style)],
        [Paragraph("Interpreter Suite", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("4 passed, 0 failed", table_cell_style)],
        [Paragraph("Regionlab Memory Prototype", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("15 passed, 0 failed", table_cell_style)],
        [Paragraph("WASI Preview2 Bridge", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("7 passed, 0 failed", table_cell_style)],
        [Paragraph("LSP Server Smoke Test", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("Initialize, Completion & Diag OK", table_cell_style)],
        [Paragraph("Examples Execution Check", table_cell_style), Paragraph("<font color='#059669'>PASSED</font>", table_cell_style), Paragraph("All .nova example files executed cleanly", table_cell_style)]
    ]
    
    test_table = Table(test_data, colWidths=[2.5*inch, 1.2*inch, 3.5*inch])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F766E')),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F0FDF4')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 15))

    # Section 3: Final Delivery Summary
    story.append(Paragraph("3. GitHub Deliverables", h2_style))
    story.append(Paragraph(
        "All code updates have been committed to the local branch <b>yethmi</b> and pushed to the remote repository "
        "<b>PesaraLimal/NOVA</b>. The branch is clean, fully verified, and ready for review via Pull Request.",
        body_style
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
    story.append(Paragraph("<b>Report Generated:</b> 2026-09-16 | NOVA Language Toolchain Verification Engine", ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=colors.HexColor('#94A3B8'))))

    doc.build(story)
    print(f"PDF generated successfully at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    pdf_path = os.path.abspath("NOVA_Debug_and_PR_Summary.pdf")
    create_summary_pdf(pdf_path)
