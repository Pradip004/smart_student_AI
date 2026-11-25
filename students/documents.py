"""Extract searchable text from supported Ask AI document uploads."""
from pathlib import PurePath
from zipfile import BadZipFile

from docx import Document
from lxml.etree import XMLSyntaxError
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError


MAX_EXTRACTED_CHARACTERS = 12000


class DocumentReadError(Exception):
    pass


def extract_document_text(uploaded_file):
    extension = PurePath(uploaded_file.name).suffix.lower()
    uploaded_file.seek(0)
    try:
        if extension == ".pdf":
            reader = PdfReader(uploaded_file)
            parts = []
            characters = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                parts.append(page_text[:MAX_EXTRACTED_CHARACTERS - characters])
                characters += len(page_text)
                if characters >= MAX_EXTRACTED_CHARACTERS:
                    break
            text = "\n".join(parts)
        elif extension == ".docx":
            document = Document(uploaded_file)
            parts = [paragraph.text for paragraph in document.paragraphs]
            for table in document.tables:
                parts.extend(
                    " | ".join(cell.text for cell in row.cells)
                    for row in table.rows
                )
            text = "\n".join(parts)
        elif extension == ".xlsx":
            workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
            try:
                parts = []
                characters = 0
                for sheet in workbook.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        row_text = " | ".join(
                            str(value) for value in row if value is not None
                        )
                        parts.append(row_text[:MAX_EXTRACTED_CHARACTERS - characters])
                        characters += len(row_text)
                        if characters >= MAX_EXTRACTED_CHARACTERS:
                            break
                    if characters >= MAX_EXTRACTED_CHARACTERS:
                        break
                text = "\n".join(parts)
            finally:
                workbook.close()
        else:
            text = uploaded_file.read().decode("utf-8-sig")
    except (BadZipFile, FileNotDecryptedError, InvalidFileException, PdfReadError,
            UnicodeDecodeError, ValueError, KeyError, XMLSyntaxError) as exc:
        raise DocumentReadError(
            "This document could not be read. Check that it is a valid, text-based file."
        ) from exc

    text = text.strip()
    if not text:
        raise DocumentReadError(
            "No searchable text was found in the document. Scanned files need OCR."
        )
    return text[:MAX_EXTRACTED_CHARACTERS]
