from .hello import hello
from .url_blocker import URLBlocker

# PDF ANALYZER
from .pdf_analyzer import PDFAnalyzer

pdf_analyzer = PDFAnalyzer()


def extract_text_from_pdf(pdf_source, **kwargs):
    return pdf_analyzer.extract_text_from_pdf(pdf_source, **kwargs)


def extract_text_batch(pdf_sources, **kwargs):
    return pdf_analyzer.extract_text_batch(pdf_sources, **kwargs)


__all__ = [
    "PDFAnalyzer",
    "pdf_analyzer",
    "extract_text_from_pdf",
    "extract_text_batch",
    "URLBlocker",
]
