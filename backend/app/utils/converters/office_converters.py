"""
Office format converters: PDF ↔ PowerPoint, PDF ↔ Excel, Excel → PDF, PowerPoint → PDF.
Uses same BaseConverter pattern as existing converters.
"""
from typing import List
from pathlib import Path
import tempfile
import os
import subprocess
import shutil

from app.utils.base_converter import BaseConverter, ConversionError


class PDFToPptxConverter(BaseConverter):
    """Convert PDF to PowerPoint: each page becomes a slide with rendered image."""

    @property
    def source_formats(self) -> List[str]:
        return ['pdf']

    @property
    def target_formats(self) -> List[str]:
        return ['pptx']

    def convert(self, input_path: str, output_path: str) -> bool:
        try:
            self.ensure_directory(output_path)
            import fitz  # PyMuPDF
            from pptx import Presentation
            from pptx.util import Inches

            doc = fitz.open(input_path)
            if len(doc) == 0:
                doc.close()
                raise ConversionError("PDF has no pages")

            prs = Presentation()
            blank_layout = prs.slide_layouts[6]  # Blank

            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=150)
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    pix.save(tmp.name)
                    tmp_path = tmp.name
                try:
                    slide = prs.slides.add_slide(blank_layout)
                    slide.shapes.add_picture(tmp_path, Inches(0.5), Inches(0.5),
                                             width=Inches(9), height=Inches(6))
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

            doc.close()
            prs.save(output_path)
            return True
        except ImportError as e:
            raise ConversionError(
                "PDF → PowerPoint requiere PyMuPDF y python-pptx. "
                "Instala con: pip install PyMuPDF python-pptx"
            ) from e
        except Exception as e:
            raise ConversionError(f"Conversión PDF a PowerPoint falló: {str(e)}") from e


class PptxToPDFConverter(BaseConverter):
    """Convert PowerPoint to PDF using LibreOffice headless when available."""

    @property
    def source_formats(self) -> List[str]:
        return ['pptx']

    @property
    def target_formats(self) -> List[str]:
        return ['pdf']

    def convert(self, input_path: str, output_path: str) -> bool:
        self.ensure_directory(output_path)
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)
        base_name = Path(input_path).stem

        # Prefer full path so subprocess does not depend on PATH
        libreoffice_cmd = shutil.which("libreoffice") or shutil.which("soffice")
        if not libreoffice_cmd:
            raise ConversionError(
                "PowerPoint → PDF requiere LibreOffice instalado. "
                "Instala con: apt install libreoffice-writer (o libreoffice-core)."
            )

        try:
            with tempfile.TemporaryDirectory(prefix="pptx2pdf_") as tmpdir:
                result = subprocess.run(
                    [
                        libreoffice_cmd,
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", tmpdir,
                        input_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env={**os.environ, "HOME": tmpdir},
                )
                if result.returncode != 0:
                    raise ConversionError(
                        f"PowerPoint → PDF falló (código {result.returncode}). "
                        f"Detalle: {(result.stderr or result.stdout or '').strip()[:200]}"
                    )
                out_pdf = Path(tmpdir) / f"{base_name}.pdf"
                if not out_pdf.exists():
                    err = (result.stderr or result.stdout or "").strip()
                    if "could not be loaded" in err or "source file" in err:
                        raise ConversionError(
                            "PowerPoint → PDF requiere LibreOffice Impress. "
                            "Instala con: apt install libreoffice-impress-nogui"
                        )
                    raise ConversionError(
                        "PowerPoint → PDF no generó el archivo PDF. "
                        f"Salida: {err[:200]}"
                    )
                shutil.copy2(out_pdf, output_path)
                return True
        except subprocess.TimeoutExpired:
            raise ConversionError(
                "PowerPoint → PDF: la conversión tardó demasiado (timeout)."
            ) from None
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"PowerPoint → PDF falló: {e}") from e


class PDFToExcelConverter(BaseConverter):
    """Convert PDF to Excel: extract tables from PDF pages into xlsx."""

    @property
    def source_formats(self) -> List[str]:
        return ['pdf']

    @property
    def target_formats(self) -> List[str]:
        return ['xlsx']

    def convert(self, input_path: str, output_path: str) -> bool:
        try:
            self.ensure_directory(output_path)
            import pdfplumber
            from openpyxl import Workbook

            wb = Workbook()
            wb.remove(wb.active)

            with pdfplumber.open(input_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    if not tables:
                        text = page.extract_text()
                        if text:
                            ws = wb.create_sheet(title=f"Pag_{page_num}"[:31])
                            for line in text.splitlines():
                                ws.append([line])
                    else:
                        for table_idx, tbl in enumerate(tables):
                            if not tbl:
                                continue
                            title = f"Pag_{page_num}" if len(tables) == 1 else f"Pag_{page_num}_{table_idx + 1}"
                            ws = wb.create_sheet(title=title[:31])
                            for row in tbl:
                                ws.append(list(row) if row else [])

            if not wb.sheetnames:
                ws = wb.create_sheet(title="Pag_1")
                ws.append(["Sin tablas ni texto detectado en el PDF."])
            wb.save(output_path)
            return True
        except ImportError as e:
            raise ConversionError(
                "PDF → Excel requiere pdfplumber y openpyxl. "
                "Instala con: pip install pdfplumber openpyxl"
            ) from e
        except Exception as e:
            raise ConversionError(f"Conversión PDF a Excel falló: {str(e)}") from e


class ExcelToPDFConverter(BaseConverter):
    """Convert Excel to PDF: render sheet(s) as PDF table using ReportLab."""

    @property
    def source_formats(self) -> List[str]:
        return ['xlsx']

    @property
    def target_formats(self) -> List[str]:
        return ['pdf']

    def convert(self, input_path: str, output_path: str) -> bool:
        try:
            self.ensure_directory(output_path)
            from openpyxl import load_workbook
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
            from reportlab.lib import colors

            wb = load_workbook(input_path, read_only=True, data_only=True)
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            elements = []

            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = []
                for row in ws.iter_rows(values_only=True):
                    rows.append([str(c) if c is not None else '' for c in row])
                if not rows:
                    continue
                table = Table(rows)
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ]))
                if elements:
                    elements.append(PageBreak())
                elements.append(table)

            wb.close()
            if not elements:
                raise ConversionError("El archivo Excel no contiene datos")
            doc.build(elements)
            return True
        except ImportError as e:
            raise ConversionError(
                "Excel → PDF requiere openpyxl y reportlab. "
                "Instala con: pip install openpyxl reportlab"
            ) from e
        except Exception as e:
            raise ConversionError(f"Conversión Excel a PDF falló: {str(e)}") from e
