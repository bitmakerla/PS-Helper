import os
from pathlib import Path
from ps_helper.pdf.pdf_analyzer import PDFAnalyzer

TEST_DIR = Path(__file__).parent

LOCAL_PDF_PATH = str(TEST_DIR / "test_files/scansmpl.pdf")

REMOTE_PDF_URL = (
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
)

PLUZ_PDF_PATH = str(TEST_DIR / "test_files/recibo_enel.pdf")
LUZ_DEL_SUR_PDF_PATH = str(TEST_DIR / "test_files/recibo_luzdelsur.pdf")
SEAL_PDF_PATH = str(TEST_DIR / "test_files/recibo_seal.pdf")


def test_local_pdf():
    print("\n===== Test: Local PDF =====")
    analyzer = PDFAnalyzer(ocr_enabled=True)
    result = analyzer.extract_text_from_pdf(LOCAL_PDF_PATH)
    print("Result (extract_text_from_pdf):")
    print(result)

    batch_result = analyzer.extract_text_batch([LOCAL_PDF_PATH])
    print("\nResult (extract_text_batch):")
    print(batch_result)


def test_remote_pdf():
    print("\n===== Test: Remote PDF =====")
    analyzer = PDFAnalyzer(ocr_enabled=False)
    result = analyzer.extract_text_from_pdf(REMOTE_PDF_URL)
    print("Result (extract_text_from_pdf):")
    print(result)

    batch_result = analyzer.extract_text_batch([REMOTE_PDF_URL])
    print("\nResult (extract_text_batch):")
    print(batch_result)


def test_pluz_receipt():
    """Pluz Energía bill (recibo_enel.pdf) — text-based, 2 pages."""
    analyzer = PDFAnalyzer(ocr_enabled=True, ocr_language="eng+spa")
    result = analyzer.extract_text_from_pdf(PLUZ_PDF_PATH)

    assert result["success"] is True
    assert result["error"] is None
    assert result["total_pages"] == 2
    assert result["pages_with_text"] > 0
    assert result["ocr_used"] is False  # embedded text, no OCR needed

    text = result["text"]
    assert "0177339" in text           # N° suministro
    assert "S820-0005693589" in text   # N° recibo
    assert "20269985900" in text       # RUC Pluz Energía
    assert "01065731" in text          # N° medidor
    assert "763" in text               # consumo kWh
    assert "0.6119" in text            # precio kWh
    assert "466.88" in text            # cargo por energía
    assert "604.61" in text            # total mes actual
    assert "613.50" in text            # total a pagar
    assert "BT5B" in text              # tarifa
    assert "03/MAR/2026" in text       # vencimiento
    assert "16/FEB/2026" in text       # emisión


def test_luz_del_sur_receipt():
    """Luz del Sur bill (recibo_luzdelsur.pdf) — text-based, 1 page."""
    analyzer = PDFAnalyzer(ocr_enabled=True, ocr_language="eng+spa")
    result = analyzer.extract_text_from_pdf(LUZ_DEL_SUR_PDF_PATH)

    assert result["success"] is True
    assert result["error"] is None
    assert result["total_pages"] == 1
    assert result["pages_with_text"] == 1
    assert result["ocr_used"] is False  # embedded text, no OCR needed

    text = result["text"]
    assert "1536584" in text                        # N° suministro
    assert "S106-639824" in text                    # N° recibo
    assert "20331898008" in text                    # RUC Luz del Sur
    assert "3296148" in text                        # N° medidor
    assert "MIRANDA CARDENAS CARLOS AUGUSTO" in text  # titular
    assert "09133544" in text                       # DNI
    assert "541.30" in text                         # consumo kWh
    assert "0.5979" in text                         # precio kWh
    assert "323.64" in text                         # consumo de energía
    assert "428.00" in text                         # total a pagar
    assert "BT5B" in text                           # tarifa
    assert "26-Feb-2026" in text                    # vencimiento
    assert "11-Feb-2026" in text                    # emisión


def test_seal_receipt():
    """SEAL (Sociedad Eléctrica del Sur Oeste) bill — text-based, 2 pages.

    Note: uses comma as decimal separator (e.g. 163,50 not 163.50).
    Page 2 is a near-blank payment stub so pages_with_text may be 1.
    """
    analyzer = PDFAnalyzer(ocr_enabled=True, ocr_language="eng+spa")
    result = analyzer.extract_text_from_pdf(SEAL_PDF_PATH)

    assert result["success"] is True
    assert result["error"] is None
    assert result["total_pages"] == 2
    assert result["pages_with_text"] >= 1
    assert result["ocr_used"] is False  # embedded text, no OCR needed

    text = result["text"]
    assert "109134" in text                     # N° contrato
    assert "34818910" in text                   # N° recibo
    assert "SE0134" in text                     # sistema eléctrico (RUC is in header image, not text)
    assert "MENDOZA CONDORI GENARA" in text     # titular
    assert "AREQUIPA" in text                   # provincia
    assert "177,00" in text                     # consumo kWh
    assert "0,6801" in text                     # precio kWh
    assert "120,38" in text                     # cargo energía
    assert "163,50" in text                     # total a pagar
    assert "BT5B" in text                       # tarifa
    assert "02/02/2026" in text                 # emisión
    assert "17/02/2026" in text                 # vencimiento


def test_receipts_batch():
    """All three receipts processed together via extract_text_batch."""
    analyzer = PDFAnalyzer(ocr_enabled=False)
    results = analyzer.extract_text_batch([PLUZ_PDF_PATH, LUZ_DEL_SUR_PDF_PATH, SEAL_PDF_PATH])

    assert len(results) == 3
    assert all(r["success"] for r in results)

    pluz, lds, seal = results
    assert "0177339" in pluz["text"]
    assert "1536584" in lds["text"]
    assert "109134" in seal["text"]


if __name__ == "__main__":
    if not os.path.exists(LOCAL_PDF_PATH):
        print(f"PDF not found. Invalid path {LOCAL_PDF_PATH}")
    else:
        test_local_pdf()

    test_remote_pdf()
