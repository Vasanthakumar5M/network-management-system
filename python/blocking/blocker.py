"""
Unified Blocking Engine.

Central blocking system that combines:
- Category-based blocking
- Domain/URL blocking
- Time-based schedules
- Keyword filtering
- Real-time blocking decisions
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .categories import (
    BlockCategory,
    CategoryDefinition,
    CATEGORY_DEFINITIONS,
    check_domain_category,
    check_url_keywords,
    get_category,
)
from .schedules import Schedule, ScheduleManager, ScheduleType


@dataclass
class BlockRule:
    """A single blocking rule."""
    id: str
    rule_type: str  # "domain", "url_pattern", "keyword", "category"
    value: str
    enabled: bool = True
    reason: str = ""
    created_at: Optional[str] = None


@dataclass
class BlockDecision:
    """Result of a blocking decision."""
    should_block: bool
    reason: str
    rule_id: Optional[str] = None
    rule_type: Optional[str] = None
    category: Optional[str] = None
    schedule_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BlockingEngine:
    """
    Unified blocking engine for all blocking decisions.
    
    Combines multiple blocking mechanisms:
    - Direct domain/URL blocks
    - Category-based blocks
    - Time-based schedules
    - Keyword-based content filtering
    """
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        schedule_file: Optional[str] = None
    ):
        """
        Initialize the blocking engine.
        
        Args:
            config_file: Path to blocklist configuration
            schedule_file: Path to schedule configuration
        """
        if config_file is None:
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config" / "blocklist.json"
        
        self.config_file = Path(config_file)
        self.schedule_manager = ScheduleManager(schedule_file)
        
        # Blocking rules
        self.blocked_domains: Set[str] = set()
        self.blocked_categories: Set[BlockCategory] = set()
        self.blocked_keywords: List[str] = []
        self.url_patterns: List[re.Pattern] = []
        self.custom_rules: Dict[str, BlockRule] = {}
        
        # Whitelist (override blocks)
        self.whitelisted_domains: Set[str] = set()
        
        # Callbacks for block events
        self._block_callbacks: List[Callable[[BlockDecision], None]] = []
        
        self._load_config()
    
    def _load_config(self):
        """Load blocking configuration from file."""
        if not self.config_file.exists():
            return
        
        try:
            data = json.loads(self.config_file.read_text())
            
            self.blocked_domains = set(data.get("blocked_domains", []))
            self.whitelisted_domains = set(data.get("whitelisted_domains", []))
            self.blocked_keywords = data.get("blocked_keywords", [])
            
            # Load blocked categories
            for cat_name in data.get("blocked_categories", []):
                try:
                    self.blocked_categories.add(get_category(cat_name))
                except ValueError:
                    pass
            
            # Load URL patterns
            for pattern in data.get("url_patterns", []):
                try:
                    self.url_patterns.append(re.compile(pattern, re.I))
                except re.error:
                    pass
            
            # Load custom rules
            for rule_data in data.get("custom_rules", []):
                rule = BlockRule(**rule_data)
                self.custom_rules[rule.id] = rule
        
        except Exception as e:
            print(json.dumps({"error": f"Failed to load blocklist: {e}"}))
    
    def _save_config(self):
        """Save blocking configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "blocked_domains": list(self.blocked_domains),
            "whitelisted_domains": list(self.whitelisted_domains),
            "blocked_categories": [c.value for c in self.blocked_categories],
            "blocked_keywords": self.blocked_keywords,
            "url_patterns": [p.pattern for p in self.url_patterns],
            "custom_rules": [
                {
                    "id": r.id,
                    "rule_type": r.rule_type,
                    "value": r.value,
                    "enabled": r.enabled,
                    "reason": r.reason,
                    "created_at": r.created_at
                }
                for r in self.custom_rules.values()
            ]
        }
        
        self.config_file.write_text(json.dumps(data, indent=2))
    
    def check(
        self,
        domain: str = "",
        url: str = "",
        content: str = "",
        check_schedule: bool = True
    ) -> BlockDecision:
        """
        Check if content should be blocked.
        
        Args:
            domain: Domain name to check
            url: Full URL to check
            content: Page content to check for keywords
            check_schedule: Whether to check time-based schedules
            
        Returns:
            BlockDecision with blocking determination
        """
        domain = domain.lower().strip()
        url = url.lower().strip()
        
        # Check whitelist first
        if self._is_whitelisted(domain):
            return BlockDecision(
                should_block=False,
                reason="Domain is whitelisted"
            )
        
        # Check direct domain blocks
        if self._check_domain_block(domain):
            decision = BlockDecision(
                should_block=True,
                reason=f"Domain blocked: {domain}",
                rule_type="domain"
            )
            self._notify_block(decision)
            return decision
        
        # Check URL patterns
        matched_pattern = self._check_url_patterns(url)
        if matched_pattern:
            decision = BlockDecision(
                should_block=True,
                reason=f"URL pattern matched: {matched_pattern}",
                rule_type="url_pattern"
            )
            self._notify_block(decision)
            return decision
        
        # Check categories
        categories = check_domain_category(domain)
        for category in categories:
            if category in self.blocked_categories:
                decision = BlockDecision(
                    should_block=True,
                    reason=f"Category blocked: {category.value}",
                    rule_type="category",
                    category=category.value
                )
                self._notify_block(decision)
                return decision
        
        # Check time-based schedules
        if check_schedule:
            for category in categories:
                should_block, schedule_id = self.schedule_manager.should_block(
                    domain=domain,
                    category=category.value
                )
                if should_block:
                    decision = BlockDecision(
                        should_block=True,
                        reason=f"Blocked by schedule: {schedule_id}",
                        rule_type="schedule",
                        schedule_id=schedule_id,
                        category=category.value
                    )
                    self._notify_block(decision)
                    return decision
            
            # Check schedule for domain without category
            should_block, schedule_id = self.schedule_manager.should_block(domain=domain)
            if should_block:
                decision = BlockDecision(
                    should_block=True,
                    reason=f"Blocked by schedule: {schedule_id}",
                    rule_type="schedule",
                    schedule_id=schedule_id
                )
                self._notify_block(decision)
                return decision
        
        # Check keywords in URL
        keyword_categories = check_url_keywords(url, content)
        for category in keyword_categories:
            if category in self.blocked_categories:
                decision = BlockDecision(
                    should_block=True,
                    reason=f"Keyword matched in {category.value}",
                    rule_type="keyword",
                    category=category.value
                )
                self._notify_block(decision)
                return decision
        
        # Check custom keywords
        matched_keyword = self._check_keywords(url, content)
        if matched_keyword:
            decision = BlockDecision(
                should_block=True,
                reason=f"Keyword blocked: {matched_keyword}",
                rule_type="keyword"
            )
            self._notify_block(decision)
            return decision
        
        # Check custom rules
        for rule in self.custom_rules.values():
            if not rule.enabled:
                continue
            
            if rule.rule_type == "domain" and domain == rule.value.lower():
                decision = BlockDecision(
                    should_block=True,
                    reason=rule.reason or f"Custom rule: {rule.value}",
                    rule_type="custom",
                    rule_id=rule.id
                )
                self._notify_block(decision)
                return decision
        
        return BlockDecision(
            should_block=False,
            reason="Allowed"
        )
    
    def _is_whitelisted(self, domain: str) -> bool:
        """Check if domain is whitelisted."""
        for whitelisted in self.whitelisted_domains:
            if domain == whitelisted or domain.endswith('.' + whitelisted):
                return True
        return False
    
    def _check_domain_block(self, domain: str) -> bool:
        """Check if domain is in block list."""
        for blocked in self.blocked_domains:
            if domain == blocked or domain.endswith('.' + blocked):
                return True
        return False
    
    def _check_url_patterns(self, url: str) -> Optional[str]:
        """Check URL against blocked patterns."""
        for pattern in self.url_patterns:
            if pattern.search(url):
                return pattern.pattern
        return None
    
    def _check_keywords(self, url: str, content: str) -> Optional[str]:
        """Check for blocked keywords."""
        combined = (url + " " + content).lower()
        
        for keyword in self.blocked_keywords:
            if keyword.lower() in combined:
                return keyword
        
        return None
    
    def _notify_block(self, decision: BlockDecision):
        """Notify callbacks about a block decision."""
        for callback in self._block_callbacks:
            try:
                callback(decision)
            except Exception:
                pass
    
    def add_callback(self, callback: Callable[[BlockDecision], None]):
        """Add a callback for block events."""
        self._block_callbacks.append(callback)
    
    # Domain management
    def block_domain(self, domain: str, reason: str = "") -> bool:
        """Add a domain to the block list."""
        domain = domain.lower().strip()
        self.blocked_domains.add(domain)
        self._save_config()
        return True
    
    def unblock_domain(self, domain: str) -> bool:
        """Remove a domain from the block list."""
        domain = domain.lower().strip()
        self.blocked_domains.discard(domain)
        self._save_config()
        return True
    
    def whitelist_domain(self, domain: str) -> bool:
        """Add a domain to the whitelist."""
        domain = domain.lower().strip()
        self.whitelisted_domains.add(domain)
        self._save_config()
        return True
    
    def remove_whitelist(self, domain: str) -> bool:
        """Remove a domain from the whitelist."""
        domain = domain.lower().strip()
        self.whitelisted_domains.discard(domain)
        self._save_config()
        return True
    
    # Category management
    def block_category(self, category: str) -> bool:
        """Block an entire category."""
        try:
            cat = get_category(category)
            self.blocked_categories.add(cat)
            self._save_config()
            return True
        except ValueError:
            return False
    
    def unblock_category(self, category: str) -> bool:
        """Unblock a category."""
        try:
            cat = get_category(category)
            self.blocked_categories.discard(cat)
            self._save_config()
            return True
        except ValueError:
            return False
    
    # Keyword management
    def add_keyword(self, keyword: str) -> bool:
        """Add a blocked keyword."""
        if keyword.lower() not in [k.lower() for k in self.blocked_keywords]:
            self.blocked_keywords.append(keyword)
            self._save_config()
            return True
        return False
    
    def remove_keyword(self, keyword: str) -> bool:
        """Remove a blocked keyword."""
        keyword_lower = keyword.lower()
        for i, k in enumerate(self.blocked_keywords):
            if k.lower() == keyword_lower:
                self.blocked_keywords.pop(i)
                self._save_config()
                return True
        return False
    
    # URL pattern management
    def add_url_pattern(self, pattern: str) -> bool:
        """Add a blocked URL pattern (regex)."""
        try:
            compiled = re.compile(pattern, re.I)
            self.url_patterns.append(compiled)
            self._save_config()
            return True
        except re.error:
            return False
    
    def remove_url_pattern(self, pattern: str) -> bool:
        """Remove a URL pattern."""
        for i, p in enumerate(self.url_patterns):
            if p.pattern == pattern:
                self.url_patterns.pop(i)
                self._save_config()
                return True
        return False
    
    # Custom rules
    def add_rule(self, rule: BlockRule) -> bool:
        """Add a custom blocking rule."""
        rule.created_at = datetime.now().isoformat()
        self.custom_rules[rule.id] = rule
        self._save_config()
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a custom rule."""
        if rule_id in self.custom_rules:
            del self.custom_rules[rule_id]
            self._save_config()
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self.custom_rules:
            self.custom_rules[rule_id].enabled = True
            self._save_config()
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self.custom_rules:
            self.custom_rules[rule_id].enabled = False
            self._save_config()
            return True
        return False
    
    # Status and reporting
    def get_status(self) -> dict:
        """Get current blocking configuration status."""
        return {
            "blocked_domains": len(self.blocked_domains),
            "whitelisted_domains": len(self.whitelisted_domains),
            "blocked_categories": [c.value for c in self.blocked_categories],
            "blocked_keywords": len(self.blocked_keywords),
            "url_patterns": len(self.url_patterns),
            "custom_rules": len(self.custom_rules),
            "active_schedules": len(self.schedule_manager.get_active_schedules())
        }
    
    def get_full_config(self) -> dict:
        """Get full blocking configuration."""
        return {
            "blocked_domains": list(self.blocked_domains),
            "whitelisted_domains": list(self.whitelisted_domains),
            "blocked_categories": [
                {
                    "id": c.value,
                    "name": CATEGORY_DEFINITIONS[c].name,
                    "severity": CATEGORY_DEFINITIONS[c].severity
                }
                for c in self.blocked_categories
            ],
            "blocked_keywords": self.blocked_keywords,
            "url_patterns": [p.pattern for p in self.url_patterns],
            "custom_rules": [
                {
                    "id": r.id,
                    "type": r.rule_type,
                    "value": r.value,
                    "enabled": r.enabled,
                    "reason": r.reason
                }
                for r in self.custom_rules.values()
            ],
            "schedules": [
                s.to_dict() for s in self.schedule_manager.list_schedules()
            ]
        }


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data, default=str), flush=True)


def main():
    """CLI entry point for blocking engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Website blocking engine")
    parser.add_argument("--action", choices=[
        "check", "block", "unblock", "whitelist", "status",
        "block-category", "unblock-category", "add-keyword",
        "remove-keyword", "config"
    ], default="status", help="Action to perform")
    parser.add_argument("--domain", help="Domain to check/block")
    parser.add_argument("--url", help="URL to check")
    parser.add_argument("--category", help="Category to block/unblock")
    parser.add_argument("--keyword", help="Keyword to add/remove")
    
    args = parser.parse_args()
    
    engine = BlockingEngine()
    
    try:
        if args.action == "check":
            if not args.domain and not args.url:
                output_json({
                    "success": False,
                    "error": "No domain or URL specified"
                })
                return
            
            decision = engine.check(
                domain=args.domain or "",
                url=args.url or ""
            )
            output_json({
                "success": True,
                "should_block": decision.should_block,
                "reason": decision.reason,
                "rule_type": decision.rule_type,
                "category": decision.category,
                "schedule_id": decision.schedule_id
            })
        
        elif args.action == "block":
            if not args.domain:
                output_json({"success": False, "error": "No domain specified"})
                return
            engine.block_domain(args.domain)
            output_json({"success": True, "action": "blocked", "domain": args.domain})
        
        elif args.action == "unblock":
            if not args.domain:
                output_json({"success": False, "error": "No domain specified"})
                return
            engine.unblock_domain(args.domain)
            output_json({"success": True, "action": "unblocked", "domain": args.domain})
        
        elif args.action == "whitelist":
            if not args.domain:
                output_json({"success": False, "error": "No domain specified"})
                return
            engine.whitelist_domain(args.domain)
            output_json({"success": True, "action": "whitelisted", "domain": args.domain})
        
        elif args.action == "block-category":
            if not args.category:
                output_json({"success": False, "error": "No category specified"})
                return
            success = engine.block_category(args.category)
            output_json({"success": success, "action": "block_category", "category": args.category})
        
        elif args.action == "unblock-category":
            if not args.category:
                output_json({"success": False, "error": "No category specified"})
                return
            success = engine.unblock_category(args.category)
            output_json({"success": success, "action": "unblock_category", "category": args.category})
        
        elif args.action == "add-keyword":
            if not args.keyword:
                output_json({"success": False, "error": "No keyword specified"})
                return
            engine.add_keyword(args.keyword)
            output_json({"success": True, "action": "add_keyword", "keyword": args.keyword})
        
        elif args.action == "remove-keyword":
            if not args.keyword:
                output_json({"success": False, "error": "No keyword specified"})
                return
            engine.remove_keyword(args.keyword)
            output_json({"success": True, "action": "remove_keyword", "keyword": args.keyword})
        
        elif args.action == "status":
            output_json({
                "success": True,
                "status": engine.get_status()
            })
        
        elif args.action == "config":
            output_json({
                "success": True,
                "config": engine.get_full_config()
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })


if __name__ == "__main__":
    main()
