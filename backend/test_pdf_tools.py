#!/usr/bin/env python3
"""
Diagnóstico de las 18 herramientas PDF.
Ejecutar desde backend con: PYTHONPATH=. python test_pdf_tools.py
"""
import os
import sys
from pathlib import Path
from io import BytesIO

# Crear PDF de prueba
def create_test_pdf(path: str, pages: int = 2) -> None:
    from reportlab.pdfgen import canvas
    p = BytesIO()
    c = canvas.Canvas(p, pagesize=(595, 842))
    for i in range(pages):
        c.drawString(100, 800, f'Test Page {i+1}')
        c.showPage()
    c.save()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(p.getvalue())

def create_test_image(path: str) -> None:
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='white')
    img.save(path)

def run_test(name: str, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return True, "OK"
    except Exception as e:
        return False, str(e)[:150]

def main():
    sys.path.insert(0, str(Path(__file__).parent))
    os.chdir(Path(__file__).parent)
    
    from app.utils.pdf_tools import (
        merge_pdf, split_pdf, rotate_pdf, compress_pdf,
        protect_pdf, unlock_pdf, order_pdf, add_page_numbers_pdf,
        crop_pdf, watermark_pdf, repair_pdf, pdf_to_pdfa,
        compare_pdf_text, edit_pdf, sign_pdf, images_to_pdf,
        redact_pdf, ocr_pdf,
    )
    
    work = Path("/tmp/pdf_tools_diag")
    work.mkdir(exist_ok=True)
    
    # PDF de prueba
    pdf1 = str(work / "a.pdf")
    pdf2 = str(work / "b.pdf")
    create_test_pdf(pdf1, 2)
    create_test_pdf(pdf2, 1)
    
    results = []
    
    # 1. merge
    ok, msg = run_test("merge", merge_pdf, [pdf1, pdf2], str(work / "merge_out.pdf"))
    results.append(("1. Unir PDF (merge)", ok, msg))
    
    # 2. split
    ok, msg = run_test("split", split_pdf, pdf1, str(work / "split_out"), 1)
    results.append(("2. Dividir PDF (split)", ok, msg))
    
    # 3. rotate
    ok, msg = run_test("rotate", rotate_pdf, pdf1, str(work / "rotate_out.pdf"), 90)
    results.append(("3. Rotar PDF (rotate)", ok, msg))
    
    # 4. compress
    ok, msg = run_test("compress", compress_pdf, pdf1, str(work / "compress_out.pdf"))
    results.append(("4. Comprimir PDF (compress)", ok, msg))
    
    # 5. protect
    ok, msg = run_test("protect", protect_pdf, pdf1, str(work / "protect_out.pdf"), "test123")
    results.append(("5. Proteger PDF (protect)", ok, msg))
    
    # 6. unlock (usar el PDF protegido)
    prot = str(work / "protect_out.pdf")
    if Path(prot).exists():
        ok, msg = run_test("unlock", unlock_pdf, prot, str(work / "unlock_out.pdf"), "test123")
    else:
        ok, msg = False, "skip (protect failed)"
    results.append(("6. Desbloquear PDF (unlock)", ok, msg))
    
    # 7. order
    ok, msg = run_test("order", order_pdf, pdf1, str(work / "order_out.pdf"), "2,1")
    results.append(("7. Ordenar PDF (order)", ok, msg))
    
    # 8. page-numbers
    ok, msg = run_test("page-numbers", add_page_numbers_pdf, pdf1, str(work / "nums_out.pdf"))
    results.append(("8. Números de página (page-numbers)", ok, msg))
    
    # 9. crop
    ok, msg = run_test("crop", crop_pdf, pdf1, str(work / "crop_out.pdf"), 10)
    results.append(("9. Recortar PDF (crop)", ok, msg))
    
    # 10. watermark
    ok, msg = run_test("watermark", watermark_pdf, pdf1, str(work / "wm_out.pdf"), "CONFIDENCIAL")
    results.append(("10. Marca de agua (watermark)", ok, msg))
    
    # 11. repair
    ok, msg = run_test("repair", repair_pdf, pdf1, str(work / "repair_out.pdf"))
    results.append(("11. Reparar PDF (repair)", ok, msg))
    
    # 12. pdfa
    ok, msg = run_test("pdfa", pdf_to_pdfa, pdf1, str(work / "pdfa_out.pdf"))
    results.append(("12. PDF/A (pdfa)", ok, msg))
    
    # 13. compare
    ok, msg = run_test("compare", compare_pdf_text, pdf1, pdf2)
    results.append(("13. Comparar PDF (compare)", ok, msg))
    
    # 14. edit
    ok, msg = run_test("edit", edit_pdf, pdf1, str(work / "edit_out.pdf"), 1, "Nota añadida", "bottom")
    results.append(("14. Editar PDF (edit)", ok, msg))
    
    # 15. sign
    ok, msg = run_test("sign", sign_pdf, pdf1, str(work / "sign_out.pdf"), "Test User", None)
    results.append(("15. Firmar PDF (sign)", ok, msg))
    
    # 16. scan (images to PDF)
    img1 = str(work / "img1.png")
    create_test_image(img1)
    ok, msg = run_test("scan", images_to_pdf, [img1], str(work / "scan_out.pdf"))
    results.append(("16. Escanear a PDF (scan)", ok, msg))
    
    # 17. redact (palabra "Test" en el PDF)
    ok, msg = run_test("redact", redact_pdf, pdf1, str(work / "redact_out.pdf"), "Test")
    results.append(("17. Censurar PDF (redact)", ok, msg))
    
    # 18. ocr
    ok, msg = run_test("ocr", ocr_pdf, pdf1, str(work / "ocr_out.pdf"))
    results.append(("18. OCR PDF (ocr)", ok, msg))
    
    # Resumen
    print("\n" + "="*70)
    print("DIAGNÓSTICO HERRAMIENTAS PDF - 18 HERRAMIENTAS")
    print("="*70)
    ok_count = sum(1 for _, ok, _ in results if ok)
    for name, ok, msg in results:
        status = "✓ OK" if ok else "✗ FALLO"
        print(f"  {status:8} | {name}")
        if not ok and msg:
            print(f"            └─ {msg}")
    print("="*70)
    print(f"RESULTADO: {ok_count}/18 herramientas OK")
    print("="*70)
    
    # Limpieza
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    
    return 0 if ok_count == 18 else 1

if __name__ == "__main__":
    sys.exit(main())
