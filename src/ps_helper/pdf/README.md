# PDFAnalyzer

Part of the **PS Helper** toolkit for the Professional Services team.\
This module provides a utility for extracting text from PDFs with
support for **OCR fallback** and **batch processing**.

------------------------------------------------------------------------

## Features

-   Extract text from:
    -   Local PDF files
    -   Remote PDFs (via URL)
    -   Raw PDF bytes
-   Automatic **OCR fallback** for scanned/image-based PDFs
-   Multi-language OCR support (e.g., `eng`, `spa`, or combined like
    `eng+spa`)
-   Parallel batch extraction using `ThreadPoolExecutor`
-   Detailed metadata with every extraction:
    -   Total pages
    -   Pages containing text
    -   Whether OCR was used
    -   Error messages if any

------------------------------------------------------------------------

## Installation

```bash
pip install ps-helper
```

(or clone this repository if you’re testing locally).

---

------------------------------------------------------------------------

## Usage

### Single PDF Extraction

``` python
from ps_helper.pdf_analyzer import PDFAnalyzer

analyzer = PDFAnalyzer(ocr_enabled=True, ocr_language="eng+spa")

result = analyzer.extract_text_from_pdf("example.pdf")

print("Success:", result["success"])
print("Pages with text:", result["pages_with_text"])
print("OCR used:", result["ocr_used"])
print("Extracted text:")
print(result["text"])
```

------------------------------------------------------------------------

### Remote PDF (via URL)

``` python
result = analyzer.extract_text_from_pdf("https://example.com/sample.pdf")
print(result["text"])
```

------------------------------------------------------------------------

### Batch Processing

``` python
pdfs = [
    "example1.pdf",
    "https://example.com/sample.pdf"
]

results = analyzer.extract_text_batch(pdfs)

for idx, res in enumerate(results, start=1):
    print(f"--- PDF {idx} ---")
    print("Success:", res["success"])
    print("OCR used:", res["ocr_used"])
    print(res["text"][:500])  # print first 500 characters
```

------------------------------------------------------------------------


### Real Example as script

```python
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

```

------------------------------------------------------------------------

### Real example as spider

Need a `/pdfs` directory to extract the pdf files.

```python
import os

import scrapy

from ps_helper import pdf_analyzer


class PDFSpider(scrapy.Spider):
    name = "pdf_spider"

    def __init__(
        self,
        dir_pdfs=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pdf_analyzer = pdf_analyzer
        if dir_pdfs is None:
            base_path = os.path.dirname(__file__)
            self.dir_pdfs = os.path.join(base_path, "pdfs")
        else:
            self.dir_pdfs = dir_pdfs

    def start_requests(self):
        """Generate fake requests for local PDF files (no HTTP)."""
        pdf_files = [
            os.path.join(self.dir_pdfs, f)
            for f in os.listdir(self.dir_pdfs)
            if f.endswith(".pdf")
        ]

        self.logger.info(f"Found {len(pdf_files)} PDFs to process.")

        for pdf_path in pdf_files:
            url = f"file://{os.path.abspath(pdf_path)}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_pdf,
                dont_filter=True,
            )

    def parse_pdf(self, response):
        try:
            # Extract text from PDF bytes (one by one)
            result = self.pdf_analyzer.extract_text_from_pdf(response.body)

            if result["success"]:
                yield {
                    "url": response.url,
                    "text": result["text"],
                    "total_pages": result["total_pages"],
                    "pages_with_text": result["pages_with_text"],
                    "ocr_used": result["ocr_used"],
                    "text_length": len(result["text"]),
                }
            else:
                self.logger.error(
                    f"Failed to extract text from {response.url}: {result['error']}"
                )
                yield {"url": response.url, "error": result["error"], "success": False}

        except Exception as e:
            self.logger.error(f"Error processing PDF {response.url}: {str(e)}")
            yield {"url": response.url, "error": str(e), "success": False}


class PDFSpiderBatch(scrapy.Spider):
    name = "pdf_spider_batch"

    def __init__(
        self,
        dir_pdfs=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pdf_analyzer = pdf_analyzer
        if dir_pdfs is None:
            base_path = os.path.dirname(__file__)
            self.dir_pdfs = os.path.join(base_path, "pdfs")
        else:
            self.dir_pdfs = dir_pdfs

    def start_requests(self):
        yield scrapy.Request("data:,init", callback=self.parse_start_url)

    def parse_start_url(self, response):
        """Generate fake requests for local PDF files (no HTTP)."""
        pdf_files = [
            os.path.join(self.dir_pdfs, f)
            for f in os.listdir(self.dir_pdfs)
            if f.endswith(".pdf")
        ]

        self.logger.info(f"Found {len(pdf_files)} PDFs to process in batch.")

        # Extract text from PDF bytes (batch)
        results = self.pdf_analyzer.extract_text_batch(pdf_files)

        for result in results:
            if result["success"]:
                yield {
                    "text": result["text"],
                    "total_pages": result["total_pages"],
                    "pages_with_text": result["pages_with_text"],
                    "ocr_used": result["ocr_used"],
                    "text_length": len(result["text"]),
                }
            else:
                self.logger.error(
                    f"Failed to extract text from {result['file']}: {result['error']}"
                )
                yield {
                    "file": result["file"],
                    "error": result["error"],
                    "success": False,
                }

```
------------------------------------------------------------------------

## Returned Result Format

Each extraction returns a dictionary like:

``` python
{
    "text": "... extracted text ...",
    "total_pages": 10,
    "pages_with_text": 9,
    "ocr_used": True,
    "success": True,
    "error": None
}
```
------------------------------------------------------------------------
