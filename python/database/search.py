"""
Full-Text Search for Traffic Data.

Provides advanced search capabilities:
- Multi-field search
- Phrase matching
- Boolean operators
- Fuzzy matching
- Search history
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .db_manager import DatabaseManager
from .models import TrafficEntry


@dataclass
class SearchQuery:
    """A parsed search query."""
    original: str
    terms: List[str] = field(default_factory=list)
    phrases: List[str] = field(default_factory=list)  # Quoted phrases
    excluded: List[str] = field(default_factory=list)  # -term
    required: List[str] = field(default_factory=list)  # +term
    filters: Dict[str, str] = field(default_factory=dict)  # field:value


@dataclass
class SearchResult:
    """A search result with relevance info."""
    entry: TrafficEntry
    score: float
    highlights: Dict[str, str] = field(default_factory=dict)


class SearchEngine:
    """
    Full-text search engine for network traffic.
    
    Supports advanced query syntax and result ranking.
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """
        Initialize the search engine.
        
        Args:
            db: Database manager instance
        """
        self.db = db or DatabaseManager()
        
        # Search history
        self._search_history: List[dict] = []
        self._max_history = 100
    
    def search(
        self,
        query: str,
        device_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        include_body: bool = True
    ) -> List[SearchResult]:
        """
        Search traffic data.
        
        Args:
            query: Search query (supports operators)
            device_id: Filter by device
            since: Only entries after this time
            limit: Maximum results
            include_body: Include request/response body in search
            
        Returns:
            List of SearchResult objects
        """
        # Parse query
        parsed = self._parse_query(query)
        
        # Build FTS query
        fts_query = self._build_fts_query(parsed)
        
        # Execute search
        if fts_query:
            # Use FTS for primary search
            entries = self.db.search(fts_query, limit=limit * 2)  # Get more for filtering
        else:
            # Fall back to regular query
            entries = self.db.get_traffic(
                device_id=device_id,
                since=since,
                limit=limit * 2
            )
        
        # Apply filters and scoring
        results = []
        for entry in entries:
            # Apply device filter
            if device_id and entry.device_id != device_id:
                continue
            
            # Apply time filter
            if since and datetime.fromisoformat(entry.timestamp) < since:
                continue
            
            # Apply field filters
            if not self._matches_filters(entry, parsed.filters):
                continue
            
            # Apply exclusions
            if self._has_excluded_terms(entry, parsed.excluded, include_body):
                continue
            
            # Check required terms
            if not self._has_required_terms(entry, parsed.required, include_body):
                continue
            
            # Calculate score
            score = self._calculate_score(entry, parsed, include_body)
            
            # Generate highlights
            highlights = self._generate_highlights(entry, parsed, include_body)
            
            results.append(SearchResult(
                entry=entry,
                score=score,
                highlights=highlights
            ))
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Apply limit
        results = results[:limit]
        
        # Record in history
        self._add_to_history(query, len(results))
        
        return results
    
    def _parse_query(self, query: str) -> SearchQuery:
        """Parse a search query into components."""
        parsed = SearchQuery(original=query)
        
        # Extract quoted phrases
        phrase_pattern = r'"([^"]+)"'
        for match in re.finditer(phrase_pattern, query):
            parsed.phrases.append(match.group(1))
        
        # Remove phrases from query for further parsing
        remaining = re.sub(phrase_pattern, '', query)
        
        # Extract field filters (field:value)
        filter_pattern = r'(\w+):(\S+)'
        for match in re.finditer(filter_pattern, remaining):
            field, value = match.groups()
            parsed.filters[field.lower()] = value
        
        remaining = re.sub(filter_pattern, '', remaining)
        
        # Extract excluded terms (-term)
        exclude_pattern = r'-(\S+)'
        for match in re.finditer(exclude_pattern, remaining):
            parsed.excluded.append(match.group(1))
        
        remaining = re.sub(exclude_pattern, '', remaining)
        
        # Extract required terms (+term)
        require_pattern = r'\+(\S+)'
        for match in re.finditer(require_pattern, remaining):
            parsed.required.append(match.group(1))
        
        remaining = re.sub(require_pattern, '', remaining)
        
        # Remaining are regular terms
        parsed.terms = [t.strip() for t in remaining.split() if t.strip()]
        
        return parsed
    
    def _build_fts_query(self, parsed: SearchQuery) -> str:
        """Build FTS5 query string."""
        parts = []
        
        # Add phrases
        for phrase in parsed.phrases:
            parts.append(f'"{phrase}"')
        
        # Add terms with OR
        if parsed.terms:
            terms_str = " OR ".join(parsed.terms)
            if len(parsed.terms) > 1:
                parts.append(f"({terms_str})")
            else:
                parts.append(terms_str)
        
        # Add required terms
        for term in parsed.required:
            parts.append(term)
        
        if not parts:
            return ""
        
        return " AND ".join(parts) if len(parts) > 1 else parts[0]
    
    def _matches_filters(self, entry: TrafficEntry, filters: Dict[str, str]) -> bool:
        """Check if entry matches field filters."""
        for field, value in filters.items():
            if field == "host" and value.lower() not in entry.host.lower():
                return False
            elif field == "method" and entry.method.upper() != value.upper():
                return False
            elif field == "status" and str(entry.status_code) != value:
                return False
            elif field == "category" and entry.category != value:
                return False
            elif field == "device" and entry.device_id != value:
                return False
        
        return True
    
    def _has_excluded_terms(
        self,
        entry: TrafficEntry,
        excluded: List[str],
        include_body: bool
    ) -> bool:
        """Check if entry contains excluded terms."""
        if not excluded:
            return False
        
        searchable = self._get_searchable_text(entry, include_body)
        searchable_lower = searchable.lower()
        
        for term in excluded:
            if term.lower() in searchable_lower:
                return True
        
        return False
    
    def _has_required_terms(
        self,
        entry: TrafficEntry,
        required: List[str],
        include_body: bool
    ) -> bool:
        """Check if entry contains all required terms."""
        if not required:
            return True
        
        searchable = self._get_searchable_text(entry, include_body)
        searchable_lower = searchable.lower()
        
        for term in required:
            if term.lower() not in searchable_lower:
                return False
        
        return True
    
    def _get_searchable_text(self, entry: TrafficEntry, include_body: bool) -> str:
        """Get all searchable text from entry."""
        parts = [
            entry.url,
            entry.host,
            entry.path,
            entry.method,
            entry.category or "",
        ]
        
        if include_body:
            if entry.request_body:
                parts.append(entry.request_body)
            if entry.response_body:
                parts.append(entry.response_body)
        
        return " ".join(parts)
    
    def _calculate_score(
        self,
        entry: TrafficEntry,
        parsed: SearchQuery,
        include_body: bool
    ) -> float:
        """Calculate relevance score for an entry."""
        score = 0.0
        
        searchable = self._get_searchable_text(entry, include_body).lower()
        
        # Score for terms in URL/host (higher weight)
        url_lower = entry.url.lower()
        host_lower = entry.host.lower()
        
        all_search_terms = parsed.terms + parsed.phrases + parsed.required
        
        for term in all_search_terms:
            term_lower = term.lower()
            
            # URL match
            if term_lower in url_lower:
                score += 3.0
            
            # Host match
            if term_lower in host_lower:
                score += 2.0
            
            # General match
            count = searchable.count(term_lower)
            score += min(count * 0.5, 5.0)  # Cap contribution
        
        # Boost for exact phrase matches
        for phrase in parsed.phrases:
            if phrase.lower() in searchable:
                score += 5.0
        
        # Boost for recent entries
        try:
            entry_time = datetime.fromisoformat(entry.timestamp)
            hours_ago = (datetime.now() - entry_time).total_seconds() / 3600
            if hours_ago < 24:
                score += 1.0
            elif hours_ago < 168:  # Week
                score += 0.5
        except Exception:
            pass
        
        return score
    
    def _generate_highlights(
        self,
        entry: TrafficEntry,
        parsed: SearchQuery,
        include_body: bool
    ) -> Dict[str, str]:
        """Generate highlighted snippets for matches."""
        highlights = {}
        
        all_terms = parsed.terms + parsed.phrases + parsed.required
        
        if not all_terms:
            return highlights
        
        # Highlight in URL
        highlights["url"] = self._highlight_text(entry.url, all_terms, max_len=200)
        
        # Highlight in host
        highlights["host"] = self._highlight_text(entry.host, all_terms)
        
        # Highlight in body if included
        if include_body and entry.request_body:
            snippet = self._extract_snippet(entry.request_body, all_terms)
            if snippet:
                highlights["request_body"] = self._highlight_text(snippet, all_terms)
        
        if include_body and entry.response_body:
            snippet = self._extract_snippet(entry.response_body, all_terms)
            if snippet:
                highlights["response_body"] = self._highlight_text(snippet, all_terms)
        
        return highlights
    
    def _highlight_text(
        self,
        text: str,
        terms: List[str],
        max_len: int = 300
    ) -> str:
        """Add highlight markers around matched terms."""
        if len(text) > max_len:
            text = text[:max_len] + "..."
        
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            text = pattern.sub(f"**{term}**", text)
        
        return text
    
    def _extract_snippet(
        self,
        text: str,
        terms: List[str],
        context_chars: int = 100
    ) -> Optional[str]:
        """Extract a snippet around the first match."""
        text_lower = text.lower()
        
        for term in terms:
            idx = text_lower.find(term.lower())
            if idx != -1:
                start = max(0, idx - context_chars)
                end = min(len(text), idx + len(term) + context_chars)
                
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                
                return snippet
        
        return None
    
    def _add_to_history(self, query: str, result_count: int):
        """Add search to history."""
        self._search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_count": result_count
        })
        
        # Trim history
        if len(self._search_history) > self._max_history:
            self._search_history = self._search_history[-self._max_history:]
    
    def get_search_history(self, limit: int = 20) -> List[dict]:
        """Get recent search history."""
        return list(reversed(self._search_history[-limit:]))
    
    def get_suggestions(self, partial: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on history and common hosts."""
        suggestions = set()
        partial_lower = partial.lower()
        
        # From history
        for item in reversed(self._search_history):
            if partial_lower in item["query"].lower():
                suggestions.add(item["query"])
                if len(suggestions) >= limit:
                    break
        
        # From database (common hosts)
        if len(suggestions) < limit:
            try:
                from .db_manager import DatabaseManager
                with self.db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT host FROM traffic
                        WHERE host LIKE ?
                        ORDER BY host
                        LIMIT ?
                    """, (f"%{partial}%", limit - len(suggestions)))
                    
                    for row in cursor.fetchall():
                        suggestions.add(row[0])
            except Exception:
                pass
        
        return list(suggestions)[:limit]


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for search."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Search network traffic")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--device", help="Filter by device ID")
    parser.add_argument("--since", help="Only entries after this time (ISO format)")
    parser.add_argument("--limit", type=int, default=100, help="Max results")
    parser.add_argument("--history", action="store_true", help="Show search history")
    parser.add_argument("--suggest", help="Get suggestions for partial query")
    
    args = parser.parse_args()
    
    engine = SearchEngine()
    
    try:
        if args.history:
            output_json({
                "success": True,
                "history": engine.get_search_history()
            })
        
        elif args.suggest:
            suggestions = engine.get_suggestions(args.suggest)
            output_json({
                "success": True,
                "suggestions": suggestions
            })
        
        elif args.query:
            since = None
            if args.since:
                since = datetime.fromisoformat(args.since)
            
            results = engine.search(
                query=args.query,
                device_id=args.device,
                since=since,
                limit=args.limit
            )
            
            output_json({
                "success": True,
                "count": len(results),
                "results": [
                    {
                        "score": r.score,
                        "highlights": r.highlights,
                        "entry": r.entry.to_dict()
                    }
                    for r in results
                ]
            })
        
        else:
            output_json({
                "success": False,
                "error": "No query specified",
                "help": "Usage: search.py 'query' [--device ID] [--since TIME] [--limit N]"
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
