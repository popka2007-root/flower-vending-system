"""Generate the Russian handoff Word document.

The source text lives in docs/project-documentation-ru.md as UTF-8 Markdown.
The generated .docx is plain Office Open XML and needs no third-party package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "docs" / "project-documentation-ru.md"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "flower-vending-system-project-documentation.docx"


@dataclass(frozen=True)
class Block:
    kind: str
    text: str


def clean_inline(text: str) -> str:
    return text.replace("`", "").replace("**", "")


def parse_markdown(markdown: str) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Block("p", clean_inline(" ".join(paragraph).strip())))
            paragraph.clear()

    def flush_code() -> None:
        if code_lines:
            blocks.append(Block("code", "\n".join(code_lines)))
            code_lines.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            marker, _, title = stripped.partition(" ")
            level = min(len(marker), 3)
            blocks.append(Block(f"h{level}", clean_inline(title.strip())))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            blocks.append(Block("bullet", clean_inline(stripped[2:].strip())))
            continue

        paragraph.append(clean_inline(stripped))

    flush_paragraph()
    if in_code:
        flush_code()
    return blocks


def xml_text(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def run_text_xml(text: str, monospace: bool = False) -> str:
    lines = text.split("\n")
    font = (
        '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" '
        'w:cs="Courier New"/><w:sz w:val="19"/></w:rPr>'
        if monospace
        else ""
    )
    chunks: list[str] = []
    for index, line in enumerate(lines):
        if index:
            chunks.append("<w:br/>")
        chunks.append(f'<w:t xml:space="preserve">{xml_text(line)}</w:t>')
    return f"<w:r>{font}{''.join(chunks)}</w:r>"


def paragraph_xml(style: str, text: str) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style != "Normal" else ""
    return f"<w:p>{style_xml}{run_text_xml(text)}</w:p>"


def block_xml(block: Block) -> str:
    if block.kind == "h1":
        return paragraph_xml("Heading1", block.text)
    if block.kind == "h2":
        return paragraph_xml("Heading2", block.text)
    if block.kind == "h3":
        return paragraph_xml("Heading3", block.text)
    if block.kind == "bullet":
        return paragraph_xml("Normal", f"• {block.text}")
    if block.kind == "code":
        return f'<w:p><w:pPr><w:pStyle w:val="CodeBlock"/></w:pPr>{run_text_xml(block.text, monospace=True)}</w:p>'
    return paragraph_xml("Normal", block.text)


def document_xml(blocks: list[Block]) -> str:
    body = "".join(block_xml(block) for block in blocks)
    section = (
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" '
        'w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'mc:Ignorable=""><w:body>'
        f"{body}{section}"
        "</w:body></w:document>"
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:lang w:val="ru-RU" w:eastAsia="ru-RU" w:bidi="ru-RU"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr><w:spacing w:after="120"/></w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/><w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="360" w:after="160"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="1F4E79"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="260" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="2F75B5"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="200" w:after="90"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="23"/><w:color w:val="404040"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="CodeBlock">
    <w:name w:val="Code Block"/><w:basedOn w:val="Normal"/>
    <w:pPr>
      <w:spacing w:before="80" w:after="120"/>
      <w:ind w:left="240"/>
      <w:pBdr><w:left w:val="single" w:sz="8" w:space="4" w:color="7F7F7F"/></w:pBdr>
      <w:shd w:fill="F3F6F8"/>
    </w:pPr>
    <w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="19"/></w:rPr>
  </w:style>
</w:styles>
"""


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def root_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def document_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>
"""


def settings_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="708"/>
  <w:characterSpacingControl w:val="doNotCompress"/>
</w:settings>
"""


def core_properties_xml() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Flower Vending System Documentation</dc:title>
  <dc:creator>Codex</dc:creator>
  <dc:description>Полная проектная документация и руководство по передаче проекта.</dc:description>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>
"""


def app_properties_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Codex OOXML generator</Application>
  <Company>Flower Vending System</Company>
  <AppVersion>1.0</AppVersion>
</Properties>
"""


def write_docx() -> None:
    markdown = SOURCE_PATH.read_text(encoding="utf-8")
    blocks = parse_markdown(markdown)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT_PATH, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", root_relationships_xml())
        archive.writestr("docProps/core.xml", core_properties_xml())
        archive.writestr("docProps/app.xml", app_properties_xml())
        archive.writestr("word/document.xml", document_xml(blocks))
        archive.writestr("word/styles.xml", styles_xml())
        archive.writestr("word/settings.xml", settings_xml())
        archive.writestr("word/_rels/document.xml.rels", document_relationships_xml())


def validate_docx() -> None:
    with ZipFile(OUTPUT_PATH) as archive:
        document = archive.read("word/document.xml").decode("utf-8")

    required = [
        "Полная проектная документация",
        "Быстрая проверка работоспособности",
        "JCM DBV-300-SD",
        "transaction journal",
    ]
    missing = [phrase for phrase in required if phrase not in document]
    if missing:
        raise RuntimeError(f"Generated DOCX is missing expected phrases: {missing}")
    if "????" in document:
        raise RuntimeError("Generated DOCX still contains corrupted question-mark runs.")


def main() -> None:
    write_docx()
    validate_docx()
    print(f"Generated {OUTPUT_PATH}")
    print(f"Size: {OUTPUT_PATH.stat().st_size} bytes")


if __name__ == "__main__":
    main()
