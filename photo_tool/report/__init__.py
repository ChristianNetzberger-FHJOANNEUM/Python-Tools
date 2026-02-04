"""Report generation"""

from .text_report import generate_text_report
from .html_report import generate_html_report

__all__ = ["generate_text_report", "generate_html_report"]
