"""
Universal Parser Agent
Converts between multiple data formats with LLM-powered intelligent extraction

Supported Input Formats:
- JSON (.json)
- XML (.xml)
- CSV (.csv)
- Excel (.xlsx, .xls)
- Text (.txt)
- Word (.docx, .doc)
- PDF (.pdf)
- HTML (.html)
- Images (.png, .jpg, .jpeg, .gif, .bmp, .tiff, .webp) - OCR + Vision LLM

Supported Output Formats:
- JSON (structured)
- XML (structured)
- CSV (comma-delimited)
- TSV (tab-delimited)
- Plain Text (unstructured)
- Markdown
- Key-Value pairs
- Custom delimiter

LLM Integration:
- Uses Ollama models for intelligent extraction
- Vision models for image understanding
- Structured data extraction from unstructured content

This enables seamless data format conversion in workflows.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json
import csv
import logging
from io import StringIO, BytesIO
import re
import base64
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of parsing operation"""
    success: bool
    data: Any
    output_format: str
    input_format: str
    rows_parsed: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class UniversalParserAgent:
    """
    Universal parser for multiple data formats with LLM intelligence
    Converts between JSON, XML, CSV, Excel, Text, Word, PDF, HTML, Images

    Supports:
    - Traditional parsing for structured formats
    - OCR for text extraction from images
    - Vision LLM for intelligent image understanding
    - LLM-based structured extraction from unstructured content
    """

    def __init__(self, config: Dict[str, Any], ollama_service=None):
        """
        Initialize parser

        Args:
            config: Parser configuration
                - input_format: Format of input data
                - output_format: Desired output format
                - llm_model: LLM model for intelligent parsing (optional)
                - use_vision: Use vision LLM for images (default: True)
                - use_ocr: Use OCR for images (default: True)
            ollama_service: OllamaService instance for LLM operations
        """
        self.config = config
        self.ollama_service = ollama_service
        self.llm_model = config.get('llm_model', 'llama3.2-vision:latest')
        self.use_vision = config.get('use_vision', True)
        self.use_ocr = config.get('use_ocr', True)

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and convert data formats with LLM intelligence

        Config:
            input_format: 'json', 'xml', 'csv', 'excel', 'text', 'word', 'pdf', 'html', 'image', 'auto'
            output_format: 'json', 'xml', 'csv', 'tsv', 'text', 'markdown', 'key_value', 'custom'
            custom_delimiter: Custom delimiter (if output_format='custom')
            encoding: File encoding (default: utf-8)
            llm_model: LLM model for intelligent parsing (default: llama3.2-vision:latest)
            use_vision: Use vision LLM for images (default: True)
            use_ocr: Use OCR fallback for images (default: True)
            extraction_prompt: Custom prompt for LLM extraction (optional)
            options: Format-specific parsing options

        Inputs:
            data: Data to parse (string, bytes, or base64)
            file_path: Path to file (alternative to data)

        LLM Models for Parsing:
            Vision Models (for images):
            - llama3.2-vision:latest (default, best for images)
            - llava:latest
            - bakllava:latest

            Text Models (for intelligent extraction):
            - llama3.2:3b (fast, lightweight)
            - llama3.1:8b (balanced)
            - mistral:latest
            - gemma2:latest

        Output Format Options:
            - json: Structured JSON
            - xml: Structured XML
            - csv: Comma-delimited
            - tsv: Tab-delimited
            - text: Plain text
            - markdown: Markdown format
            - key_value: Key: Value pairs
            - custom: Custom delimiter

        Returns:
            success, data, output_format, rows_parsed, llm_used
        """
        try:
            input_format = self.config.get('input_format', 'auto')
            output_format = self.config.get('output_format', 'json')
            encoding = self.config.get('encoding', 'utf-8')
            options = self.config.get('options', {})

            # Get input data
            data = inputs.get('data')
            file_path = inputs.get('file_path')

            if file_path:
                # Load from file
                data, detected_format = self._load_from_file(file_path, encoding)
                if input_format == 'auto':
                    input_format = detected_format
            elif not data:
                return {
                    'success': False,
                    'error': 'No data or file_path provided'
                }

            # Auto-detect format if needed
            if input_format == 'auto':
                input_format = self._detect_format(data)

            # Parse input format
            parsed_data = await self._parse_input(data, input_format, options)

            # Convert to output format
            output_data = await self._convert_to_output(
                parsed_data, output_format, options
            )

            return {
                'success': True,
                'data': output_data,
                'input_format': input_format,
                'output_format': output_format,
                'rows_parsed': self._count_rows(parsed_data),
                'preview': self._generate_preview(output_data),
                'llm_used': self.llm_model if input_format == 'image' or self.config.get('use_llm_extraction') else None
            }

        except Exception as e:
            logger.error(f"Parser failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _load_from_file(self, file_path: str, encoding: str) -> tuple:
        """Load data from file and detect format"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect format from extension
        extension = path.suffix.lower()
        format_map = {
            '.json': 'json',
            '.xml': 'xml',
            '.csv': 'csv',
            '.tsv': 'tsv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.txt': 'text',
            '.docx': 'word',
            '.doc': 'word',
            '.pdf': 'pdf',
            '.html': 'html',
            '.htm': 'html',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.tiff': 'image',
            '.tif': 'image',
            '.webp': 'image',
            '.svg': 'image'
        }

        detected_format = format_map.get(extension, 'text')

        # Load file based on format
        if detected_format in ['excel', 'word', 'pdf', 'image']:
            # Binary formats
            with open(file_path, 'rb') as f:
                data = f.read()
        else:
            # Text formats
            with open(file_path, 'r', encoding=encoding) as f:
                data = f.read()

        return data, detected_format

    def _detect_format(self, data: Any) -> str:
        """Auto-detect data format"""
        if isinstance(data, bytes):
            # Binary data - could be Excel, Word, PDF
            return 'binary'

        if isinstance(data, str):
            data_stripped = data.strip()

            # Check JSON
            if data_stripped.startswith('{') or data_stripped.startswith('['):
                try:
                    json.loads(data_stripped)
                    return 'json'
                except:
                    pass

            # Check XML
            if data_stripped.startswith('<'):
                return 'xml'

            # Check CSV (has commas and consistent columns)
            if ',' in data_stripped:
                lines = data_stripped.split('\n')[:5]
                comma_counts = [line.count(',') for line in lines if line.strip()]
                if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
                    return 'csv'

            # Check TSV (has tabs)
            if '\t' in data_stripped:
                return 'tsv'

            # Default to text
            return 'text'

        return 'unknown'

    async def _parse_input(self, data: Any, input_format: str, options: Dict) -> Any:
        """Parse input data based on format"""
        if input_format == 'json':
            return self._parse_json(data, options)
        elif input_format == 'xml':
            return self._parse_xml(data, options)
        elif input_format == 'csv':
            return self._parse_csv(data, options)
        elif input_format == 'tsv':
            return self._parse_csv(data, {**options, 'delimiter': '\t'})
        elif input_format == 'excel':
            return self._parse_excel(data, options)
        elif input_format == 'text':
            return self._parse_text(data, options)
        elif input_format == 'word':
            return self._parse_word(data, options)
        elif input_format == 'pdf':
            return self._parse_pdf(data, options)
        elif input_format == 'html':
            return self._parse_html(data, options)
        elif input_format == 'image':
            return await self._parse_image(data, options)
        else:
            raise ValueError(f"Unsupported input format: {input_format}")

    def _parse_json(self, data: str, options: Dict) -> Any:
        """Parse JSON data"""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def _parse_xml(self, data: str, options: Dict) -> Dict:
        """Parse XML data"""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(data)
            return self._xml_to_dict(root)

        except Exception as e:
            raise ValueError(f"Invalid XML: {e}")

    def _xml_to_dict(self, element) -> Dict:
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['#text'] = element.text.strip()

        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)

            if child.tag in result:
                # Multiple elements with same tag - convert to list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result or element.text

    def _parse_csv(self, data: str, options: Dict) -> List[Dict]:
        """Parse CSV/TSV data"""
        delimiter = options.get('delimiter', ',')
        has_header = options.get('has_header', True)

        lines = data.strip().split('\n')
        reader = csv.reader(lines, delimiter=delimiter)

        rows = list(reader)

        if not rows:
            return []

        if has_header:
            headers = rows[0]
            data_rows = rows[1:]
            return [
                {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                for row in data_rows
            ]
        else:
            return [
                {f'column_{i}': value for i, value in enumerate(row)}
                for row in rows
            ]

    def _parse_excel(self, data: bytes, options: Dict) -> List[Dict]:
        """Parse Excel file"""
        try:
            import openpyxl
            from io import BytesIO

            workbook = openpyxl.load_workbook(BytesIO(data))

            # Get specified sheet or first sheet
            sheet_name = options.get('sheet_name')
            if sheet_name:
                sheet = workbook[sheet_name]
            else:
                sheet = workbook.active

            # Read data
            rows = list(sheet.values)

            if not rows:
                return []

            # First row as headers
            headers = [str(h) if h is not None else f'column_{i}' for i, h in enumerate(rows[0])]
            data_rows = rows[1:]

            return [
                {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                for row in data_rows
                if any(cell is not None for cell in row)
            ]

        except ImportError:
            raise ValueError("openpyxl library required for Excel parsing. Install: pip install openpyxl")
        except Exception as e:
            raise ValueError(f"Failed to parse Excel: {e}")

    def _parse_text(self, data: str, options: Dict) -> Dict:
        """Parse plain text"""
        split_by = options.get('split_by', 'lines')

        if split_by == 'lines':
            lines = data.split('\n')
            return {
                'text': data,
                'lines': lines,
                'line_count': len(lines),
                'char_count': len(data)
            }
        elif split_by == 'paragraphs':
            paragraphs = [p.strip() for p in data.split('\n\n') if p.strip()]
            return {
                'text': data,
                'paragraphs': paragraphs,
                'paragraph_count': len(paragraphs)
            }
        elif split_by == 'words':
            words = data.split()
            return {
                'text': data,
                'words': words,
                'word_count': len(words)
            }
        else:
            return {'text': data}

    def _parse_word(self, data: bytes, options: Dict) -> Dict:
        """Parse Word document"""
        try:
            from docx import Document
            from io import BytesIO

            doc = Document(BytesIO(data))

            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            tables = []

            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    table_data.append([cell.text for cell in row.cells])
                tables.append(table_data)

            return {
                'text': '\n'.join(paragraphs),
                'paragraphs': paragraphs,
                'tables': tables,
                'paragraph_count': len(paragraphs),
                'table_count': len(tables)
            }

        except ImportError:
            raise ValueError("python-docx library required for Word parsing. Install: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to parse Word document: {e}")

    def _parse_pdf(self, data: bytes, options: Dict) -> Dict:
        """Parse PDF document"""
        try:
            import PyPDF2
            from io import BytesIO

            pdf_reader = PyPDF2.PdfReader(BytesIO(data))

            pages = []
            for page in pdf_reader.pages:
                pages.append(page.extract_text())

            full_text = '\n\n'.join(pages)

            return {
                'text': full_text,
                'pages': pages,
                'page_count': len(pages)
            }

        except ImportError:
            raise ValueError("PyPDF2 library required for PDF parsing. Install: pip install PyPDF2")
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")

    def _parse_html(self, data: str, options: Dict) -> Dict:
        """Parse HTML content"""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(data, 'html.parser')

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Extract links
            links = [{'text': a.get_text(strip=True), 'href': a.get('href')}
                     for a in soup.find_all('a') if a.get('href')]

            # Extract headers
            headers = [{'level': h.name, 'text': h.get_text(strip=True)}
                       for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]

            return {
                'text': text,
                'links': links,
                'headers': headers,
                'title': soup.title.string if soup.title else None
            }

        except ImportError:
            # Fallback without BeautifulSoup
            import re
            text = re.sub(r'<[^>]+>', '', data)
            return {'text': text}

        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {e}")

    async def _parse_image(self, data: bytes, options: Dict) -> Dict:
        """
        Parse image using LLM vision or OCR

        Approaches:
        1. Vision LLM (preferred) - Understands image content intelligently
        2. OCR (fallback) - Extracts text only

        Options:
            extraction_prompt: Custom prompt for LLM (default: "Describe this image and extract any text, data, or structured information.")
            ocr_only: Force OCR-only mode (default: False)
            language: OCR language (default: 'eng')
        """
        try:
            # Convert bytes to base64 for LLM vision models
            image_base64 = base64.b64encode(data).decode('utf-8')

            extraction_prompt = options.get('extraction_prompt',
                "Describe this image in detail. Extract any text, numbers, tables, charts, or structured data you see. "
                "If there are any tables, format them clearly. If there's a chart or graph, describe the data points. "
                "Provide the information in a structured format."
            )

            ocr_only = options.get('ocr_only', False)

            result = {
                'image_size_bytes': len(data),
                'extraction_method': None,
                'text': '',
                'description': '',
                'structured_data': {},
                'confidence': None
            }

            # Try Vision LLM first (if available and enabled)
            if self.ollama_service and self.use_vision and not ocr_only:
                try:
                    logger.info(f"Using vision LLM: {self.llm_model}")

                    # Call vision LLM with image
                    vision_response = await self.ollama_service.generate(
                        model=self.llm_model,
                        prompt=extraction_prompt,
                        images=[image_base64]
                    )

                    if vision_response and 'response' in vision_response:
                        extracted_content = vision_response['response']

                        result['extraction_method'] = 'vision_llm'
                        result['text'] = extracted_content
                        result['description'] = extracted_content
                        result['llm_model'] = self.llm_model

                        # Try to extract structured data using LLM
                        if self.config.get('extract_structured', True):
                            structured = await self._extract_structured_from_text(extracted_content)
                            if structured:
                                result['structured_data'] = structured

                        logger.info("Vision LLM extraction successful")
                        return result

                except Exception as e:
                    logger.warning(f"Vision LLM failed: {e}, falling back to OCR")

            # Fallback to OCR
            if self.use_ocr:
                try:
                    import pytesseract
                    from PIL import Image
                    from io import BytesIO

                    # Convert bytes to PIL Image
                    image = Image.open(BytesIO(data))

                    # Extract text using OCR
                    language = options.get('language', 'eng')
                    ocr_text = pytesseract.image_to_string(image, lang=language)

                    result['extraction_method'] = 'ocr'
                    result['text'] = ocr_text.strip()
                    result['description'] = f"OCR extracted text ({language})"
                    result['image_dimensions'] = f"{image.width}x{image.height}"
                    result['image_format'] = image.format

                    logger.info("OCR extraction successful")
                    return result

                except ImportError:
                    logger.warning("pytesseract not available. Install: pip install pytesseract pillow")
                except Exception as e:
                    logger.warning(f"OCR failed: {e}")

            # If both methods fail
            result['extraction_method'] = 'failed'
            result['error'] = 'Both Vision LLM and OCR extraction failed. Ensure Ollama vision model is available or pytesseract is installed.'
            return result

        except Exception as e:
            raise ValueError(f"Failed to parse image: {e}")

    async def _extract_structured_from_text(self, text: str) -> Optional[Dict]:
        """
        Extract structured data from unstructured text using LLM
        """
        if not self.ollama_service:
            return None

        try:
            extraction_prompt = f"""Extract any structured data from the following text.
If there are tables, lists, key-value pairs, or other structured information, convert them to JSON format.

Text:
{text}

Return ONLY valid JSON with the structured data. If no structured data is found, return {{}}.
"""

            response = await self.ollama_service.generate(
                model=self.config.get('llm_model', 'llama3.2:3b'),
                prompt=extraction_prompt,
                temperature=0.1
            )

            if response and 'response' in response:
                # Try to parse JSON from response
                response_text = response['response'].strip()

                # Extract JSON from markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                try:
                    structured = json.loads(response_text)
                    return structured if structured else None
                except json.JSONDecodeError:
                    logger.warning("Failed to parse structured data as JSON")
                    return None

        except Exception as e:
            logger.warning(f"Structured extraction failed: {e}")
            return None

    async def _convert_to_output(self, parsed_data: Any, output_format: str, options: Dict) -> Any:
        """Convert parsed data to output format"""
        if output_format == 'json':
            return self._to_json(parsed_data, options)
        elif output_format == 'xml':
            return self._to_xml(parsed_data, options)
        elif output_format == 'csv':
            return self._to_csv(parsed_data, ',', options)
        elif output_format == 'tsv':
            return self._to_csv(parsed_data, '\t', options)
        elif output_format == 'text':
            return self._to_text(parsed_data, options)
        elif output_format == 'markdown':
            return self._to_markdown(parsed_data, options)
        elif output_format == 'key_value':
            return self._to_key_value(parsed_data, options)
        elif output_format == 'custom':
            delimiter = self.config.get('custom_delimiter', '|')
            return self._to_csv(parsed_data, delimiter, options)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _to_json(self, data: Any, options: Dict) -> str:
        """Convert to JSON"""
        indent = options.get('indent', 2)
        ensure_ascii = options.get('ensure_ascii', False)

        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

    def _to_xml(self, data: Any, options: Dict) -> str:
        """Convert to XML"""
        import xml.etree.ElementTree as ET

        root_name = options.get('root_name', 'root')
        item_name = options.get('item_name', 'item')

        root = ET.Element(root_name)
        self._dict_to_xml(data, root, item_name)

        return ET.tostring(root, encoding='unicode')

    def _dict_to_xml(self, data: Any, parent: Any, item_name: str):
        """Convert dictionary to XML elements"""
        import xml.etree.ElementTree as ET

        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith('@'):
                    # Attribute
                    parent.set(key[1:], str(value))
                elif key == '#text':
                    # Text content
                    parent.text = str(value)
                else:
                    # Child element
                    child = ET.SubElement(parent, str(key))
                    self._dict_to_xml(value, child, item_name)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, item_name)
                self._dict_to_xml(item, child, item_name)
        else:
            parent.text = str(data)

    def _to_csv(self, data: Any, delimiter: str, options: Dict) -> str:
        """Convert to CSV/TSV/Custom delimited"""
        include_headers = options.get('include_headers', True)

        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                # List of dictionaries
                output = StringIO()
                headers = list(data[0].keys())

                writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter)

                if include_headers:
                    writer.writeheader()

                writer.writerows(data)

                return output.getvalue()
            else:
                # List of lists
                output = StringIO()
                writer = csv.writer(output, delimiter=delimiter)

                for row in data:
                    writer.writerow(row if isinstance(row, (list, tuple)) else [row])

                return output.getvalue()
        elif isinstance(data, dict):
            # Dictionary - convert to key-value pairs
            output = StringIO()
            writer = csv.writer(output, delimiter=delimiter)

            if include_headers:
                writer.writerow(['Key', 'Value'])

            for key, value in data.items():
                writer.writerow([key, value])

            return output.getvalue()
        else:
            return str(data)

    def _to_text(self, data: Any, options: Dict) -> str:
        """Convert to plain text"""
        separator = options.get('separator', '\n')

        if isinstance(data, dict):
            if 'text' in data:
                return data['text']
            else:
                return separator.join(f"{k}: {v}" for k, v in data.items())
        elif isinstance(data, list):
            return separator.join(str(item) for item in data)
        else:
            return str(data)

    def _to_markdown(self, data: Any, options: Dict) -> str:
        """Convert to Markdown"""
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # List of dictionaries - convert to table
            headers = list(data[0].keys())

            md = '| ' + ' | '.join(headers) + ' |\n'
            md += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'

            for row in data:
                md += '| ' + ' | '.join(str(row.get(h, '')) for h in headers) + ' |\n'

            return md
        elif isinstance(data, dict):
            # Dictionary - convert to definition list
            md = ''
            for key, value in data.items():
                md += f"**{key}**: {value}\n\n"
            return md
        else:
            return str(data)

    def _to_key_value(self, data: Any, options: Dict) -> str:
        """Convert to Key: Value format"""
        separator = options.get('separator', ': ')
        line_separator = options.get('line_separator', '\n')

        if isinstance(data, dict):
            return line_separator.join(f"{k}{separator}{v}" for k, v in data.items())
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            result = []
            for i, item in enumerate(data):
                result.append(f"--- Item {i+1} ---")
                result.append(line_separator.join(f"{k}{separator}{v}" for k, v in item.items()))
            return line_separator.join(result)
        else:
            return str(data)

    def _count_rows(self, data: Any) -> Optional[int]:
        """Count number of rows in parsed data"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if 'lines' in data:
                return len(data['lines'])
            elif 'paragraphs' in data:
                return len(data['paragraphs'])
            elif 'pages' in data:
                return len(data['pages'])
        return None

    def _generate_preview(self, data: Any, max_length: int = 200) -> str:
        """Generate preview of output data"""
        data_str = str(data)
        if len(data_str) > max_length:
            return data_str[:max_length] + '...'
        return data_str


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'UniversalParserAgent',
    'ParseResult'
]
