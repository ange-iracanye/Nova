"""Secure, bounded extraction for chat attachments.

Files are processed in memory and are never written to the application filesystem.
"""
from __future__ import annotations

import base64
import binascii
import csv
import html
import io
import json
import os
import re
import zipfile
from html.parser import HTMLParser
from pathlib import PurePath
from typing import Any

MAX_FILES = 5
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 60_000
MAX_PDF_PAGES = 40
MAX_ARCHIVE_MEMBERS = 1_000
MAX_ARCHIVE_EXPANDED = 40 * 1024 * 1024
MAX_IMAGE_PIXELS = 30_000_000

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl",
    ".xml", ".html", ".htm", ".rtf", ".py", ".js", ".jsx", ".ts",
    ".tsx", ".css", ".scss", ".sql", ".yaml", ".yml", ".toml",
    ".ini", ".log", ".java", ".c", ".cpp", ".h", ".cs", ".go",
    ".rs", ".sh", ".bat", ".ipynb",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | {
    ".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".odt", ".ods",
}
IMAGE_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/png", ".bmp": "image/png",
    ".tif": "image/png", ".tiff": "image/png",
}


class AttachmentError(ValueError):
    """An attachment is unsupported, malformed, or exceeds safe limits."""


class _TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1
        elif tag.lower() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def _decode_file(item: dict[str, Any]) -> tuple[str, str, bytes]:
    if not isinstance(item, dict):
        raise AttachmentError("Each attachment must be a file object.")
    name = PurePath(str(item.get("name") or "attachment")).name[:255]
    extension = PurePath(name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise AttachmentError(f"{name}: this file type is not supported.")
    encoded = item.get("data")
    if not isinstance(encoded, str):
        raise AttachmentError(f"{name}: file data is missing.")
    if encoded.startswith("data:") and "," in encoded:
        encoded = encoded.split(",", 1)[1]
    if len(encoded) > ((MAX_FILE_BYTES + 2) // 3) * 4 + 8:
        raise AttachmentError(f"{name}: maximum file size is 8 MB.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttachmentError(f"{name}: file data is not valid base64.") from exc
    if not raw or len(raw) > MAX_FILE_BYTES:
        raise AttachmentError(f"{name}: file is empty or exceeds the 8 MB limit.")
    return name, extension, raw


def _check_office_archive(raw: bytes, name: str) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise AttachmentError(f"{name}: document contains too many internal files.")
        if sum(member.file_size for member in members) > MAX_ARCHIVE_EXPANDED:
            raise AttachmentError(f"{name}: expanded document is too large.")
        if any(member.file_size > MAX_ARCHIVE_EXPANDED for member in members):
            raise AttachmentError(f"{name}: an internal document item is too large.")
        return archive
    except zipfile.BadZipFile as exc:
        raise AttachmentError(f"{name}: document archive is invalid.") from exc


def _extract_text(name: str, extension: str, raw: bytes) -> str:
    if extension in {".txt", ".md", ".markdown", ".py", ".js", ".jsx", ".ts", ".tsx",
                     ".css", ".scss", ".sql", ".yaml", ".yml", ".toml", ".ini",
                     ".log", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs",
                     ".sh", ".bat", ".json", ".jsonl", ".xml"}:
        return raw.decode("utf-8-sig", errors="replace")
    if extension in {".html", ".htm"}:
        parser = _TextHTMLParser()
        parser.feed(raw.decode("utf-8-sig", errors="replace"))
        return html.unescape(" ".join(parser.parts))
    if extension == ".rtf":
        value = raw.decode("latin-1", errors="replace")
        value = re.sub(r"\\'[0-9a-fA-F]{2}", " ", value)
        value = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", value)
        return re.sub(r"[{}]", " ", value)
    if extension in {".csv", ".tsv"}:
        delimiter = "\t" if extension == ".tsv" else ","
        rows = csv.reader(io.StringIO(raw.decode("utf-8-sig", errors="replace")), delimiter=delimiter)
        return "\n".join(" | ".join(cell for cell in row) for row in rows)
    if extension == ".ipynb":
        try:
            notebook = json.loads(raw.decode("utf-8-sig"))
            return "\n\n".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))
        except (ValueError, AttributeError):
            raise AttachmentError(f"{name}: notebook JSON is invalid.")
    if extension == ".pdf":
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(raw), strict=False)
            if len(reader.pages) > MAX_PDF_PAGES:
                raise AttachmentError(f"{name}: PDFs are limited to {MAX_PDF_PAGES} pages.")
            parts = []
            for number, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    parts.append(f"[Page {number}]\n{page_text}")
            return "\n\n".join(parts)
        except AttachmentError:
            raise
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this PDF.") from exc
    if extension == ".docx":
        _check_office_archive(raw, name).close()
        from docx import Document
        try:
            document = Document(io.BytesIO(raw))
            parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            return "\n".join(parts)
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this Word document.") from exc
    if extension == ".xlsx":
        _check_office_archive(raw, name).close()
        from openpyxl import load_workbook
        try:
            workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            parts = []
            for sheet in workbook.worksheets:
                parts.append(f"[Sheet: {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    values = [str(value) if value is not None else "" for value in row]
                    if any(values):
                        parts.append(" | ".join(values))
            workbook.close()
            return "\n".join(parts)
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this Excel workbook.") from exc
    if extension == ".xls":
        import xlrd
        try:
            workbook = xlrd.open_workbook(file_contents=raw, on_demand=True)
            parts = []
            for sheet in workbook.sheets():
                parts.append(f"[Sheet: {sheet.name}]")
                for row in range(sheet.nrows):
                    values = [str(value) for value in sheet.row_values(row)]
                    if any(values):
                        parts.append(" | ".join(values))
            workbook.release_resources()
            return "\n".join(parts)
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this legacy Excel workbook.") from exc
    if extension == ".pptx":
        _check_office_archive(raw, name).close()
        from pptx import Presentation
        try:
            presentation = Presentation(io.BytesIO(raw))
            parts = []
            for number, slide in enumerate(presentation.slides, start=1):
                parts.append(f"[Slide {number}]")
                for shape in slide.shapes:
                    if getattr(shape, "has_text_frame", False) and shape.text.strip():
                        parts.append(shape.text.strip())
                    if getattr(shape, "has_table", False):
                        for row in shape.table.rows:
                            parts.append(" | ".join(cell.text.strip() for cell in row.cells))
            return "\n".join(parts)
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this PowerPoint presentation.") from exc
    if extension in {".odt", ".ods"}:
        archive = _check_office_archive(raw, name)
        try:
            from xml.etree import ElementTree
            xml = archive.read("content.xml")
            root = ElementTree.fromstring(xml)
            return "\n".join(text.strip() for text in root.itertext() if text.strip())
        except Exception as exc:
            raise AttachmentError(f"{name}: Nova could not read this OpenDocument file.") from exc
        finally:
            archive.close()
    return ""


def _render_scanned_pdf_pages(name: str, raw: bytes) -> list[dict[str, str]]:
    """Render up to three pages with no extractable text for vision-based reading."""
    try:
        import fitz
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw), strict=False)
        document = fitz.open(stream=raw, filetype="pdf")
        rendered = []
        for page_index, source_page in enumerate(reader.pages):
            if len(rendered) >= 3:
                break
            try:
                has_text = bool((source_page.extract_text() or "").strip())
            except Exception:
                has_text = False
            if has_text:
                continue
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
            rendered.append({
                "name": f"{name} · page {page_index + 1}",
                "mime_type": "image/png",
                "data": base64.b64encode(pixmap.tobytes("png")).decode("ascii"),
            })
        document.close()
        return rendered
    except Exception as exc:
        raise AttachmentError(f"{name}: scanned PDF page rendering is unavailable.") from exc


