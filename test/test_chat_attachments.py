import base64
import io
import json

import pytest

from backend.file_attachments import AttachmentError, process_attachments


def upload(name, raw):
    return {"name": name, "data": base64.b64encode(raw).decode("ascii")}


def test_extracts_plain_text_without_writing_files():
    result = process_attachments([upload("notes.txt", b"Nova can read this file.")])
    assert "Nova can read this file." in result["text"]
    assert result["files"] == [{"name": "notes.txt", "type": "txt"}]
    assert result["images"] == []


def test_extracts_csv_as_rows():
    result = process_attachments([upload("grades.csv", b"Name,Score\nAda,98\nLin,95\n")])
    assert "Name | Score" in result["text"]
    assert "Ada | 98" in result["text"]


def test_extracts_html_without_script_content():
    raw = b"<h1>Report</h1><script>ignore this</script><p>Important result</p>"
    result = process_attachments([upload("report.html", raw)])
    assert "Report" in result["text"]
    assert "Important result" in result["text"]
    assert "ignore this" not in result["text"]


def test_extracts_docx_paragraphs_and_tables():
    from docx import Document
    document = Document()
    document.add_paragraph("Quarterly report")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Revenue"
    table.cell(0, 1).text = "120"
    buffer = io.BytesIO()
    document.save(buffer)
    result = process_attachments([upload("report.docx", buffer.getvalue())])
    assert "Quarterly report" in result["text"]
    assert "Revenue | 120" in result["text"]


def test_extracts_xlsx_cells():
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Results"
    sheet.append(["Subject", "Grade"])
    sheet.append(["Maths", 18])
    buffer = io.BytesIO()
    workbook.save(buffer)
    result = process_attachments([upload("grades.xlsx", buffer.getvalue())])
    assert "[Sheet: Results]" in result["text"]
    assert "Maths | 18" in result["text"]


def test_extracts_powerpoint_slide_text():
    from pptx import Presentation
    from pptx.util import Inches
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    shape = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    shape.text = "Photosynthesis"
    buffer = io.BytesIO()
    presentation.save(buffer)
    result = process_attachments([upload("lesson.pptx", buffer.getvalue())])
    assert "[Slide 1]" in result["text"]
    assert "Photosynthesis" in result["text"]


def test_converts_image_to_vision_payload():
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (20, 40, 60)).save(buffer, format="PNG")
    result = process_attachments([upload("diagram.png", buffer.getvalue())])
    assert len(result["images"]) == 1
    assert result["images"][0]["mime_type"] == "image/png"
    assert base64.b64decode(result["images"][0]["data"])


def test_rejects_unsupported_file_types():
    with pytest.raises(AttachmentError, match="not supported"):
        process_attachments([upload("archive.exe", b"not executable")])


def test_rejects_invalid_base64():
    with pytest.raises(AttachmentError, match="base64"):
        process_attachments([{"name": "notes.txt", "data": "%%%"}])


def test_rejects_more_than_five_files():
    items = [upload(f"{index}.txt", b"x") for index in range(6)]
    with pytest.raises(AttachmentError, match="up to 5 files"):
        process_attachments(items)


def test_rejects_oversized_files_before_decoding():
    item = {"name": "large.txt", "data": "A" * (11 * 1024 * 1024)}
    with pytest.raises(AttachmentError, match="8 MB"):
        process_attachments([item])


def test_rejects_combined_upload_over_ten_megabytes():
    raw = b"x" * (6 * 1024 * 1024)
    items = [upload("one.txt", raw), upload("two.txt", raw)]
    with pytest.raises(AttachmentError, match="10 MB"):
        process_attachments(items)


def test_caps_extracted_document_text():
    raw = ("x" * 65_000).encode()
    result = process_attachments([upload("large.txt", raw)])
    assert len(result["text"]) < 61_000
    assert "truncated" in result["text"]


def test_rejects_corrupt_image_data():
    with pytest.raises(AttachmentError, match="could not decode this image"):
        process_attachments([upload("broken.png", b"not an image")])
