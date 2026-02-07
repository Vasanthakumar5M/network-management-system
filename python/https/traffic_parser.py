"""
Traffic Parser for HTTP/HTTPS Traffic.

Parses HTTP requests and responses into structured, human-readable format.
Handles:
- Request/response parsing
- Header extraction
- Cookie parsing
- URL decoding
- Sensitive data detection (passwords, tokens, etc.)
- Traffic categorization
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from .content_decoder import ContentDecoder, ContentType, DecodedContent


class TrafficCategory(Enum):
    """Categories for traffic classification."""
    SOCIAL_MEDIA = "social_media"
    STREAMING = "streaming"
    GAMING = "gaming"
    SHOPPING = "shopping"
    SEARCH = "search"
    EMAIL = "email"
    NEWS = "news"
    ADULT = "adult"
    MESSAGING = "messaging"
    EDUCATION = "education"
    PRODUCTIVITY = "productivity"
    FINANCE = "finance"
    ADVERTISING = "advertising"
    ANALYTICS = "analytics"
    API = "api"
    OTHER = "other"


class SensitivityLevel(Enum):
    """Sensitivity level of content."""
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"  # Contains passwords, tokens, etc.
    CRITICAL = "critical"  # Financial data, SSN, etc.


@dataclass
class ParsedCookie:
    """Parsed HTTP cookie."""
    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = None
    expires: Optional[str] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None


@dataclass
class ParsedHeader:
    """Parsed HTTP header with metadata."""
    name: str
    value: str
    is_sensitive: bool = False  # Contains auth tokens, etc.


@dataclass
class ParsedRequest:
    """Parsed HTTP request."""
    timestamp: str
    method: str
    url: str
    host: str
    path: str
    query_params: Dict[str, List[str]]
    headers: List[ParsedHeader]
    cookies: List[ParsedCookie]
    body: Optional[DecodedContent]
    content_length: int
    client_ip: str
    category: TrafficCategory
    sensitivity: SensitivityLevel
    sensitive_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedResponse:
    """Parsed HTTP response."""
    timestamp: str
    status_code: int
    status_message: str
    headers: List[ParsedHeader]
    cookies: List[ParsedCookie]
    body: Optional[DecodedContent]
    content_length: int
    content_type: str
    sensitivity: SensitivityLevel
    sensitive_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedFlow:
    """Complete HTTP request/response flow."""
    id: str
    request: ParsedRequest
    response: Optional[ParsedResponse]
    duration_ms: int
    intercepted: bool
    blocked: bool
    block_reason: Optional[str] = None
    alerts: List[str] = field(default_factory=list)


# Domain patterns for categorization
CATEGORY_PATTERNS = {
    TrafficCategory.SOCIAL_MEDIA: [
        r'facebook\.com', r'instagram\.com', r'twitter\.com', r'x\.com',
        r'tiktok\.com', r'snapchat\.com', r'linkedin\.com', r'reddit\.com',
        r'pinterest\.com', r'tumblr\.com', r'discord\.com', r'discord\.gg',
    ],
    TrafficCategory.STREAMING: [
        r'youtube\.com', r'netflix\.com', r'hulu\.com', r'disneyplus\.com',
        r'twitch\.tv', r'spotify\.com', r'soundcloud\.com', r'vimeo\.com',
        r'dailymotion\.com', r'crunchyroll\.com', r'hbomax\.com',
    ],
    TrafficCategory.GAMING: [
        r'steampowered\.com', r'epicgames\.com', r'roblox\.com', r'minecraft\.net',
        r'ea\.com', r'blizzard\.com', r'ubisoft\.com', r'xbox\.com',
        r'playstation\.com', r'nintendo\.com', r'itch\.io',
    ],
    TrafficCategory.SHOPPING: [
        r'amazon\.com', r'ebay\.com', r'walmart\.com', r'target\.com',
        r'etsy\.com', r'shopify\.com', r'aliexpress\.com', r'wish\.com',
    ],
    TrafficCategory.SEARCH: [
        r'google\.com/search', r'bing\.com/search', r'duckduckgo\.com',
        r'yahoo\.com/search', r'baidu\.com',
    ],
    TrafficCategory.EMAIL: [
        r'gmail\.com', r'mail\.google\.com', r'outlook\.com', r'mail\.yahoo\.com',
        r'protonmail\.com', r'icloud\.com/mail',
    ],
    TrafficCategory.MESSAGING: [
        r'whatsapp\.com', r'telegram\.org', r'signal\.org', r'messenger\.com',
        r'slack\.com', r'teams\.microsoft\.com', r'zoom\.us',
    ],
    TrafficCategory.NEWS: [
        r'cnn\.com', r'bbc\.com', r'nytimes\.com', r'foxnews\.com',
        r'reuters\.com', r'apnews\.com', r'theguardian\.com',
    ],
    TrafficCategory.EDUCATION: [
        r'khanacademy\.org', r'coursera\.org', r'udemy\.com', r'edx\.org',
        r'duolingo\.com', r'quizlet\.com', r'chegg\.com',
    ],
    TrafficCategory.FINANCE: [
        r'paypal\.com', r'venmo\.com', r'chase\.com', r'bankofamerica\.com',
        r'wellsfargo\.com', r'coinbase\.com', r'robinhood\.com',
    ],
    TrafficCategory.ADVERTISING: [
        r'doubleclick\.net', r'googlesyndication\.com', r'googleadservices\.com',
        r'facebook\.com/tr', r'ads\.', r'adservice\.',
    ],
    TrafficCategory.ANALYTICS: [
        r'google-analytics\.com', r'googletagmanager\.com', r'segment\.com',
        r'mixpanel\.com', r'amplitude\.com', r'hotjar\.com',
    ],
    TrafficCategory.ADULT: [
        r'pornhub\.com', r'xvideos\.com', r'xnxx\.com', r'xhamster\.com',
        r'onlyfans\.com', r'chaturbate\.com',
    ],
}

# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    'password': [
        r'\bpassword\b', r'\bpasswd\b', r'\bpass\b', r'\bpwd\b',
        r'\bsecret\b', r'\bcredential\b',
    ],
    'token': [
        r'\btoken\b', r'\bapi[_-]?key\b', r'\baccess[_-]?token\b',
        r'\bbearer\b', r'\bauth\b', r'\bsession\b',
    ],
    'credit_card': [
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        r'\bcvv\b', r'\bcvc\b', r'\bcard[_-]?number\b',
    ],
    'ssn': [
        r'\b\d{3}-\d{2}-\d{4}\b',
        r'\bssn\b', r'\bsocial[_-]?security\b',
    ],
    'email': [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ],
    'phone': [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        r'\+\d{1,3}[-.]?\d{3,14}\b',
    ],
}


class TrafficParser:
    """
    Parses HTTP traffic into structured, human-readable format.
    
    Works with mitmproxy flow objects or raw HTTP data.
    """
    
    def __init__(
        self,
        detect_sensitive: bool = True,
        categorize: bool = True,
        max_body_size: int = 5 * 1024 * 1024  # 5MB
    ):
        """
        Initialize the traffic parser.
        
        Args:
            detect_sensitive: Whether to detect sensitive data
            categorize: Whether to categorize traffic by domain
            max_body_size: Maximum body size to parse (larger bodies truncated)
        """
        self.detect_sensitive = detect_sensitive
        self.categorize = categorize
        self.max_body_size = max_body_size
        self.content_decoder = ContentDecoder(max_text_size=max_body_size)
        
        # Compile regex patterns
        self._category_patterns = {
            cat: [re.compile(p, re.I) for p in patterns]
            for cat, patterns in CATEGORY_PATTERNS.items()
        }
        self._sensitive_patterns = {
            name: [re.compile(p, re.I) for p in patterns]
            for name, patterns in SENSITIVE_PATTERNS.items()
        }
    
    def parse_mitmproxy_flow(self, flow) -> ParsedFlow:
        """
        Parse a mitmproxy flow object.
        
        Args:
            flow: mitmproxy.http.HTTPFlow object
            
        Returns:
            ParsedFlow with structured data
        """
        request = self._parse_mitmproxy_request(flow.request)
        response = None
        duration_ms = 0
        
        if flow.response:
            response = self._parse_mitmproxy_response(flow.response)
            # Calculate duration
            if hasattr(flow, 'timestamp_start') and hasattr(flow, 'timestamp_end'):
                if flow.timestamp_end and flow.timestamp_start:
                    duration_ms = int((flow.timestamp_end - flow.timestamp_start) * 1000)
        
        # Check for alerts
        alerts = self._generate_alerts(request, response)
        
        return ParsedFlow(
            id=flow.id if hasattr(flow, 'id') else str(id(flow)),
            request=request,
            response=response,
            duration_ms=duration_ms,
            intercepted=getattr(flow, 'intercepted', False),
            blocked=getattr(flow, 'killed', False),
            block_reason=getattr(flow, 'kill_reason', None),
            alerts=alerts
        )
    
    def _parse_mitmproxy_request(self, request) -> ParsedRequest:
        """Parse mitmproxy request object."""
        # Parse URL
        parsed_url = urlparse(request.pretty_url if hasattr(request, 'pretty_url') else request.url)
        
        # Parse query parameters
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)
        
        # Parse headers
        headers = []
        sensitive_headers = []
        for name, value in request.headers.items():
            is_sensitive = self._is_sensitive_header(name, value)
            headers.append(ParsedHeader(
                name=name,
                value=value,
                is_sensitive=is_sensitive
            ))
            if is_sensitive:
                sensitive_headers.append(name)
        
        # Parse cookies
        cookies = self._parse_cookies(request.headers.get('cookie', ''))
        
        # Parse body
        body = None
        if request.content:
            content_type = request.headers.get('content-type', '')
            content_encoding = request.headers.get('content-encoding', '')
            
            body = self.content_decoder.decode(
                content=request.content[:self.max_body_size],
                content_type=content_type,
                content_encoding=content_encoding
            )
        
        # Categorize
        host = parsed_url.netloc or request.host
        category = self._categorize_domain(host) if self.categorize else TrafficCategory.OTHER
        
        # Detect sensitivity
        sensitivity, sensitive_fields = self._analyze_sensitivity(
            query_params=query_params,
            headers=headers,
            body=body,
            sensitive_headers=sensitive_headers
        )
        
        return ParsedRequest(
            timestamp=datetime.utcnow().isoformat(),
            method=request.method,
            url=request.pretty_url if hasattr(request, 'pretty_url') else request.url,
            host=host,
            path=parsed_url.path or '/',
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            body=body,
            content_length=len(request.content) if request.content else 0,
            client_ip=getattr(request, 'client_conn', {}).get('address', ('unknown', 0))[0]
                      if hasattr(request, 'client_conn') else 'unknown',
            category=category,
            sensitivity=sensitivity,
            sensitive_fields=sensitive_fields
        )
    
    def _parse_mitmproxy_response(self, response) -> ParsedResponse:
        """Parse mitmproxy response object."""
        # Parse headers
        headers = []
        sensitive_headers = []
        for name, value in response.headers.items():
            is_sensitive = self._is_sensitive_header(name, value)
            headers.append(ParsedHeader(
                name=name,
                value=value,
                is_sensitive=is_sensitive
            ))
            if is_sensitive:
                sensitive_headers.append(name)
        
        # Parse set-cookie headers
        cookies = []
        for cookie in response.headers.get_all('set-cookie'):
            parsed = self._parse_set_cookie(cookie)
            if parsed:
                cookies.append(parsed)
        
        # Parse body
        body = None
        content_type = response.headers.get('content-type', '')
        if response.content:
            content_encoding = response.headers.get('content-encoding', '')
            
            body = self.content_decoder.decode(
                content=response.content[:self.max_body_size],
                content_type=content_type,
                content_encoding=content_encoding
            )
        
        # Detect sensitivity in response
        sensitivity, sensitive_fields = self._analyze_sensitivity(
            headers=headers,
            body=body,
            sensitive_headers=sensitive_headers
        )
        
        return ParsedResponse(
            timestamp=datetime.utcnow().isoformat(),
            status_code=response.status_code,
            status_message=response.reason if hasattr(response, 'reason') else '',
            headers=headers,
            cookies=cookies,
            body=body,
            content_length=len(response.content) if response.content else 0,
            content_type=content_type,
            sensitivity=sensitivity,
            sensitive_fields=sensitive_fields
        )
    
    def _parse_cookies(self, cookie_header: str) -> List[ParsedCookie]:
        """Parse Cookie header into list of cookies."""
        cookies = []
        if not cookie_header:
            return cookies
        
        for part in cookie_header.split(';'):
            part = part.strip()
            if '=' in part:
                name, value = part.split('=', 1)
                cookies.append(ParsedCookie(
                    name=name.strip(),
                    value=value.strip()
                ))
        
        return cookies
    
    def _parse_set_cookie(self, set_cookie: str) -> Optional[ParsedCookie]:
        """Parse Set-Cookie header."""
        if not set_cookie:
            return None
        
        parts = set_cookie.split(';')
        if not parts:
            return None
        
        # First part is name=value
        main = parts[0].strip()
        if '=' not in main:
            return None
        
        name, value = main.split('=', 1)
        
        cookie = ParsedCookie(
            name=name.strip(),
            value=value.strip()
        )
        
        # Parse attributes
        for part in parts[1:]:
            part = part.strip().lower()
            if '=' in part:
                attr_name, attr_value = part.split('=', 1)
                attr_name = attr_name.strip()
                attr_value = attr_value.strip()
                
                if attr_name == 'domain':
                    cookie.domain = attr_value
                elif attr_name == 'path':
                    cookie.path = attr_value
                elif attr_name == 'expires':
                    cookie.expires = attr_value
                elif attr_name == 'samesite':
                    cookie.same_site = attr_value
            else:
                if part == 'secure':
                    cookie.secure = True
                elif part == 'httponly':
                    cookie.http_only = True
        
        return cookie
    
    def _is_sensitive_header(self, name: str, value: str) -> bool:
        """Check if header contains sensitive data."""
        sensitive_names = {
            'authorization', 'cookie', 'set-cookie', 'x-api-key',
            'x-auth-token', 'x-csrf-token', 'x-access-token'
        }
        
        if name.lower() in sensitive_names:
            return True
        
        # Check value patterns
        for patterns in self._sensitive_patterns.values():
            for pattern in patterns:
                if pattern.search(value):
                    return True
        
        return False
    
    def _categorize_domain(self, domain: str) -> TrafficCategory:
        """Categorize domain into traffic category."""
        domain = domain.lower()
        
        for category, patterns in self._category_patterns.items():
            for pattern in patterns:
                if pattern.search(domain):
                    return category
        
        return TrafficCategory.OTHER
    
    def _analyze_sensitivity(
        self,
        query_params: Optional[Dict[str, List[str]]] = None,
        headers: Optional[List[ParsedHeader]] = None,
        body: Optional[DecodedContent] = None,
        sensitive_headers: Optional[List[str]] = None
    ) -> Tuple[SensitivityLevel, List[str]]:
        """
        Analyze content for sensitive data.
        
        Returns:
            Tuple of (sensitivity level, list of sensitive field names)
        """
        if not self.detect_sensitive:
            return SensitivityLevel.PUBLIC, []
        
        sensitive_fields = []
        has_critical = False
        has_sensitive = False
        has_private = False
        
        # Check query parameters
        if query_params:
            for param, values in query_params.items():
                sensitivity = self._check_field_sensitivity(param, ' '.join(values))
                if sensitivity:
                    sensitive_fields.append(f"query:{param}")
                    if sensitivity == 'critical':
                        has_critical = True
                    elif sensitivity == 'sensitive':
                        has_sensitive = True
                    else:
                        has_private = True
        
        # Check sensitive headers
        if sensitive_headers:
            sensitive_fields.extend(f"header:{h}" for h in sensitive_headers)
            has_sensitive = True
        
        # Check body content
        if body and body.text_content:
            # Check structured content (JSON, forms)
            if body.structured_content:
                if isinstance(body.structured_content, dict):
                    for key, value in self._flatten_dict(body.structured_content):
                        sensitivity = self._check_field_sensitivity(key, str(value))
                        if sensitivity:
                            sensitive_fields.append(f"body:{key}")
                            if sensitivity == 'critical':
                                has_critical = True
                            elif sensitivity == 'sensitive':
                                has_sensitive = True
                            else:
                                has_private = True
            
            # Check raw text for patterns
            for pattern_name, patterns in self._sensitive_patterns.items():
                for pattern in patterns:
                    if pattern.search(body.text_content):
                        if pattern_name not in sensitive_fields:
                            sensitive_fields.append(f"content:{pattern_name}")
                        if pattern_name in ('credit_card', 'ssn'):
                            has_critical = True
                        elif pattern_name in ('password', 'token'):
                            has_sensitive = True
                        else:
                            has_private = True
        
        # Determine overall sensitivity level
        if has_critical:
            return SensitivityLevel.CRITICAL, sensitive_fields
        elif has_sensitive:
            return SensitivityLevel.SENSITIVE, sensitive_fields
        elif has_private:
            return SensitivityLevel.PRIVATE, sensitive_fields
        
        return SensitivityLevel.PUBLIC, []
    
    def _check_field_sensitivity(
        self,
        field_name: str,
        value: str
    ) -> Optional[str]:
        """Check if a field contains sensitive data."""
        field_lower = field_name.lower()
        
        # Check field name
        for pattern_name, patterns in self._sensitive_patterns.items():
            for pattern in patterns:
                if pattern.search(field_lower):
                    if pattern_name in ('credit_card', 'ssn'):
                        return 'critical'
                    elif pattern_name in ('password', 'token'):
                        return 'sensitive'
                    return 'private'
        
        # Check value for patterns
        if value:
            for pattern_name, patterns in self._sensitive_patterns.items():
                for pattern in patterns:
                    if pattern.search(value):
                        if pattern_name in ('credit_card', 'ssn'):
                            return 'critical'
                        elif pattern_name in ('password', 'token'):
                            return 'sensitive'
                        return 'private'
        
        return None
    
    def _flatten_dict(
        self,
        d: dict,
        parent_key: str = '',
        sep: str = '.'
    ):
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep))
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        return items
    
    def _generate_alerts(
        self,
        request: ParsedRequest,
        response: Optional[ParsedResponse]
    ) -> List[str]:
        """Generate alerts based on traffic analysis."""
        alerts = []
        
        # Adult content alert
        if request.category == TrafficCategory.ADULT:
            alerts.append("ADULT_CONTENT")
        
        # Sensitive data alerts
        if request.sensitivity == SensitivityLevel.CRITICAL:
            alerts.append("CRITICAL_DATA_TRANSMITTED")
        elif request.sensitivity == SensitivityLevel.SENSITIVE:
            alerts.append("SENSITIVE_DATA_TRANSMITTED")
        
        # Login detection
        if request.body and request.body.structured_content:
            if isinstance(request.body.structured_content, dict):
                keys = str(request.body.structured_content.keys()).lower()
                if 'password' in keys and ('email' in keys or 'username' in keys):
                    alerts.append("LOGIN_ATTEMPT")
        
        # Financial activity
        if request.category == TrafficCategory.FINANCE:
            alerts.append("FINANCIAL_ACTIVITY")
        
        return alerts
    
    def format_flow_summary(self, flow: ParsedFlow) -> str:
        """Format flow as human-readable summary."""
        lines = []
        
        # Request summary
        req = flow.request
        lines.append(f"[{req.timestamp}] {req.method} {req.url}")
        lines.append(f"  Host: {req.host}")
        lines.append(f"  Category: {req.category.value}")
        
        if req.sensitive_fields:
            lines.append(f"  ⚠️ Sensitive: {', '.join(req.sensitive_fields)}")
        
        if req.body and not req.body.is_binary:
            lines.append(f"  Request Body: {req.body.content_type.value}")
            if req.body.structured_content:
                lines.append(f"    {json.dumps(req.body.structured_content, indent=4)[:500]}")
        
        # Response summary
        if flow.response:
            resp = flow.response
            lines.append(f"  Response: {resp.status_code} {resp.status_message}")
            lines.append(f"  Content-Type: {resp.content_type}")
            lines.append(f"  Size: {resp.content_length} bytes")
            lines.append(f"  Duration: {flow.duration_ms}ms")
            
            if resp.sensitive_fields:
                lines.append(f"  ⚠️ Sensitive: {', '.join(resp.sensitive_fields)}")
        
        # Alerts
        if flow.alerts:
            lines.append(f"  🚨 Alerts: {', '.join(flow.alerts)}")
        
        if flow.blocked:
            lines.append(f"  🛑 BLOCKED: {flow.block_reason}")
        
        return '\n'.join(lines)
    
    def to_dict(self, flow: ParsedFlow) -> Dict[str, Any]:
        """Convert ParsedFlow to dictionary for JSON serialization."""
        def dataclass_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                result = {}
                for field_name in obj.__dataclass_fields__:
                    value = getattr(obj, field_name)
                    result[field_name] = dataclass_to_dict(value)
                return result
            elif isinstance(obj, list):
                return [dataclass_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: dataclass_to_dict(v) for k, v in obj.items()}
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        return dataclass_to_dict(flow)


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for traffic parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse HTTP traffic")
    parser.add_argument("--action", choices=["categories", "test"],
                       default="categories", help="Action to perform")
    
    args = parser.parse_args()
    
    traffic_parser = TrafficParser()
    
    try:
        if args.action == "categories":
            output_json({
                "success": True,
                "categories": [c.value for c in TrafficCategory],
                "sensitivity_levels": [s.value for s in SensitivityLevel]
            })
        
        elif args.action == "test":
            # Test with sample data
            output_json({
                "success": True,
                "message": "Traffic parser initialized successfully",
                "patterns_loaded": {
                    "categories": len(CATEGORY_PATTERNS),
                    "sensitive_patterns": len(SENSITIVE_PATTERNS)
                }
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
