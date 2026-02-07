"""
Keyword Detection and Matching.

Provides advanced keyword matching for content alerts:
- Exact match
- Fuzzy matching
- Regex patterns
- Context-aware matching
- Severity levels
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class MatchType(Enum):
    """Type of keyword match."""
    EXACT = "exact"  # Exact word match
    CONTAINS = "contains"  # Substring match
    REGEX = "regex"  # Regular expression
    FUZZY = "fuzzy"  # Fuzzy matching (typos, leetspeak)


class AlertSeverity(Enum):
    """Severity level of alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Categories for keyword alerts."""
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    BULLYING = "bullying"
    DRUGS = "drugs"
    SEXUAL = "sexual"
    PREDATOR = "predator"
    PERSONAL_INFO = "personal_info"
    PROFANITY = "profanity"
    CUSTOM = "custom"


@dataclass
class Keyword:
    """A keyword to monitor for."""
    id: str
    word: str
    match_type: MatchType = MatchType.CONTAINS
    category: AlertCategory = AlertCategory.CUSTOM
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    case_sensitive: bool = False
    context_words: List[str] = field(default_factory=list)  # Words that increase severity
    exclude_words: List[str] = field(default_factory=list)  # Words that prevent match
    description: str = ""
    
    _compiled_pattern: Optional[re.Pattern] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Compile regex pattern if needed."""
        if self.match_type == MatchType.REGEX:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._compiled_pattern = re.compile(self.word, flags)
        elif self.match_type == MatchType.EXACT:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._compiled_pattern = re.compile(rf'\b{re.escape(self.word)}\b', flags)
    
    def matches(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if this keyword matches in the text.
        
        Args:
            text: Text to search
            
        Returns:
            Tuple of (matched, matched_text)
        """
        if not self.enabled:
            return False, None
        
        # Check exclusions first
        for exclude in self.exclude_words:
            if exclude.lower() in text.lower():
                return False, None
        
        if self.match_type == MatchType.EXACT:
            match = self._compiled_pattern.search(text)
            if match:
                return True, match.group()
        
        elif self.match_type == MatchType.CONTAINS:
            search_text = text if self.case_sensitive else text.lower()
            search_word = self.word if self.case_sensitive else self.word.lower()
            if search_word in search_text:
                return True, self.word
        
        elif self.match_type == MatchType.REGEX:
            match = self._compiled_pattern.search(text)
            if match:
                return True, match.group()
        
        elif self.match_type == MatchType.FUZZY:
            matched = self._fuzzy_match(text)
            if matched:
                return True, matched
        
        return False, None
    
    def _fuzzy_match(self, text: str) -> Optional[str]:
        """
        Fuzzy match for leetspeak and common misspellings.
        
        Returns matched text or None.
        """
        # Common leetspeak substitutions
        leetspeak_map = {
            'a': '[a@4]',
            'e': '[e3]',
            'i': '[i1!]',
            'o': '[o0]',
            's': '[s$5]',
            't': '[t7+]',
            'l': '[l1]',
            'b': '[b8]',
        }
        
        # Build fuzzy pattern
        pattern_parts = []
        word = self.word.lower()
        
        for char in word:
            if char in leetspeak_map:
                pattern_parts.append(leetspeak_map[char])
            else:
                pattern_parts.append(re.escape(char))
        
        pattern = ''.join(pattern_parts)
        
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        except re.error:
            pass
        
        return None
    
    def get_severity_with_context(self, text: str) -> AlertSeverity:
        """
        Get severity, potentially elevated by context words.
        
        Args:
            text: Text containing the match
            
        Returns:
            Severity (may be elevated from base)
        """
        if not self.context_words:
            return self.severity
        
        text_lower = text.lower()
        for context_word in self.context_words:
            if context_word.lower() in text_lower:
                # Elevate severity
                if self.severity == AlertSeverity.LOW:
                    return AlertSeverity.MEDIUM
                elif self.severity == AlertSeverity.MEDIUM:
                    return AlertSeverity.HIGH
                elif self.severity == AlertSeverity.HIGH:
                    return AlertSeverity.CRITICAL
        
        return self.severity
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "word": self.word,
            "match_type": self.match_type.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "case_sensitive": self.case_sensitive,
            "context_words": self.context_words,
            "exclude_words": self.exclude_words,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Keyword":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            word=data["word"],
            match_type=MatchType(data.get("match_type", "contains")),
            category=AlertCategory(data.get("category", "custom")),
            severity=AlertSeverity(data.get("severity", "medium")),
            enabled=data.get("enabled", True),
            case_sensitive=data.get("case_sensitive", False),
            context_words=data.get("context_words", []),
            exclude_words=data.get("exclude_words", []),
            description=data.get("description", "")
        )


@dataclass
class KeywordMatch:
    """A keyword match result."""
    keyword: Keyword
    matched_text: str
    context: str  # Surrounding text
    location: str  # Where it was found (url, body, etc.)
    severity: AlertSeverity
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# Predefined keyword sets for common concerns
PREDEFINED_KEYWORDS = {
    AlertCategory.SELF_HARM: [
        Keyword(
            id="sh_suicide",
            word="suicide",
            category=AlertCategory.SELF_HARM,
            severity=AlertSeverity.CRITICAL,
            context_words=["method", "how to", "want to", "thinking about"],
            exclude_words=["prevention", "hotline", "awareness"]
        ),
        Keyword(
            id="sh_cutting",
            word="cutting myself",
            category=AlertCategory.SELF_HARM,
            severity=AlertSeverity.CRITICAL,
            match_type=MatchType.FUZZY
        ),
        Keyword(
            id="sh_end_life",
            word="end my life",
            category=AlertCategory.SELF_HARM,
            severity=AlertSeverity.CRITICAL,
            match_type=MatchType.FUZZY
        ),
        Keyword(
            id="sh_kill_myself",
            word="kill myself",
            category=AlertCategory.SELF_HARM,
            severity=AlertSeverity.CRITICAL,
            match_type=MatchType.FUZZY
        ),
        Keyword(
            id="sh_self_harm",
            word="self harm",
            category=AlertCategory.SELF_HARM,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.FUZZY
        ),
    ],
    
    AlertCategory.BULLYING: [
        Keyword(
            id="bully_kys",
            word="kys",
            category=AlertCategory.BULLYING,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.EXACT,
            description="Kill yourself (acronym)"
        ),
        Keyword(
            id="bully_kill_yourself",
            word="kill yourself",
            category=AlertCategory.BULLYING,
            severity=AlertSeverity.CRITICAL,
            match_type=MatchType.FUZZY
        ),
        Keyword(
            id="bully_hate_you",
            word="everyone hates you",
            category=AlertCategory.BULLYING,
            severity=AlertSeverity.HIGH
        ),
        Keyword(
            id="bully_die",
            word="go die",
            category=AlertCategory.BULLYING,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.FUZZY
        ),
    ],
    
    AlertCategory.PREDATOR: [
        Keyword(
            id="pred_age",
            word=r"how old are you",
            category=AlertCategory.PREDATOR,
            severity=AlertSeverity.MEDIUM,
            context_words=["pic", "photo", "meet", "address", "alone"]
        ),
        Keyword(
            id="pred_meet",
            word="let's meet",
            category=AlertCategory.PREDATOR,
            severity=AlertSeverity.HIGH,
            context_words=["alone", "secret", "don't tell"]
        ),
        Keyword(
            id="pred_secret",
            word="our secret",
            category=AlertCategory.PREDATOR,
            severity=AlertSeverity.HIGH,
            context_words=["parents", "mom", "dad", "don't tell"]
        ),
        Keyword(
            id="pred_send_pic",
            word=r"send (me )?(a )?pic(ture)?",
            category=AlertCategory.PREDATOR,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.REGEX,
            context_words=["body", "private", "naked", "underwear"]
        ),
    ],
    
    AlertCategory.DRUGS: [
        Keyword(
            id="drug_buy",
            word="buy weed",
            category=AlertCategory.DRUGS,
            severity=AlertSeverity.HIGH
        ),
        Keyword(
            id="drug_dealer",
            word="drug dealer",
            category=AlertCategory.DRUGS,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.FUZZY
        ),
        Keyword(
            id="drug_molly",
            word="molly",
            category=AlertCategory.DRUGS,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.EXACT,
            context_words=["roll", "party", "pills", "high"]
        ),
        Keyword(
            id="drug_xanax",
            word="xanax",
            category=AlertCategory.DRUGS,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.FUZZY,
            context_words=["bars", "buy", "get some"]
        ),
    ],
    
    AlertCategory.PERSONAL_INFO: [
        Keyword(
            id="pii_address",
            word=r"\d+\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln)",
            category=AlertCategory.PERSONAL_INFO,
            severity=AlertSeverity.HIGH,
            match_type=MatchType.REGEX,
            description="Street address pattern"
        ),
        Keyword(
            id="pii_phone",
            word=r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            category=AlertCategory.PERSONAL_INFO,
            severity=AlertSeverity.MEDIUM,
            match_type=MatchType.REGEX,
            description="Phone number"
        ),
        Keyword(
            id="pii_ssn",
            word=r"\b\d{3}-\d{2}-\d{4}\b",
            category=AlertCategory.PERSONAL_INFO,
            severity=AlertSeverity.CRITICAL,
            match_type=MatchType.REGEX,
            description="Social Security Number"
        ),
    ],
}


class KeywordMatcher:
    """
    Keyword matching engine.
    
    Efficiently matches multiple keywords against text content.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the keyword matcher.
        
        Args:
            config_file: Path to keyword configuration file
        """
        if config_file is None:
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config" / "keywords.json"
        
        self.config_file = Path(config_file)
        self.keywords: Dict[str, Keyword] = {}
        
        self._load_keywords()
    
    def _load_keywords(self):
        """Load keywords from configuration file."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                for kw_data in data.get("keywords", []):
                    keyword = Keyword.from_dict(kw_data)
                    self.keywords[keyword.id] = keyword
            except Exception as e:
                print(json.dumps({"error": f"Failed to load keywords: {e}"}))
    
    def _save_keywords(self):
        """Save keywords to configuration file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "keywords": [kw.to_dict() for kw in self.keywords.values()]
        }
        self.config_file.write_text(json.dumps(data, indent=2))
    
    def add_keyword(self, keyword: Keyword) -> bool:
        """Add a keyword to monitor."""
        self.keywords[keyword.id] = keyword
        self._save_keywords()
        return True
    
    def remove_keyword(self, keyword_id: str) -> bool:
        """Remove a keyword."""
        if keyword_id in self.keywords:
            del self.keywords[keyword_id]
            self._save_keywords()
            return True
        return False
    
    def enable_keyword(self, keyword_id: str) -> bool:
        """Enable a keyword."""
        if keyword_id in self.keywords:
            self.keywords[keyword_id].enabled = True
            self._save_keywords()
            return True
        return False
    
    def disable_keyword(self, keyword_id: str) -> bool:
        """Disable a keyword."""
        if keyword_id in self.keywords:
            self.keywords[keyword_id].enabled = False
            self._save_keywords()
            return True
        return False
    
    def load_predefined(self, category: AlertCategory) -> int:
        """
        Load predefined keywords for a category.
        
        Returns number of keywords loaded.
        """
        if category not in PREDEFINED_KEYWORDS:
            return 0
        
        count = 0
        for keyword in PREDEFINED_KEYWORDS[category]:
            if keyword.id not in self.keywords:
                self.keywords[keyword.id] = keyword
                count += 1
        
        self._save_keywords()
        return count
    
    def load_all_predefined(self) -> int:
        """Load all predefined keywords."""
        count = 0
        for category in AlertCategory:
            count += self.load_predefined(category)
        return count
    
    def match(
        self,
        text: str,
        location: str = "content",
        context_chars: int = 50
    ) -> List[KeywordMatch]:
        """
        Match text against all keywords.
        
        Args:
            text: Text to search
            location: Where this text is from (url, body, etc.)
            context_chars: Characters of context to include
            
        Returns:
            List of KeywordMatch objects
        """
        matches = []
        
        for keyword in self.keywords.values():
            matched, matched_text = keyword.matches(text)
            
            if matched and matched_text:
                # Extract context
                context = self._extract_context(text, matched_text, context_chars)
                
                # Get severity with context
                severity = keyword.get_severity_with_context(context)
                
                matches.append(KeywordMatch(
                    keyword=keyword,
                    matched_text=matched_text,
                    context=context,
                    location=location,
                    severity=severity
                ))
        
        return matches
    
    def _extract_context(
        self,
        text: str,
        matched: str,
        context_chars: int
    ) -> str:
        """Extract surrounding context for a match."""
        idx = text.lower().find(matched.lower())
        if idx == -1:
            return ""
        
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(matched) + context_chars)
        
        context = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def get_keywords_by_category(
        self,
        category: AlertCategory
    ) -> List[Keyword]:
        """Get all keywords in a category."""
        return [
            kw for kw in self.keywords.values()
            if kw.category == category
        ]
    
    def get_keywords_by_severity(
        self,
        min_severity: AlertSeverity
    ) -> List[Keyword]:
        """Get keywords at or above a severity level."""
        severity_order = [
            AlertSeverity.LOW,
            AlertSeverity.MEDIUM,
            AlertSeverity.HIGH,
            AlertSeverity.CRITICAL
        ]
        min_idx = severity_order.index(min_severity)
        
        return [
            kw for kw in self.keywords.values()
            if severity_order.index(kw.severity) >= min_idx
        ]
    
    def list_keywords(self) -> List[dict]:
        """List all keywords."""
        return [kw.to_dict() for kw in self.keywords.values()]


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for keyword matching."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Keyword matching engine")
    parser.add_argument("--action", choices=[
        "match", "list", "add", "remove", "load-predefined", "categories"
    ], default="list", help="Action to perform")
    parser.add_argument("--text", help="Text to match")
    parser.add_argument("--word", help="Keyword word")
    parser.add_argument("--id", help="Keyword ID")
    parser.add_argument("--category", help="Keyword category")
    parser.add_argument("--severity", help="Keyword severity")
    
    args = parser.parse_args()
    
    matcher = KeywordMatcher()
    
    try:
        if args.action == "match":
            if not args.text:
                output_json({"success": False, "error": "No text specified"})
                return
            
            matches = matcher.match(args.text)
            output_json({
                "success": True,
                "matches": [
                    {
                        "keyword_id": m.keyword.id,
                        "word": m.keyword.word,
                        "matched_text": m.matched_text,
                        "context": m.context,
                        "category": m.keyword.category.value,
                        "severity": m.severity.value
                    }
                    for m in matches
                ]
            })
        
        elif args.action == "list":
            output_json({
                "success": True,
                "keywords": matcher.list_keywords()
            })
        
        elif args.action == "add":
            if not args.word or not args.id:
                output_json({"success": False, "error": "Word and ID required"})
                return
            
            keyword = Keyword(
                id=args.id,
                word=args.word,
                category=AlertCategory(args.category) if args.category else AlertCategory.CUSTOM,
                severity=AlertSeverity(args.severity) if args.severity else AlertSeverity.MEDIUM
            )
            matcher.add_keyword(keyword)
            output_json({"success": True, "action": "added", "keyword": keyword.to_dict()})
        
        elif args.action == "remove":
            if not args.id:
                output_json({"success": False, "error": "Keyword ID required"})
                return
            
            success = matcher.remove_keyword(args.id)
            output_json({"success": success, "action": "removed", "id": args.id})
        
        elif args.action == "load-predefined":
            if args.category:
                cat = AlertCategory(args.category)
                count = matcher.load_predefined(cat)
            else:
                count = matcher.load_all_predefined()
            
            output_json({"success": True, "keywords_loaded": count})
        
        elif args.action == "categories":
            output_json({
                "success": True,
                "categories": [c.value for c in AlertCategory],
                "severities": [s.value for s in AlertSeverity]
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
