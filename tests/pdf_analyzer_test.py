import os
from ps_helper.pdf_analyzer import PDFAnalyzer

LOCAL_PDF_PATH = "test_files/scansmpl.pdf"

REMOTE_PDF_URL = (
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
)


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


if __name__ == "__main__":
    if not os.path.exists(LOCAL_PDF_PATH):
        print(f"PDF not found. Invalid path {LOCAL_PDF_PATH}")
    else:
        test_local_pdf()

    test_remote_pdf()
