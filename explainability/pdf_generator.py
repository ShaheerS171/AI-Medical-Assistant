import io
import re
from typing import Dict, Any, Optional
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    HRFlowable,
    KeepTogether
)


class MedicalReportPDFGenerator:
    """
    Generates a structured medical PDF report compiling patient metadata,
    side-by-side visual inference analysis, metrics table, and Mistral LLM text.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        # Base modifications
        self.title_style = ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=4
        )
        self.subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=10
        )
        self.section_heading = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )
        self.body_style = ParagraphStyle(
            'ReportBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )
        self.meta_label = ParagraphStyle(
            'MetaLabel',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#475569')
        )
        self.meta_val = ParagraphStyle(
            'MetaValue',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#0F172A')
        )
        self.disclaimer_style = ParagraphStyle(
            'Disclaimer',
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#64748B'),
            alignment=1
        )

    def _pil_to_rl_image(self, pil_img: Image.Image, max_width: float, max_height: float) -> RLImage:
        """Helper to convert PIL Image into ReportLab Image while preserving aspect ratio."""
        img_buffer = io.BytesIO()
        pil_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        orig_w, orig_h = pil_img.size
        aspect = orig_h / float(orig_w)
        
        width = max_width
        height = width * aspect
        
        if height > max_height:
            height = max_height
            width = height / aspect
            
        return RLImage(img_buffer, width=width, height=height)

    def _parse_markdown_to_flowables(self, md_text: str) -> list:
        """Parses Markdown headings and paragraphs into ReportLab flowables."""
        flowables = []
        lines = md_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Match Markdown headings (e.g., ### Section, **1. Section**)
            heading_match = re.match(r'^(?:#{1,4}\s*|\*\*\d+\.\s*|\d+\.\s*\*\*)+(.*?)(?:\*\*|$)', line)
            
            if line.startswith('#') or (line.startswith('**') and ':' not in line[:20]):
                clean_heading = re.sub(r'[\*#]', '', line).strip()
                flowables.append(Paragraph(clean_heading, self.section_heading))
            else:
                # Convert bold syntax **text** to HTML <b>text</b> for ReportLab
                formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                flowables.append(Paragraph(formatted_line, self.body_style))
                
        return flowables

    def generate_pdf(
        self,
        patient_info: Dict[str, Any],
        report_text: str,
        original_img: Image.Image,
        overlay_img: Image.Image,
        metrics: Dict[str, Any],
        scan_type: str = "Brain MRI Scan"
    ) -> bytes:
        """
        Builds the entire PDF report document in memory.
        Returns bytes buffer suitable for Streamlit download button.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("AI MEDICAL ASSISTANT | RADIOLOGY REPORT", self.title_style))
        story.append(Paragraph(f"Automated Diagnostic & Decision-Support Document • Modality: {scan_type}", self.subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

        # 2. Patient Intake Metadata Box
        meta_data = [
            [
                Paragraph("Patient Name:", self.meta_label), Paragraph(str(patient_info.get('name', 'N/A')), self.meta_val),
                Paragraph("Patient ID:", self.meta_label), Paragraph(str(patient_info.get('id', 'N/A')), self.meta_val)
            ],
            [
                Paragraph("Age / Sex:", self.meta_label), Paragraph(f"{patient_info.get('age', 'N/A')} / {patient_info.get('sex', 'N/A')}", self.meta_val),
                Paragraph("Clinical History:", self.meta_label), Paragraph(str(patient_info.get('history', 'N/A')), self.meta_val)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[1.1*inch, 2.3*inch, 1.1*inch, 2.7*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 3. Side-by-Side Images (Original vs Explainability Overlay)
        rl_orig = self._pil_to_rl_image(original_img, max_width=3.2*inch, max_height=2.5*inch)
        rl_over = self._pil_to_rl_image(overlay_img, max_width=3.2*inch, max_height=2.5*inch)

        img_table_data = [
            [Paragraph("<b>Original Input Scan</b>", self.meta_label), Paragraph("<b>Vision Analysis (Grad-CAM / YOLO)</b>", self.meta_label)],
            [rl_orig, rl_over]
        ]
        img_table = Table(img_table_data, colWidths=[3.6*inch, 3.6*inch])
        img_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ]))
        story.append(img_table)
        story.append(Spacer(1, 10))

        # 4. Quantitative Metrics Summary Banner
        metric_rows = [[Paragraph(f"<b>{k}:</b> {v}", self.meta_val) for k, v in metrics.items()]]
        metrics_table = Table(metric_rows, colWidths=[7.2*inch / max(len(metrics), 1)] * len(metrics))
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#BFDBFE')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 10))

        # 5. Full 5-Section LLM Draft Text
        parsed_body = self._parse_markdown_to_flowables(report_text)
        story.extend(parsed_body)

        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        
        # 6. Medical Disclaimer Footer
        disclaimer = (
            "DISCLAIMER: This automated report is generated by an AI decision-support system for research and preliminary "
            "review only. It is not a finalized clinical diagnosis. Final interpretations must be performed by a certified radiologist."
        )
        story.append(Paragraph(disclaimer, self.disclaimer_style))

        # Build Document
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()