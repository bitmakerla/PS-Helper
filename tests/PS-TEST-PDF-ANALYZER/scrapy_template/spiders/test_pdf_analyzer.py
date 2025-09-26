import os

import scrapy

from ps_helper import pdf_analyzer


class PDFSpider(scrapy.Spider):
    name = "pdf_spider"

    def __init__(
        self,
        carpeta_pdfs=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pdf_analyzer = pdf_analyzer
        if carpeta_pdfs is None:
            base_path = os.path.dirname(__file__)
            self.carpeta_pdfs = os.path.join(base_path, "pdfs")
        else:
            self.carpeta_pdfs = carpeta_pdfs

    def start_requests(self):
        """Generate fake requests for local PDF files (no HTTP)."""
        pdf_files = [
            os.path.join(self.carpeta_pdfs, f)
            for f in os.listdir(self.carpeta_pdfs)
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
        carpeta_pdfs=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pdf_analyzer = pdf_analyzer
        if carpeta_pdfs is None:
            base_path = os.path.dirname(__file__)
            self.carpeta_pdfs = os.path.join(base_path, "pdfs")
        else:
            self.carpeta_pdfs = carpeta_pdfs

    def start_requests(self):
        yield scrapy.Request("data:,init", callback=self.parse_start_url)

    def parse_start_url(self, response):
        """Generate fake requests for local PDF files (no HTTP)."""
        pdf_files = [
            os.path.join(self.carpeta_pdfs, f)
            for f in os.listdir(self.carpeta_pdfs)
            if f.endswith(".pdf")
        ]

        self.logger.info(f"Found {len(pdf_files)} PDFs to process in batch.")

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
