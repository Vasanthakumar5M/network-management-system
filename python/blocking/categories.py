"""
Website/Content Blocking Categories.

Defines categories for blocking websites and content.
Includes predefined domain lists for common categories.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class BlockCategory(Enum):
    """Categories for content blocking."""
    ADULT = "adult"
    GAMBLING = "gambling"
    SOCIAL_MEDIA = "social_media"
    GAMING = "gaming"
    STREAMING = "streaming"
    DATING = "dating"
    VIOLENCE = "violence"
    DRUGS = "drugs"
    WEAPONS = "weapons"
    MALWARE = "malware"
    PHISHING = "phishing"
    ADVERTISING = "advertising"
    CRYPTOCURRENCY = "cryptocurrency"
    VPN_PROXY = "vpn_proxy"
    FILE_SHARING = "file_sharing"
    MESSAGING = "messaging"
    CUSTOM = "custom"


@dataclass
class CategoryDefinition:
    """Definition of a blocking category."""
    name: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    domains: Set[str] = field(default_factory=set)
    keywords: List[str] = field(default_factory=list)
    url_patterns: List[str] = field(default_factory=list)


# Predefined category definitions
CATEGORY_DEFINITIONS: Dict[BlockCategory, CategoryDefinition] = {
    BlockCategory.ADULT: CategoryDefinition(
        name="Adult Content",
        description="Pornographic and adult-only websites",
        severity="critical",
        domains={
            "pornhub.com", "xvideos.com", "xnxx.com", "xhamster.com",
            "redtube.com", "youporn.com", "tube8.com", "spankbang.com",
            "brazzers.com", "bangbros.com", "onlyfans.com", "chaturbate.com",
            "stripchat.com", "livejasmin.com", "cam4.com", "bongacams.com",
            "porntrex.com", "hqporner.com", "eporner.com", "tnaflix.com",
        },
        keywords=[
            "porn", "xxx", "adult", "nsfw", "nude", "naked",
            "sex video", "hardcore", "escort",
        ]
    ),
    
    BlockCategory.GAMBLING: CategoryDefinition(
        name="Gambling",
        description="Online gambling and betting websites",
        severity="high",
        domains={
            "bet365.com", "draftkings.com", "fanduel.com", "betmgm.com",
            "caesars.com", "pokerstars.com", "888poker.com", "partypoker.com",
            "bovada.lv", "stake.com", "betway.com", "unibet.com",
            "williamhill.com", "paddypower.com", "ladbrokes.com",
            "betfair.com", "1xbet.com", "pinnacle.com",
        },
        keywords=[
            "gambling", "casino", "poker", "betting", "sportsbook",
            "slot machine", "blackjack", "roulette",
        ]
    ),
    
    BlockCategory.SOCIAL_MEDIA: CategoryDefinition(
        name="Social Media",
        description="Social networking platforms",
        severity="low",
        domains={
            "facebook.com", "instagram.com", "twitter.com", "x.com",
            "tiktok.com", "snapchat.com", "linkedin.com", "pinterest.com",
            "tumblr.com", "reddit.com", "threads.net", "mastodon.social",
            "bsky.app", "truthsocial.com",
        },
        keywords=[]
    ),
    
    BlockCategory.GAMING: CategoryDefinition(
        name="Gaming",
        description="Online games and gaming platforms",
        severity="low",
        domains={
            "steampowered.com", "store.steampowered.com", "epicgames.com",
            "roblox.com", "minecraft.net", "fortnite.com", "ea.com",
            "blizzard.com", "ubisoft.com", "xbox.com", "playstation.com",
            "nintendo.com", "gog.com", "twitch.tv", "itch.io",
            "kongregate.com", "miniclip.com", "poki.com", "crazygames.com",
        },
        keywords=[]
    ),
    
    BlockCategory.STREAMING: CategoryDefinition(
        name="Streaming",
        description="Video and music streaming services",
        severity="low",
        domains={
            "youtube.com", "netflix.com", "hulu.com", "disneyplus.com",
            "hbomax.com", "max.com", "peacocktv.com", "paramountplus.com",
            "primevideo.com", "twitch.tv", "crunchyroll.com", "funimation.com",
            "spotify.com", "soundcloud.com", "pandora.com", "tidal.com",
            "deezer.com", "vimeo.com", "dailymotion.com",
        },
        keywords=[]
    ),
    
    BlockCategory.DATING: CategoryDefinition(
        name="Dating",
        description="Dating and relationship websites",
        severity="medium",
        domains={
            "tinder.com", "bumble.com", "hinge.co", "match.com",
            "okcupid.com", "plentyoffish.com", "eharmony.com", "zoosk.com",
            "grindr.com", "her.app", "coffee-meets-bagel.com",
        },
        keywords=["dating", "hookup", "singles", "meet singles"]
    ),
    
    BlockCategory.VIOLENCE: CategoryDefinition(
        name="Violence",
        description="Violent or disturbing content",
        severity="critical",
        domains={
            "liveleak.com", "bestgore.com", "theync.com", "crazyshit.com",
            "documentingreality.com",
        },
        keywords=["gore", "death video", "execution", "murder video"]
    ),
    
    BlockCategory.DRUGS: CategoryDefinition(
        name="Drugs",
        description="Drug-related content",
        severity="critical",
        domains={
            "erowid.org", "drugs-forum.com", "420magazine.com",
            "grasscity.com", "shroomery.org",
        },
        keywords=["buy drugs", "drug dealer", "cannabis seeds", "psychedelics"]
    ),
    
    BlockCategory.WEAPONS: CategoryDefinition(
        name="Weapons",
        description="Weapons sales and related content",
        severity="high",
        domains={
            "gunbroker.com", "budsgunshop.com", "palmettostatearmory.com",
            "cheaperthandirt.com", "midwayusa.com",
        },
        keywords=["buy guns", "firearms sale", "ammunition sale"]
    ),
    
    BlockCategory.VPN_PROXY: CategoryDefinition(
        name="VPN/Proxy Services",
        description="VPN and proxy services that could bypass monitoring",
        severity="high",
        domains={
            "nordvpn.com", "expressvpn.com", "surfshark.com", "cyberghostvpn.com",
            "privateinternetaccess.com", "protonvpn.com", "mullvad.net",
            "torproject.org", "hidemyass.com", "hotspotshield.com",
            "tunnelbear.com", "windscribe.com", "hide.me", "proxify.com",
            "kproxy.com", "proxysite.com", "whoer.net",
        },
        keywords=["vpn download", "anonymous proxy", "hide ip", "unblock sites"]
    ),
    
    BlockCategory.FILE_SHARING: CategoryDefinition(
        name="File Sharing",
        description="Torrents and file sharing platforms",
        severity="medium",
        domains={
            "thepiratebay.org", "1337x.to", "rarbg.to", "yts.mx",
            "kickasstorrents.to", "limetorrents.info", "torrentz2.eu",
            "nyaa.si", "rutracker.org", "mega.nz", "rapidgator.net",
            "mediafire.com", "zippyshare.com",
        },
        keywords=["torrent download", "free movies download", "pirated"]
    ),
    
    BlockCategory.MESSAGING: CategoryDefinition(
        name="Messaging Apps",
        description="Instant messaging and chat platforms",
        severity="low",
        domains={
            "whatsapp.com", "web.whatsapp.com", "telegram.org", "web.telegram.org",
            "signal.org", "discord.com", "slack.com", "messenger.com",
            "teams.microsoft.com", "zoom.us", "skype.com", "viber.com",
        },
        keywords=[]
    ),
    
    BlockCategory.ADVERTISING: CategoryDefinition(
        name="Advertising",
        description="Ad networks and tracking",
        severity="low",
        domains={
            "doubleclick.net", "googlesyndication.com", "googleadservices.com",
            "facebook.com/tr", "adnxs.com", "criteo.com", "taboola.com",
            "outbrain.com", "amazon-adsystem.com", "adsrvr.org",
        },
        keywords=[]
    ),
    
    BlockCategory.CRYPTOCURRENCY: CategoryDefinition(
        name="Cryptocurrency",
        description="Cryptocurrency trading and mining",
        severity="medium",
        domains={
            "coinbase.com", "binance.com", "kraken.com", "crypto.com",
            "robinhood.com", "ftx.com", "kucoin.com", "gemini.com",
            "bitfinex.com", "blockchain.com", "nicehash.com",
        },
        keywords=["buy bitcoin", "crypto trading", "mining pool"]
    ),
    
    BlockCategory.MALWARE: CategoryDefinition(
        name="Malware",
        description="Known malware and phishing domains",
        severity="critical",
        domains=set(),  # Populated dynamically from threat feeds
        keywords=[]
    ),
    
    BlockCategory.PHISHING: CategoryDefinition(
        name="Phishing",
        description="Phishing and scam websites",
        severity="critical",
        domains=set(),  # Populated dynamically from threat feeds
        keywords=[]
    ),
    
    BlockCategory.CUSTOM: CategoryDefinition(
        name="Custom",
        description="User-defined blocked sites",
        severity="medium",
        domains=set(),
        keywords=[]
    ),
}


def get_category(category: str) -> BlockCategory:
    """
    Get BlockCategory enum from string.
    
    Args:
        category: Category name string
        
    Returns:
        BlockCategory enum
        
    Raises:
        ValueError: If category is not found
    """
    try:
        return BlockCategory(category.lower())
    except ValueError:
        # Try matching by name
        for cat in BlockCategory:
            if cat.name.lower() == category.lower():
                return cat
        raise ValueError(f"Unknown category: {category}")


def get_category_definition(category: BlockCategory) -> CategoryDefinition:
    """Get the definition for a category."""
    return CATEGORY_DEFINITIONS.get(category, CATEGORY_DEFINITIONS[BlockCategory.CUSTOM])


def get_all_categories() -> List[dict]:
    """Get all categories with their definitions."""
    return [
        {
            "id": cat.value,
            "name": defn.name,
            "description": defn.description,
            "severity": defn.severity,
            "domain_count": len(defn.domains)
        }
        for cat, defn in CATEGORY_DEFINITIONS.items()
    ]


def check_domain_category(domain: str) -> List[BlockCategory]:
    """
    Check which categories a domain belongs to.
    
    Args:
        domain: Domain name to check
        
    Returns:
        List of matching categories
    """
    domain = domain.lower()
    matches = []
    
    for category, definition in CATEGORY_DEFINITIONS.items():
        for blocked_domain in definition.domains:
            if domain == blocked_domain or domain.endswith('.' + blocked_domain):
                matches.append(category)
                break
    
    return matches


def check_url_keywords(url: str, content: str = "") -> List[BlockCategory]:
    """
    Check URL and content for blocked keywords.
    
    Args:
        url: URL to check
        content: Optional page content to check
        
    Returns:
        List of matching categories
    """
    combined = (url + " " + content).lower()
    matches = []
    
    for category, definition in CATEGORY_DEFINITIONS.items():
        for keyword in definition.keywords:
            if keyword.lower() in combined:
                matches.append(category)
                break
    
    return matches
