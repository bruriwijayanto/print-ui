import pytest

from app.utils.files import InvalidFileError, validate_content, validate_extension


def test_validate_extension_accepts_pdf_case_insensitive():
    assert validate_extension("Document.PDF") == ".pdf"


def test_validate_extension_rejects_unsupported_type():
    with pytest.raises(InvalidFileError):
        validate_extension("virus.exe")


def test_validate_extension_rejects_missing_filename():
    with pytest.raises(InvalidFileError):
        validate_extension("")


def test_validate_content_accepts_real_pdf_magic_bytes():
    validate_content(".pdf", b"%PDF-1.4\nfake but correctly-signed pdf content")


def test_validate_content_accepts_real_png_magic_bytes():
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    validate_content(".png", png_header)


def test_validate_content_rejects_mismatched_magic_bytes():
    # Extension says .pdf, content is actually a PNG.
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    with pytest.raises(InvalidFileError):
        validate_content(".pdf", png_header)


def test_validate_content_accepts_plain_text():
    validate_content(".txt", b"Hello, this is a plain text print job.\n")


def test_validate_content_rejects_binary_disguised_as_text():
    elf_header = b"\x7fELF" + b"\x00" * 32
    with pytest.raises(InvalidFileError):
        validate_content(".txt", elf_header)


def test_validate_content_rejects_empty_file():
    with pytest.raises(InvalidFileError):
        validate_content(".pdf", b"")