def _image_for_vision(name: str, extension: str, raw: bytes) -> dict[str, str]:
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise AttachmentError(f"{name}: image dimensions are too large.")
        if extension == ".gif":
            image.seek(0)
        if extension in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG", quality=90, optimize=True)
        else:
            mime = "image/png"
            output = io.BytesIO()
            image.convert("RGBA").save(output, format="PNG", optimize=True)
        data = base64.b64encode(output.getvalue()).decode("ascii")
        return {"name": name, "mime_type": mime, "data": data}
    except AttachmentError:
        raise
    except Exception as exc:
        raise AttachmentError(f"{name}: Nova could not decode this image.") from exc


def process_attachments(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Validate and extract attachments without persisting their binary data."""
    if not items:
        return {"text": "", "images": [], "files": []}
    if not isinstance(items, list) or len(items) > MAX_FILES:
        raise AttachmentError(f"You can attach up to {MAX_FILES} files per message.")
    total = 0
    text_parts: list[str] = []
    images: list[dict[str, str]] = []
    files: list[dict[str, str]] = []
    for item in items:
        name, extension, raw = _decode_file(item)
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise AttachmentError("Attachments together must not exceed 10 MB.")
        files.append({"name": name, "type": extension.lstrip(".")})
        if extension in IMAGE_EXTENSIONS:
            images.append(_image_for_vision(name, extension, raw))
        else:
            extracted = _extract_text(name, extension, raw).strip()
            if extension == ".pdf":
                images.extend(_render_scanned_pdf_pages(name, raw))
            if extracted:
                text_parts.append(f"[Document: {name}]\n{extracted}")
    combined = "\n\n".join(text_parts)
    if len(combined) > MAX_EXTRACTED_CHARS:
        combined = combined[:MAX_EXTRACTED_CHARS] + "\n[Document text truncated by Nova's safety limit.]"
    return {"text": combined, "images": images[:5], "files": files}
