import io
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Union

import fitz
import pytesseract
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class PDFAnalyzer:
    def __init__(
        self,
        ocr_enabled: bool = True,
        ocr_language: str = "eng+spa",
        max_workers: int = 4,
        timeout: int = 30,
    ):
        """
        Initialize PDF analyzer with configuration options.

        Args:
            ocr_enabled: Enable OCR for image-based PDFs
            ocr_language: Tesseract language codes (e.g., 'eng', 'spa', 'eng+spa')
            max_workers: Maximum threads for parallel processing
            timeout: Request timeout in seconds
        """
        self.ocr_enabled = ocr_enabled
        self.ocr_language = ocr_language
        self.max_workers = max_workers
        self.timeout = timeout
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def extract_text_from_pdf(
        self, pdf_source: Union[str, bytes], use_ocr_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from PDF with fallback to OCR for images.

        Args:
            pdf_source: PDF URL, file path, or bytes
            use_ocr_fallback: Use OCR if no text found

        Returns:
            Dict with extracted text and metadata
        """
        try:
            pdf_bytes = self._get_pdf_bytes(pdf_source)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            extracted_text = ""
            total_pages = len(doc)
            pages_with_text = 0
            ocr_used = False

            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text().strip()

                if page_text:
                    extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    pages_with_text += 1
                elif self.ocr_enabled and use_ocr_fallback:
                    ocr_text = self._extract_text_with_ocr(page)
                    if ocr_text.strip():
                        extracted_text += (
                            f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}\n"
                        )
                        ocr_used = True

            doc.close()

            return {
                "text": extracted_text.strip(),
                "total_pages": total_pages,
                "pages_with_text": pages_with_text,
                "ocr_used": ocr_used,
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return {
                "text": "",
                "total_pages": 0,
                "pages_with_text": 0,
                "ocr_used": False,
                "success": False,
                "error": str(e),
            }

    def _get_pdf_bytes(self, pdf_source: Union[str, bytes]) -> bytes:
        """Get PDF bytes from various sources."""
        if isinstance(pdf_source, bytes):
            return pdf_source
        elif isinstance(pdf_source, str):
            if pdf_source.startswith(("http://", "https://")):
                # Download from URL
                response = requests.get(pdf_source, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            else:
                # Read from file path
                with open(pdf_source, "rb") as f:
                    return f.read()
        else:
            raise ValueError("pdf_source must be URL, file path, or bytes")

    def _extract_text_with_ocr(self, page) -> str:
        """Extract text from PDF page using OCR."""
        try:
            # Get page as image
            mat = fitz.Matrix(2.0, 2.0)  # Scale for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))

            # OCR
            text = pytesseract.image_to_string(
                image, lang=self.ocr_language, config="--oem 3 --psm 6"
            )

            return text

        except Exception as e:
            logger.warning(f"OCR failed for page: {str(e)}")
            return ""

    def extract_text_batch(self, pdf_sources: list) -> list:
        """
        Extract text from multiple PDFs in parallel.
        Optimized for Scrapy's concurrent processing.
        """
        futures = []
        for pdf_source in pdf_sources:
            future = self._executor.submit(self.extract_text_from_pdf, pdf_source)
            futures.append(future)

        results = []
        for future in futures:
            try:
                result = future.result(timeout=self.timeout)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing error: {str(e)}")
                results.append({"text": "", "success": False, "error": str(e)})

        return results

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)
