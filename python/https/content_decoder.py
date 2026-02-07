"""
Content Decoder for HTTP Traffic.

Decodes various content types from HTTP requests/responses:
- JSON parsing and formatting
- Form data (URL-encoded and multipart)
- Gzip/Brotli/Deflate decompression
- Base64 decoding
- Binary content detection
- Character encoding handling
"""

import base64
import gzip
import io
import json
import re
import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, unquote, unquote_plus


class ContentType(Enum):
    """HTTP content types."""
    JSON = "application/json"
    HTML = "text/html"
    XML = "text/xml"
    PLAIN = "text/plain"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    FORM_MULTIPART = "multipart/form-data"
    JAVASCRIPT = "application/javascript"
    CSS = "text/css"
    IMAGE = "image/*"
    VIDEO = "video/*"
    AUDIO = "audio/*"
    BINARY = "application/octet-stream"
    PDF = "application/pdf"
    UNKNOWN = "unknown"


@dataclass
class DecodedContent:
    """Represents decoded HTTP content."""
    content_type: ContentType
    mime_type: str
    encoding: str
    raw_size: int
    decoded_size: int
    is_binary: bool
    is_compressed: bool
    text_content: Optional[str] = None
    structured_content: Optional[Any] = None  # Parsed JSON, form data, etc.
    binary_preview: Optional[str] = None  # Hex preview for binary
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentDecoder:
    """
    Decodes HTTP request/response content into human-readable format.
    
    Handles compression, encoding, and various content types.
    """
    
    # Binary file signatures (magic bytes)
    BINARY_SIGNATURES = {
        b'\x89PNG': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'\x1f\x8b': 'application/gzip',
        b'RIFF': 'audio/wav',
        b'\x00\x00\x00\x1c': 'video/mp4',
        b'\x00\x00\x00\x18': 'video/mp4',
        b'\x00\x00\x00\x20': 'video/mp4',
    }
    
    # Text content types that should be displayed
    TEXT_TYPES = {
        'text/', 'application/json', 'application/javascript',
        'application/xml', 'application/xhtml', 'application/x-www-form-urlencoded'
    }
    
    def __init__(self, max_text_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize the content decoder.
        
        Args:
            max_text_size: Maximum size for text content (larger = binary preview)
        """
        self.max_text_size = max_text_size
    
    def decode(
        self,
        content: bytes,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        charset: Optional[str] = None
    ) -> DecodedContent:
        """
        Decode HTTP content.
        
        Args:
            content: Raw bytes from HTTP body
            content_type: Content-Type header value
            content_encoding: Content-Encoding header value (gzip, br, deflate)
            charset: Character set (utf-8, iso-8859-1, etc.)
            
        Returns:
            DecodedContent with parsed/decoded data
        """
        raw_size = len(content)
        is_compressed = False
        
        # Step 1: Decompress if needed
        if content_encoding:
            try:
                content, is_compressed = self._decompress(content, content_encoding)
            except Exception as e:
                return DecodedContent(
                    content_type=ContentType.UNKNOWN,
                    mime_type=content_type or "unknown",
                    encoding=charset or "unknown",
                    raw_size=raw_size,
                    decoded_size=raw_size,
                    is_binary=True,
                    is_compressed=True,
                    error=f"Decompression failed: {str(e)}"
                )
        
        decoded_size = len(content)
        
        # Step 2: Detect content type
        detected_type, mime_type = self._detect_content_type(content, content_type)
        
        # Step 3: Check if binary
        is_binary = self._is_binary(content, detected_type)
        
        # Step 4: Determine charset
        if charset is None:
            charset = self._detect_charset(content, content_type)
        
        # Step 5: Decode based on type
        if is_binary:
            return DecodedContent(
                content_type=detected_type,
                mime_type=mime_type,
                encoding=charset,
                raw_size=raw_size,
                decoded_size=decoded_size,
                is_binary=True,
                is_compressed=is_compressed,
                binary_preview=self._binary_preview(content),
                metadata=self._extract_binary_metadata(content, detected_type)
            )
        
        # Decode text content
        try:
            text_content = content.decode(charset, errors='replace')
        except Exception as e:
            text_content = content.decode('utf-8', errors='replace')
        
        # Parse structured content
        structured = None
        if detected_type == ContentType.JSON:
            structured = self._parse_json(text_content)
        elif detected_type == ContentType.FORM_URLENCODED:
            structured = self._parse_form_urlencoded(text_content)
        elif detected_type == ContentType.FORM_MULTIPART:
            structured = self._parse_multipart(content, content_type)
        elif detected_type == ContentType.HTML:
            structured = self._extract_html_info(text_content)
        
        return DecodedContent(
            content_type=detected_type,
            mime_type=mime_type,
            encoding=charset,
            raw_size=raw_size,
            decoded_size=decoded_size,
            is_binary=False,
            is_compressed=is_compressed,
            text_content=text_content,
            structured_content=structured
        )
    
    def _decompress(self, content: bytes, encoding: str) -> Tuple[bytes, bool]:
        """
        Decompress content based on Content-Encoding.
        
        Returns:
            Tuple of (decompressed bytes, was_compressed)
        """
        encoding = encoding.lower().strip()
        
        if encoding == 'gzip':
            return gzip.decompress(content), True
        
        elif encoding == 'deflate':
            try:
                # Try raw deflate first
                return zlib.decompress(content, -zlib.MAX_WBITS), True
            except zlib.error:
                # Try with header
                return zlib.decompress(content), True
        
        elif encoding == 'br':
            try:
                import brotli
                return brotli.decompress(content), True
            except ImportError:
                raise ImportError("brotli library required for br decompression")
        
        elif encoding == 'identity' or encoding == 'none':
            return content, False
        
        else:
            # Unknown encoding, return as-is
            return content, False
    
    def _detect_content_type(
        self,
        content: bytes,
        content_type_header: Optional[str]
    ) -> Tuple[ContentType, str]:
        """
        Detect content type from header and magic bytes.
        
        Returns:
            Tuple of (ContentType enum, mime type string)
        """
        mime_type = "application/octet-stream"
        
        if content_type_header:
            # Parse Content-Type header
            mime_type = content_type_header.split(';')[0].strip().lower()
        
        # Map to ContentType enum
        if 'json' in mime_type:
            return ContentType.JSON, mime_type
        elif 'html' in mime_type:
            return ContentType.HTML, mime_type
        elif 'xml' in mime_type:
            return ContentType.XML, mime_type
        elif mime_type == 'application/x-www-form-urlencoded':
            return ContentType.FORM_URLENCODED, mime_type
        elif 'multipart/form-data' in mime_type:
            return ContentType.FORM_MULTIPART, mime_type
        elif 'javascript' in mime_type:
            return ContentType.JAVASCRIPT, mime_type
        elif 'css' in mime_type:
            return ContentType.CSS, mime_type
        elif mime_type.startswith('image/'):
            return ContentType.IMAGE, mime_type
        elif mime_type.startswith('video/'):
            return ContentType.VIDEO, mime_type
        elif mime_type.startswith('audio/'):
            return ContentType.AUDIO, mime_type
        elif mime_type == 'application/pdf':
            return ContentType.PDF, mime_type
        elif mime_type.startswith('text/'):
            return ContentType.PLAIN, mime_type
        
        # Detect from magic bytes
        for signature, detected_mime in self.BINARY_SIGNATURES.items():
            if content.startswith(signature):
                return self._mime_to_content_type(detected_mime), detected_mime
        
        # Try to detect if it's text
        if self._looks_like_text(content[:1024]):
            return ContentType.PLAIN, "text/plain"
        
        return ContentType.BINARY, mime_type
    
    def _mime_to_content_type(self, mime: str) -> ContentType:
        """Convert MIME type to ContentType enum."""
        if mime.startswith('image/'):
            return ContentType.IMAGE
        elif mime.startswith('video/'):
            return ContentType.VIDEO
        elif mime.startswith('audio/'):
            return ContentType.AUDIO
        elif mime == 'application/pdf':
            return ContentType.PDF
        return ContentType.BINARY
    
    def _is_binary(self, content: bytes, content_type: ContentType) -> bool:
        """Check if content is binary."""
        binary_types = {
            ContentType.IMAGE, ContentType.VIDEO, ContentType.AUDIO,
            ContentType.BINARY, ContentType.PDF
        }
        
        if content_type in binary_types:
            return True
        
        if len(content) > self.max_text_size:
            return True
        
        return not self._looks_like_text(content)
    
    def _looks_like_text(self, content: bytes) -> bool:
        """Heuristic check if content looks like text."""
        if not content:
            return True
        
        # Check for null bytes (usually indicates binary)
        if b'\x00' in content[:1024]:
            return False
        
        # Check if most bytes are printable ASCII or UTF-8
        try:
            text = content.decode('utf-8')
            # Count printable characters
            printable = sum(1 for c in text if c.isprintable() or c in '\n\r\t')
            return printable / len(text) > 0.85
        except UnicodeDecodeError:
            return False
    
    def _detect_charset(
        self,
        content: bytes,
        content_type_header: Optional[str]
    ) -> str:
        """Detect character encoding."""
        # Check Content-Type header for charset
        if content_type_header:
            match = re.search(r'charset=([^\s;]+)', content_type_header, re.I)
            if match:
                return match.group(1).strip('"\'')
        
        # Check for BOM
        if content.startswith(b'\xef\xbb\xbf'):
            return 'utf-8'
        elif content.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif content.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        
        # Check HTML meta tag
        if b'<meta' in content[:2048].lower():
            meta_match = re.search(
                rb'<meta[^>]+charset=["\']?([^"\'\s>]+)',
                content[:2048],
                re.I
            )
            if meta_match:
                return meta_match.group(1).decode('ascii', errors='ignore')
        
        # Default to UTF-8
        return 'utf-8'
    
    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON content."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def _parse_form_urlencoded(self, text: str) -> Dict[str, List[str]]:
        """Parse URL-encoded form data."""
        try:
            # Decode URL encoding
            decoded = unquote_plus(text)
            return parse_qs(decoded, keep_blank_values=True)
        except Exception:
            return {"raw": [text]}
    
    def _parse_multipart(
        self,
        content: bytes,
        content_type: str
    ) -> List[Dict[str, Any]]:
        """Parse multipart form data."""
        parts = []
        
        # Extract boundary
        match = re.search(r'boundary=([^\s;]+)', content_type, re.I)
        if not match:
            return parts
        
        boundary = match.group(1).strip('"')
        boundary_bytes = f'--{boundary}'.encode()
        
        # Split by boundary
        sections = content.split(boundary_bytes)
        
        for section in sections[1:]:  # Skip preamble
            if section.strip() in (b'', b'--', b'--\r\n'):
                continue
            
            # Split headers from body
            header_end = section.find(b'\r\n\r\n')
            if header_end == -1:
                continue
            
            headers_raw = section[:header_end]
            body = section[header_end + 4:].rstrip(b'\r\n')
            
            # Parse headers
            headers = {}
            for line in headers_raw.split(b'\r\n'):
                if b':' in line:
                    key, value = line.split(b':', 1)
                    headers[key.decode().strip().lower()] = value.decode().strip()
            
            # Extract field name
            name = None
            filename = None
            if 'content-disposition' in headers:
                disp = headers['content-disposition']
                name_match = re.search(r'name="([^"]+)"', disp)
                if name_match:
                    name = name_match.group(1)
                file_match = re.search(r'filename="([^"]+)"', disp)
                if file_match:
                    filename = file_match.group(1)
            
            part = {
                "name": name,
                "headers": headers
            }
            
            if filename:
                part["filename"] = filename
                part["size"] = len(body)
                part["preview"] = self._binary_preview(body[:64])
            else:
                # Text field
                try:
                    part["value"] = body.decode('utf-8')
                except UnicodeDecodeError:
                    part["value"] = body.decode('latin-1')
            
            parts.append(part)
        
        return parts
    
    def _extract_html_info(self, html: str) -> Dict[str, Any]:
        """Extract useful information from HTML."""
        info = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        if title_match:
            info['title'] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
            html, re.I
        )
        if desc_match:
            info['description'] = desc_match.group(1).strip()
        
        # Count forms
        form_count = len(re.findall(r'<form\b', html, re.I))
        if form_count:
            info['forms'] = form_count
        
        # Extract form actions
        form_actions = re.findall(r'<form[^>]+action=["\']([^"\']+)', html, re.I)
        if form_actions:
            info['form_actions'] = form_actions
        
        # Extract links
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)', html, re.I)
        if links:
            info['link_count'] = len(links)
        
        # Check for login forms
        if re.search(r'type=["\']password["\']', html, re.I):
            info['has_password_field'] = True
        
        return info
    
    def _binary_preview(self, content: bytes, max_bytes: int = 64) -> str:
        """Generate hex preview of binary content."""
        preview_bytes = content[:max_bytes]
        hex_str = preview_bytes.hex()
        
        # Format as hex dump
        formatted = ' '.join(
            hex_str[i:i+2] for i in range(0, len(hex_str), 2)
        )
        
        if len(content) > max_bytes:
            formatted += f' ... ({len(content)} bytes total)'
        
        return formatted
    
    def _extract_binary_metadata(
        self,
        content: bytes,
        content_type: ContentType
    ) -> Dict[str, Any]:
        """Extract metadata from binary content."""
        metadata = {
            "size_bytes": len(content),
            "size_human": self._human_size(len(content))
        }
        
        if content_type == ContentType.IMAGE:
            metadata.update(self._extract_image_info(content))
        
        return metadata
    
    def _extract_image_info(self, content: bytes) -> Dict[str, Any]:
        """Extract image dimensions and format."""
        info = {}
        
        # PNG
        if content.startswith(b'\x89PNG'):
            info['format'] = 'PNG'
            if len(content) > 24:
                width = int.from_bytes(content[16:20], 'big')
                height = int.from_bytes(content[20:24], 'big')
                info['dimensions'] = f"{width}x{height}"
        
        # JPEG
        elif content.startswith(b'\xff\xd8\xff'):
            info['format'] = 'JPEG'
            # Find SOF marker for dimensions
            i = 2
            while i < len(content) - 9:
                if content[i] == 0xff:
                    marker = content[i + 1]
                    if marker in (0xc0, 0xc1, 0xc2):  # SOF markers
                        height = int.from_bytes(content[i+5:i+7], 'big')
                        width = int.from_bytes(content[i+7:i+9], 'big')
                        info['dimensions'] = f"{width}x{height}"
                        break
                    length = int.from_bytes(content[i+2:i+4], 'big')
                    i += 2 + length
                else:
                    i += 1
        
        # GIF
        elif content.startswith(b'GIF'):
            info['format'] = 'GIF'
            if len(content) > 10:
                width = int.from_bytes(content[6:8], 'little')
                height = int.from_bytes(content[8:10], 'little')
                info['dimensions'] = f"{width}x{height}"
        
        return info
    
    def _human_size(self, size: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def decode_base64(self, data: str) -> Tuple[bytes, bool]:
        """
        Decode Base64 encoded data.
        
        Returns:
            Tuple of (decoded bytes, success)
        """
        try:
            # Handle URL-safe base64
            data = data.replace('-', '+').replace('_', '/')
            
            # Add padding if needed
            padding = 4 - (len(data) % 4)
            if padding != 4:
                data += '=' * padding
            
            return base64.b64decode(data), True
        except Exception:
            return b'', False
    
    def format_for_display(
        self,
        decoded: DecodedContent,
        max_lines: int = 100,
        indent: int = 2
    ) -> str:
        """
        Format decoded content for human-readable display.
        
        Args:
            decoded: DecodedContent object
            max_lines: Maximum lines to display
            indent: JSON indent spaces
            
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Header info
        lines.append(f"Content-Type: {decoded.mime_type}")
        lines.append(f"Encoding: {decoded.encoding}")
        lines.append(f"Size: {self._human_size(decoded.decoded_size)}")
        
        if decoded.is_compressed:
            lines.append(f"Compressed: {self._human_size(decoded.raw_size)} -> {self._human_size(decoded.decoded_size)}")
        
        lines.append("")
        
        if decoded.error:
            lines.append(f"Error: {decoded.error}")
            return '\n'.join(lines)
        
        if decoded.is_binary:
            lines.append("[Binary Content]")
            if decoded.metadata:
                for key, value in decoded.metadata.items():
                    lines.append(f"  {key}: {value}")
            if decoded.binary_preview:
                lines.append("")
                lines.append("Preview (hex):")
                lines.append(decoded.binary_preview)
        else:
            if decoded.structured_content:
                if decoded.content_type == ContentType.JSON:
                    try:
                        formatted = json.dumps(
                            decoded.structured_content,
                            indent=indent,
                            ensure_ascii=False
                        )
                        lines.append("[JSON]")
                        for i, line in enumerate(formatted.split('\n')):
                            if i >= max_lines:
                                lines.append(f"... ({len(formatted.split(chr(10)))} total lines)")
                                break
                            lines.append(line)
                    except Exception:
                        lines.append(decoded.text_content or "")
                
                elif decoded.content_type == ContentType.FORM_URLENCODED:
                    lines.append("[Form Data]")
                    for key, values in decoded.structured_content.items():
                        for value in values:
                            lines.append(f"  {key}: {value}")
                
                elif decoded.content_type == ContentType.FORM_MULTIPART:
                    lines.append("[Multipart Form]")
                    for part in decoded.structured_content:
                        name = part.get('name', 'unnamed')
                        if 'filename' in part:
                            lines.append(f"  [{name}] File: {part['filename']} ({part['size']} bytes)")
                        else:
                            lines.append(f"  [{name}]: {part.get('value', '')}")
                
                elif decoded.content_type == ContentType.HTML:
                    if 'title' in decoded.structured_content:
                        lines.append(f"[HTML] Title: {decoded.structured_content['title']}")
                    if 'description' in decoded.structured_content:
                        lines.append(f"Description: {decoded.structured_content['description']}")
                    if decoded.structured_content.get('has_password_field'):
                        lines.append("⚠️ Contains password field")
                    lines.append("")
                    # Add truncated HTML
                    html_lines = (decoded.text_content or "").split('\n')
                    for i, line in enumerate(html_lines):
                        if i >= max_lines:
                            lines.append(f"... ({len(html_lines)} total lines)")
                            break
                        lines.append(line)
            else:
                # Plain text
                text_lines = (decoded.text_content or "").split('\n')
                for i, line in enumerate(text_lines):
                    if i >= max_lines:
                        lines.append(f"... ({len(text_lines)} total lines)")
                        break
                    lines.append(line)
        
        return '\n'.join(lines)


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for content decoding."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Decode HTTP content")
    parser.add_argument("--file", help="File to decode")
    parser.add_argument("--content-type", help="Content-Type header")
    parser.add_argument("--encoding", help="Content-Encoding (gzip, br, deflate)")
    parser.add_argument("--charset", help="Character encoding")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                       help="Output format")
    
    args = parser.parse_args()
    
    decoder = ContentDecoder()
    
    try:
        if args.file:
            with open(args.file, 'rb') as f:
                content = f.read()
        else:
            # Read from stdin
            content = sys.stdin.buffer.read()
        
        decoded = decoder.decode(
            content=content,
            content_type=args.content_type,
            content_encoding=args.encoding,
            charset=args.charset
        )
        
        if args.format == "json":
            output_json({
                "success": True,
                "content_type": decoded.content_type.value,
                "mime_type": decoded.mime_type,
                "encoding": decoded.encoding,
                "raw_size": decoded.raw_size,
                "decoded_size": decoded.decoded_size,
                "is_binary": decoded.is_binary,
                "is_compressed": decoded.is_compressed,
                "text_content": decoded.text_content,
                "structured_content": decoded.structured_content,
                "binary_preview": decoded.binary_preview,
                "metadata": decoded.metadata
            })
        else:
            print(decoder.format_for_display(decoded))
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
