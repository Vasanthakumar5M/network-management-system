"""
HTTPS Interception Module.

Provides HTTPS traffic interception, decryption, and analysis:
- Certificate generation with disguised profiles
- Content decoding (JSON, forms, compression)
- Traffic parsing and categorization
- Transparent proxy with mitmproxy
"""

from .cert_generator import (
    CERT_PROFILES,
    CertificateGenerator,
    CertificateInfo,
)
from .content_decoder import (
    ContentDecoder,
    ContentType,
    DecodedContent,
)
from .traffic_parser import (
    ParsedCookie,
    ParsedFlow,
    ParsedHeader,
    ParsedRequest,
    ParsedResponse,
    SensitivityLevel,
    TrafficCategory,
    TrafficParser,
)
from .transparent_proxy import (
    FlowEvent,
    ProxyConfig,
    TrafficInterceptor,
    TransparentProxy,
    cleanup_windows_redirect,
    setup_windows_redirect,
)

__all__ = [
    # Certificate Generator
    "CertificateGenerator",
    "CertificateInfo",
    "CERT_PROFILES",
    # Content Decoder
    "ContentDecoder",
    "ContentType",
    "DecodedContent",
    # Traffic Parser
    "TrafficParser",
    "TrafficCategory",
    "SensitivityLevel",
    "ParsedFlow",
    "ParsedRequest",
    "ParsedResponse",
    "ParsedHeader",
    "ParsedCookie",
    # Transparent Proxy
    "TransparentProxy",
    "ProxyConfig",
    "TrafficInterceptor",
    "FlowEvent",
    "setup_windows_redirect",
    "cleanup_windows_redirect",
]
