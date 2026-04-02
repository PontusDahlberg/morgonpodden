#!/usr/bin/env python3
"""
Komplett podcast-generator för MMM Senaste Nytt
Med musik-integration och riktig väderdata
"""

import os
import sys
import json
import logging
import shutil
import requests
import re
import html
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Lägg till modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from music_mixer import MusicMixer
from episode_history import EpisodeHistory

# Import Gemini TTS för förbättrad dialog
try:
    from gemini_tts_dialog import GeminiTTSDialogGenerator
    GEMINI_TTS_AVAILABLE = True
    GEMINI_TTS_IMPORT_ERROR: Optional[str] = None
except ImportError as e:
    GEMINI_TTS_AVAILABLE = False
    GEMINI_TTS_IMPORT_ERROR = str(e)

# Import KRITISK faktakontroll-agent
try:
    from news_fact_checker import NewsFactChecker
    FACT_CHECKER_AVAILABLE = True
except ImportError as e:
    FACT_CHECKER_AVAILABLE = False

# Import backup faktakontroll (fungerar utan AI)
try:
    from basic_fact_checker import BasicFactChecker, quick_fact_check
    BASIC_FACT_CHECKER_AVAILABLE = True
except ImportError as e:
    BASIC_FACT_CHECKER_AVAILABLE = False

# Import självkorrigerande faktakontroll
try:
    from self_correcting_fact_checker import SelfCorrectingFactChecker, auto_correct_podcast_content
    SELF_CORRECTING_AVAILABLE = True
except ImportError as e:
    SELF_CORRECTING_AVAILABLE = False

# Ladda miljövariabler
load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('podcast_generation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SWEDISH_WEEKDAYS = {
    'Monday': 'måndag',
    'Tuesday': 'tisdag',
    'Wednesday': 'onsdag',
    'Thursday': 'torsdag',
    'Friday': 'fredag',
    'Saturday': 'lördag',
    'Sunday': 'söndag'
}

SWEDISH_MONTHS = {
    1: 'januari',
    2: 'februari',
    3: 'mars',
    4: 'april',
    5: 'maj',
    6: 'juni',
    7: 'juli',
    8: 'augusti',
    9: 'september',
    10: 'oktober',
    11: 'november',
    12: 'december'
}

# Stopwords för enkel titel-fingerprinting (för att undvika dagliga upprepningar)
_TITLE_STOPWORDS = {
    'och', 'eller', 'men', 'att', 'som', 'det', 'den', 'detta', 'dessa', 'en', 'ett', 'i', 'på', 'av', 'till',
    'för', 'med', 'utan', 'över', 'under', 'efter', 'före', 'om', 'när', 'där', 'här', 'från', 'mot',
    'säger', 'sa', 'uppger', 'enligt', 'nya', 'ny', 'nu', 'idag', 'igår', 'imorgon',
    'the', 'a', 'an', 'and', 'or', 'but', 'to', 'of', 'in', 'on', 'for', 'with', 'from', 'by', 'as', 'at',
}

_PROMOTIONAL_TITLE_PATTERNS = (
    r'\bsave up to\b',
    r'\bdays? left\b',
    r'\bbefore prices rise\b',
    r'\bexhibit table\b',
    r'\bpass\b',
    r'\bticket(?:s)?\b',
    r'\bbiljett(?:er)?\b',
    r'\bdeal(?:s)?\b',
    r'\bsale\b',
    r'\brabatt\b',
    r'\berbjudande\b',
    r'\bshopping\b',
    r'\breview\b',
    r'\bgallery\b',
    r'\bbest\b',
)

_ARTICLE_HARD_CUT_MARKERS = (
    'är du redan prenumerant',
    'logga in för att fortsätta läsa',
    'läs dn +',
    'ditt erbjudande',
    'det här ingår',
    'share this article',
    'copy/paste the article video embed link below',
    'go to accessibility shortcuts',
    'advertisement',
    'in partnership with',
    'follow live coverage',
    'follow the latest updates',
    'also on ',
    'så arbetar vi',
    'läs mer om hur vi arbetar',
    'relaterat',
    'copied',
    'javascript är avstängt',
    'javascript måste vara påslaget',
    'läs mer om webbläsarstöd',
    'någonting är fel',
    'läs vidare',
    'starta din prenumeration',
    'redan prenumerant',
    'logga in och läs vidare',
    'full tillgång till allt digitalt material',
    'på din profilsida',
    'kontakta vår kundtjänst',
    'premium',
)

_ARTICLE_DROP_PATTERNS = (
    r'https?://\S+',
    r'\bwww\.\S+',
    r'\bartikelns ursprungsadress\b',
    r'\ben utskrift från\b',
    r'\bshare\b',
    r'\bsave\b',
    r'\bfacebook\b',
    r'\btwitter\b',
    r'\bwhatsapp\b',
    r'\breddit\b',
    r'\blinkedin\b',
    r'\btelegram\b',
    r'\bbluesky\b',
    r'\bthreads\b',
    r'\blogga in\b',
    r'\bprenumerant\b',
    r'\bgratiskonto\b',
    r'\bsubscription\b',
    r'\bsubscribe\b',
    r'\bord\.?\s*pris\b',
    r'\b\d+\s*kr(?:/mån|/man|/månad)?\b',
    r'\b\d+\s*mån(?:ader)?\s*för\s*\d+\s*kr\b',
    r'\b0\s*kr\b',
    r'\bannons\b',
    r'\badvertisement\b',
    r'\bsponsor(?:ed)?\b',
    r'\berbjudande\b',
    r'\brabatt\b',
    r'\bkampanj\b',
    r'\bexhibit table\b',
    r'\bbefore prices rise\b',
    r'\bsave up to\b',
    r'\bfoto\s*:',
    r'\bbild(?:text)?\s*:',
    r'\bfotograf\s*:',
    r'\barkivbild\b',
    r'\bgenrebild\b',
    r'\bjavascript är avstängt\b',
    r'\bjavascript måste vara påslaget\b',
    r'\bwebbläsarstöd\b',
    r'\bpremium\b',
    r'\bprenumerera\b',
    r'\bredan prenumerant\b',
)

_ENGLISH_FUNCTION_WORDS = {
    'the', 'and', 'that', 'with', 'from', 'this', 'these', 'those', 'into', 'about', 'after', 'before',
    'while', 'when', 'where', 'which', 'their', 'there', 'would', 'could', 'should', 'have', 'has',
    'had', 'said', 'says', 'will', 'just', 'more', 'most', 'than', 'also', 'over', 'under', 'through',
}

_SWEDISH_FUNCTION_WORDS = {
    'och', 'det', 'att', 'som', 'för', 'med', 'den', 'detta', 'där', 'här', 'inte', 'också', 'från',
    'genom', 'efter', 'innan', 'skulle', 'kan', 'kunde', 'har', 'hade', 'säger', 'sa', 'fler', 'mest',
}

_SPOKEN_URL_PATTERNS = (
    re.compile(r'https?://\S+', re.IGNORECASE),
    re.compile(r'\bwww\.\S+', re.IGNORECASE),
    re.compile(
        r'(?<!@)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+'
        r'(?:se|com|net|org|io|ai|news|tv|dev|co|nu|eu|gov|edu)\b(?:/[^\s]*)?',
        re.IGNORECASE,
    ),
)

# Diagnostics
DIAGNOSTICS_FILE = os.getenv('MMM_DIAGNOSTICS_FILE', 'diagnostics.jsonl')
_CURRENT_RUN_ID: Optional[str] = None
_LAST_GEMINI_ERROR: Optional[str] = None


def set_run_id(run_id: str) -> None:
    global _CURRENT_RUN_ID
    _CURRENT_RUN_ID = run_id


def log_diagnostic(event: str, payload: Dict) -> None:
    """Skriv en strukturerad rad till diagnostics.jsonl utan att spamma huvudloggen."""
    try:
        entry = {
            'ts': datetime.now().isoformat(timespec='seconds'),
            'run_id': _CURRENT_RUN_ID,
            'event': event,
            **payload,
        }
        with open(DIAGNOSTICS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Diagnostik får aldrig stoppa körningen
        pass


def _write_run_diagnostics_extract(
    *,
    run_id: str,
    diagnostics_file: str = DIAGNOSTICS_FILE,
    output_dir: str = 'episodes',
    max_lines: int = 2000,
) -> Optional[str]:
    """Write a filtered diagnostics.jsonl containing only entries for this run_id."""
    try:
        if not run_id:
            return None
        if not os.path.exists(diagnostics_file):
            return None
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"diagnostics_{run_id}.jsonl")

        kept = 0
        with open(diagnostics_file, 'r', encoding='utf-8') as fin, open(out_path, 'w', encoding='utf-8') as fout:
            for line in fin:
                if not line.strip():
                    continue
                # Fast path: don't parse JSON unless likely match
                if f'"run_id": "{run_id}"' not in line and f'"run_id":"{run_id}"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get('run_id') != run_id:
                    continue
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                if kept >= max(1, int(max_lines)):
                    break

        if kept <= 0:
            try:
                os.remove(out_path)
            except Exception:
                pass
        return out_path
    except Exception:
        return None


def cleanup_generated_dialogue(text: str) -> str:
    """Städa bort kända oönskade meta-fraser innan publicering/TTS."""
    if not text:
        return text

    updated = text
    updated = _strip_spoken_urls(updated)
    news_labels_removed = len(re.findall(r'\bNyhet\s+\d+\s*[:.]?', updated, flags=re.IGNORECASE))
    updated = re.sub(r'\bNyhet\s+\d+\s*[:.]?\s*', '', updated, flags=re.IGNORECASE)

    replacements = {
        "Okej, vad är kärnan här – och vad vet vi faktiskt?": "Vad är det viktigaste att ta med sig här?",
        "Okej, vad är kärnan här - och vad vet vi faktiskt?": "Vad är det viktigaste att ta med sig här?",
        "Vad vet vi faktiskt här?": "Vad är det viktigaste här?",
        "Det här väcker ju frågan om konsekvenser och nästa steg. Finns det något som fortfarande är oklart?": "Det intressanta nu är vilka följder det här kan få framåt.",
        "Ja – och det är viktigt att säga högt: om källtexten inte ger exakta siffror eller tidsplaner så låtsas vi inte. Vi följer upp när mer information finns.": "Vi återkommer när fler bekräftade detaljer finns på plats.",
        "Ja - och det är viktigt att säga högt: om källtexten inte ger exakta siffror eller tidsplaner så låtsas vi inte. Vi följer upp när mer information finns.": "Vi återkommer när fler bekräftade detaljer finns på plats.",
        "Vi har inte så mycket underliggande information här ännu.": "Det finns fortfarande flera detaljer som väntar på besked.",
        "Det finns inte så mycket underliggande information här ännu.": "Det finns fortfarande flera detaljer som väntar på besked.",
        "Och som alltid: vi länkar till originalkällan så att du kan läsa mer själv och bedöma detaljerna.": "Källan finns länkad i avsnittsbeskrivningen för den som vill läsa vidare.",
    }

    replaced_phrases = 0
    removed_english_quotes = 0
    removed_english_lines = 0

    def _strip_long_english_quote(match: re.Match[str]) -> str:
        nonlocal removed_english_quotes

        quoted = (match.group(2) or '').strip()
        if _is_probably_english_span(quoted, min_word_count=8):
            removed_english_quotes += 1
            return ''
        return match.group(0)

    for old, new in replacements.items():
        hits = len(re.findall(re.escape(old), updated, flags=re.IGNORECASE))
        if hits:
            updated = re.sub(re.escape(old), new, updated, flags=re.IGNORECASE)
            replaced_phrases += hits

    updated = re.sub(r'(["“])([^"”\n]{40,})(["”])', _strip_long_english_quote, updated)
    updated = re.sub(
        r'(?:,?\s*)\b(?:sade|skrev|beskrev|kallade det|formulerade det som)\b\s*$',
        '',
        updated,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    meta_line_patterns = (
        r'\bunderliggande information\b',
        r'\bkälltext(?:en)?\b',
        r'\bvad vet vi faktiskt\b',
        r'\bvad är oklart\b',
        r'\bvi (?:kan|ska|bör) inte hitta på\b',
        r'\bvi låtsas inte\b',
        r'\bai-röster\b',
        r'\bvi kan göra fel\b',
        r'\bdubbelkolla gärna\b',
        r'\bavsnittsinformationen\b',
        r'\bkällan finns länkad\b',
        r'https?://',
        r'\bwww\.',
        r'\bord\.?\s*pris\b',
        r'\b\d+\s*kr(?:/mån|/man|/månad)?\b',
        r'\brabatt\b',
        r'\berbjudande\b',
        r'\bkampanj\b',
        r'\bannons\b',
        r'\badvertisement\b',
        r'\bsponsor(?:ed)?\b',
        r'\bfoto\s*:',
        r'\bbild(?:text)?\s*:',
        r'\bfotograf\s*:',
        r'\barkivbild\b',
        r'\bgenrebild\b',
        r'\bjavascript är avstängt\b',
        r'\bwebbläsarstöd\b',
    )
    removed_meta_lines = 0
    cleaned_lines = []
    for line in updated.splitlines():
        stripped = line.strip()
        if stripped and re.match(r'^(Lisa|Pelle):', stripped):
            lowered = stripped.lower()
            spoken_text = stripped.split(':', 1)[1].strip() if ':' in stripped else stripped
            if any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in meta_line_patterns):
                removed_meta_lines += 1
                continue
            if _is_probably_english_span(spoken_text, min_word_count=14):
                removed_english_lines += 1
                continue
        cleaned_lines.append(line)

    updated = '\n'.join(cleaned_lines)

    updated = re.sub(r'\n{3,}', '\n\n', updated).strip()

    if updated != text:
        logger.info(
            "[SCRIPT] Städade manus före TTS/publicering (tog bort %s nyhetsetiketter, ersatte %s meta-fraser, tog bort %s meta-rader, strök %s långa engelska citat, tog bort %s engelsktunga repliker)",
            news_labels_removed,
            replaced_phrases,
            removed_meta_lines,
            removed_english_quotes,
            removed_english_lines,
        )
        log_diagnostic('script_cleanup_applied', {
            'news_labels_removed': news_labels_removed,
            'replaced_phrases': replaced_phrases,
            'removed_meta_lines': removed_meta_lines,
            'removed_english_quotes': removed_english_quotes,
            'removed_english_lines': removed_english_lines,
        })

    return updated


def _write_log_tail(
    *,
    run_id: str,
    log_path: str = 'podcast_generation.log',
    output_dir: str = 'episodes',
    max_lines: int = 600,
) -> Optional[str]:
    """Write a short tail of the main log file for email attachment."""
    try:
        if not run_id:
            return None
        if not os.path.exists(log_path):
            return None
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"log_tail_{run_id}.txt")

        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        tail = lines[-max(50, int(max_lines)):] if lines else []
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write("".join(tail))
        return out_path
    except Exception:
        return None


def _set_last_gemini_error(message: Optional[str]) -> None:
    global _LAST_GEMINI_ERROR
    _LAST_GEMINI_ERROR = message


def _canonicalize_url(url: str) -> str:
    """Skapa stabil URL-nyckel som inte påverkas av tracking-parametrar."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

        parsed = urlparse(url.strip())
        query_pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                       if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid'}]
        cleaned = parsed._replace(query=urlencode(query_pairs, doseq=True), fragment="")

        # Normalisera bort trailing slash
        normalized = urlunparse(cleaned).rstrip('/')
        return normalized
    except Exception:
        return url.strip().rstrip('/')


def _title_fingerprint(title: str) -> str:
    """Skapa en grov "fingerprint" av en titel för dedupe mellan dagar."""
    if not title:
        return ""
    text = title.lower()
    text = re.sub(r'[^\w\såäöÅÄÖ-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = [t for t in text.split(' ') if len(t) >= 4 and t not in _TITLE_STOPWORDS and not t.isdigit()]
    if not tokens:
        return ""
    # Sortera och ta en begränsad mängd token för stabilitet
    tokens = sorted(set(tokens))
    return ' '.join(tokens[:12])


def _is_follow_up_article(title: str, content: str) -> bool:
    """Heuristik: uppföljningar är okej, men daglig repetition ska bort."""
    text = f"{title} {content}".lower()
    # Viktigt: håll detta strikt. Många rubriker innehåller ord som "nu"/"senaste" utan att vara
    # en verklig uppföljning, vilket annars gör att samma nyheter slinker igenom dag efter dag.
    follow_up_markers = [
        'uppfölj', 'fortsatt', 'ytterligare', 'nya uppgifter', 'uppdater',
        'rättegång', 'dom', 'dömd', 'överklag', 'åtal', 'åtalad', 'fäll', 'frias', 'utred',
        'follow-up', 'update', 'new details'
    ]
    return any(m in text for m in follow_up_markers)


def _format_swedish_date(dt: datetime) -> str:
    month_swedish = SWEDISH_MONTHS.get(dt.month, dt.strftime('%B').lower())
    return f"{dt.day} {month_swedish} {dt.year}"


def _load_recent_episode_articles(within_days: int, today: datetime) -> List[Dict[str, Any]]:
    """Load recent episode_articles_*.json entries.

    Returns a flat list of dicts:
    { 'date': datetime, 'source': str, 'title': str, 'link': str, 'content': str }
    """
    try:
        import glob

        cutoff_date = (today - timedelta(days=within_days)).date()
        results: List[Dict[str, Any]] = []
        for article_file in glob.glob('episode_articles_*.json'):
            try:
                # episode_articles_20251014_190405.json
                date_part = article_file.split('_')[2]
                file_date = datetime.strptime(date_part, '%Y%m%d').date()
                if file_date < cutoff_date:
                    continue
            except Exception:
                continue

            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    prev_articles = json.load(f) or []
                for a in prev_articles:
                    results.append({
                        'date': datetime.combine(file_date, datetime.min.time()),
                        'source': (a.get('source') or '').strip(),
                        'title': (a.get('title') or '').strip(),
                        'link': (a.get('link') or '').strip(),
                        'content': (a.get('content') or '').strip(),
                    })
            except Exception as e:
                logger.warning(f"[HISTORY] Kunde inte läsa {article_file}: {e}")
        return results
    except Exception:
        return []


def _build_previous_coverage_hints(
    current_articles: List[Dict[str, Any]],
    recent_episode_articles: List[Dict[str, Any]],
    today: datetime,
    max_hints: int = 3,
    min_overlap_tokens: int = 4,
    min_jaccard: float = 0.50,
    informative_max_freq: int = 2,
    min_anchor_token_len: int = 7,
    debug: bool = False,
    debug_max_samples: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Find conservative "topic" matches between today's curated articles and recent episode archives.

    Goal: enable safe callbacks like "senast vi var inne på ämnet".
    We only emit hints when we have high confidence (rare anchor token overlap + similarity).
    """
    debug_info: Dict[str, Any] = {
        'current_considered': 0,
        'recent_items': 0,
        'evaluated_pairs': 0,
        'reasons': {
            'no_title_tokens': 0,
            'no_anchor_tokens': 0,
            'identical_url': 0,
            'identical_title_fp': 0,
            'prev_already_used': 0,
            'prev_is_today_or_future': 0,
            'overlap_below_min': 0,
            'no_anchor_overlap': 0,
            'similarity_below_min': 0,
            'no_candidate': 0,
            'hint_emitted': 0,
        },
        'samples': [],
    }

    if not current_articles or not recent_episode_articles:
        return [], debug_info

    def _token_set_from_title(title: str) -> set:
        fp = _title_fingerprint(title)
        return set(fp.split(' ')) if fp else set()

    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return (inter / union) if union else 0.0

    # Precompute token sets for recent items + token frequency for "rarity".
    recent: List[Tuple[Dict[str, Any], set]] = []
    token_freq: Dict[str, int] = {}
    for r in recent_episode_articles:
        tset = _token_set_from_title(r.get('title', ''))
        if not tset:
            continue
        recent.append((r, tset))
        for t in tset:
            token_freq[t] = token_freq.get(t, 0) + 1

    debug_info['recent_items'] = len(recent)

    hints: List[Dict[str, Any]] = []
    used_prev_keys: set = set()

    for cur in (current_articles or [])[:10]:
        debug_info['current_considered'] += 1
        cur_title = (cur.get('title') or '').strip()
        cur_link = (cur.get('link') or '').strip()
        cur_source = (cur.get('source') or '').strip()

        cur_tokens = _token_set_from_title(cur_title)
        if not cur_tokens:
            debug_info['reasons']['no_title_tokens'] += 1
            continue

        cur_url_key = _canonicalize_url(cur_link)
        cur_fp = _title_fingerprint(cur_title)

        # Identify "anchor" tokens that are rare in the recent archive.
        cur_informative = {
            t for t in cur_tokens
            if token_freq.get(t, 0) <= informative_max_freq and len(t) >= min_anchor_token_len
        }
        if not cur_informative:
            debug_info['reasons']['no_anchor_tokens'] += 1
            continue

        best = None
        best_score = 0.0
        best_date = None
        best_overlap_info = 0

        # For diagnostics: what's the closest we got, even if not passing thresholds.
        best_any_score = 0.0
        best_any_prev_source = ""
        best_any_prev_date = None

        for prev, prev_tokens in recent:
            prev_title = (prev.get('title') or '').strip()
            prev_link = (prev.get('link') or '').strip()

            debug_info['evaluated_pairs'] += 1

            # Avoid identical items (dedupe already tries, but keep this strict)
            if cur_url_key and cur_url_key == _canonicalize_url(prev_link):
                debug_info['reasons']['identical_url'] += 1
                continue
            if cur_fp and cur_fp == _title_fingerprint(prev_title):
                debug_info['reasons']['identical_title_fp'] += 1
                continue

            # Avoid mentioning the same historical item multiple times
            prev_key = _canonicalize_url(prev_link) or _title_fingerprint(prev_title)
            if prev_key and prev_key in used_prev_keys:
                debug_info['reasons']['prev_already_used'] += 1
                continue

            # Avoid "today" as "previous"
            try:
                prev_date = prev.get('date')
                if isinstance(prev_date, datetime) and prev_date.date() >= today.date():
                    debug_info['reasons']['prev_is_today_or_future'] += 1
                    continue
            except Exception:
                pass

            overlap_total = len(cur_tokens & prev_tokens)
            if overlap_total < min_overlap_tokens:
                debug_info['reasons']['overlap_below_min'] += 1
                continue

            overlap_info = len(cur_informative & prev_tokens)
            if overlap_info < 1:
                debug_info['reasons']['no_anchor_overlap'] += 1
                continue

            score = _jaccard(cur_tokens, prev_tokens)

            if score > best_any_score:
                best_any_score = score
                best_any_prev_source = (prev.get('source') or '').strip()
                prev_dt_any = prev.get('date')
                if isinstance(prev_dt_any, datetime):
                    best_any_prev_date = prev_dt_any.date()
                else:
                    best_any_prev_date = None

            if score < min_jaccard:
                debug_info['reasons']['similarity_below_min'] += 1
                continue

            # Prefer the most recent prior mention ("förra gången").
            prev_dt = prev.get('date')
            prev_date_key = None
            if isinstance(prev_dt, datetime):
                prev_date_key = prev_dt.date()

            if best is None:
                best = prev
                best_score = score
                best_date = prev_date_key
                best_overlap_info = overlap_info
            else:
                # Pick newer; break ties by stronger informative overlap, then higher similarity.
                if prev_date_key and (best_date is None or prev_date_key > best_date):
                    best = prev
                    best_score = score
                    best_date = prev_date_key
                    best_overlap_info = overlap_info
                elif prev_date_key == best_date:
                    if overlap_info > best_overlap_info:
                        best = prev
                        best_score = score
                        best_overlap_info = overlap_info
                    elif overlap_info == best_overlap_info and score > best_score:
                        best = prev
                        best_score = score

        if best and best_score >= min_jaccard:
            prev_date = best.get('date')
            if isinstance(prev_date, datetime):
                prev_date_str = _format_swedish_date(prev_date)
            else:
                prev_date_str = str(prev_date) if prev_date else "(okänt datum)"

            prev_title = (best.get('title') or '').strip()
            prev_source = (best.get('source') or '').strip()
            prev_link = (best.get('link') or '').strip()

            hints.append({
                'current_source': cur_source,
                'current_title': cur_title,
                'current_link': cur_link,
                'topic_tokens': ' '.join(sorted(list(cur_informative))[:3]),
                'previous_date': prev_date_str,
                'previous_source': prev_source,
                'previous_title': prev_title,
                'previous_link': prev_link,
                'score': round(best_score, 3),
            })

            prev_key = _canonicalize_url(prev_link) or _title_fingerprint(prev_title)
            if prev_key:
                used_prev_keys.add(prev_key)

            debug_info['reasons']['hint_emitted'] += 1
        else:
            debug_info['reasons']['no_candidate'] += 1
            if debug and len(debug_info.get('samples', [])) < max(0, int(debug_max_samples)):
                debug_info['samples'].append({
                    'current_source': cur_source,
                    'current_title': _truncate_text(cur_title, 120),
                    'anchor_tokens': ' '.join(sorted(list(cur_informative))[:3]),
                    'best_any_score': round(best_any_score, 3),
                    'best_any_prev_source': best_any_prev_source,
                    'best_any_prev_date': str(best_any_prev_date) if best_any_prev_date else None,
                })

        if len(hints) >= max_hints:
            break

    # Sort by recency first (best effort), then score.
    def _hint_sort_key(h: Dict[str, Any]) -> tuple:
        try:
            # previous_date is a Swedish string; sorting by score is fine for secondary
            return (h.get('score', 0.0),)
        except Exception:
            return (0.0,)

    hints.sort(key=_hint_sort_key, reverse=True)
    return hints[:max_hints], debug_info


def extract_referenced_articles(podcast_content: str, candidate_articles: List[Dict], max_results: int = 8) -> List[Dict]:
    """Försök avgöra vilka av kandidat-artiklarna som faktiskt refereras i manuset.

    Vi matchar på stabila titel-token (inte exakta strängar) för att undvika att RSS listar källor
    som aldrig nämndes i avsnittet.
    """
    if not podcast_content or not candidate_articles:
        return []

    haystack = podcast_content.lower()
    haystack = re.sub(r'[^\w\såäöÅÄÖ-]', ' ', haystack)
    haystack = re.sub(r'\s+', ' ', haystack)

    scored: List[tuple[int, Dict]] = []
    for article in candidate_articles:
        title = (article.get('title') or '').strip()
        source = (article.get('source') or '').strip()
        fp = _title_fingerprint(title)
        if not fp:
            continue

        tokens = fp.split(' ')
        token_hits = sum(1 for t in tokens if t in haystack)
        source_hit = 1 if source and source.lower() in haystack else 0
        score = token_hits + source_hit

        # Kräver minst en rimlig träff för att räknas
        if score >= 2 or (score >= 1 and any(len(t) >= 10 and t in haystack for t in tokens)):
            scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:max_results]]

def get_swedish_weather() -> str:
    """Hämta aktuell väderdata från SMHI för svenska landskap"""
    try:
        # Importera SMHI-modulen
        from smhi_weather import SMHIWeatherService
        
        service = SMHIWeatherService()
        weather_summary = service.get_swedish_weather_summary()
        
        logger.info(f"[WEATHER] {weather_summary}")
        return weather_summary
            
    except Exception as e:
        logger.error(f"[WEATHER] Fel vid SMHI väder-hämtning: {e}")
        # Fallback till wttr.in om SMHI misslyckas
        try:
            logger.info("[WEATHER] Använder wttr.in som backup")
            # Svenska landskap med representativa städer - alla 4 regioner
            regions = [
                ("Götaland", "Goteborg"),
                ("Svealand", "Stockholm"),  
                ("Södra Norrland", "Sundsvall"),
                ("Norra Norrland", "Kiruna")
            ]
            
            weather_data = []
            for region_name, api_name in regions:
                try:
                    url = f"https://wttr.in/{api_name}?format=%C+%t"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        weather_info = response.text.strip()
                        weather_data.append(f"{region_name}: {weather_info}")
                        
                except Exception:
                    continue
            
            if weather_data:
                weather_text = f"Vädret idag: {', '.join(weather_data)}"  # Visa alla regioner
                return weather_text
            else:
                return "Vädret idag: Varierande väderförhållanden över Sverige"
                
        except Exception:
            return "Vädret idag: Varierande väderförhållanden över Sverige"

def load_config() -> Dict:
    """Ladda konfiguration från sources.json"""
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("[ERROR] sources.json hittades inte")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Fel i sources.json: {e}")
        return {}

def _normalize_gemini_model(model: str) -> str:
    raw = (model or "").strip()
    if not raw:
        return "gemini-2.5-flash"
    return raw.split('/', 1)[1] if '/' in raw else raw


def _get_gemini_direct_response(messages: List[Dict], model: str) -> str:
    """Skicka förfrågan direkt till Gemini API (utan OpenRouter)."""
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY saknas i miljövariabler")

    gemini_model = _normalize_gemini_model(model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent"

    max_tokens_env = os.getenv('MMM_MAX_TOKENS', '').strip()
    try:
        max_tokens = int(max_tokens_env) if max_tokens_env else 2200
    except ValueError:
        max_tokens = 2200

    system_lines: List[str] = []
    contents: List[Dict[str, Any]] = []
    for msg in messages or []:
        role = (msg.get('role') or 'user').strip().lower()
        text = (msg.get('content') or '').strip()
        if not text:
            continue
        if role == 'system':
            system_lines.append(text)
            continue
        gemini_role = 'model' if role == 'assistant' else 'user'
        contents.append({
            'role': gemini_role,
            'parts': [{'text': text}],
        })

    if not contents:
        raise ValueError("Inga giltiga messages för Gemini-anrop")

    payload: Dict[str, Any] = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': max_tokens,
        }
    }
    if system_lines:
        payload['systemInstruction'] = {
            'parts': [{'text': "\n\n".join(system_lines)}]
        }

    try:
        response = requests.post(
            url,
            params={'key': api_key},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        result = response.json()

        candidates = result.get('candidates') or []
        if not candidates:
            raise RuntimeError("Gemini svar saknar candidates")
        parts = (candidates[0].get('content') or {}).get('parts') or []
        text = ''.join((p.get('text') or '') for p in parts).strip()
        if not text:
            raise RuntimeError("Gemini svar saknar text")
        return text
    except requests.RequestException as e:
        logger.error(f"[ERROR] Gemini API error: {e}")
        raise


def get_openrouter_response(messages: List[Dict], model: str = "google/gemini-2.5-flash", provider: str = "openrouter") -> str:
    """Skicka förfrågan till vald LLM-provider (gemini/openrouter/openai)."""
    provider = (provider or 'openrouter').strip().lower()

    if provider == 'gemini':
        return _get_gemini_direct_response(messages, model)

    if provider == 'openai':
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY saknas i miljövariabler")
        try:
            from openai import OpenAI

            default_openai_model = model.split('/', 1)[1] if '/' in model else model
            openai_model = os.getenv('OPENAI_MODEL', '').strip() or default_openai_model
            max_tokens_env = os.getenv('MMM_MAX_TOKENS', '').strip()
            try:
                max_tokens = int(max_tokens_env) if max_tokens_env else 2200
            except ValueError:
                max_tokens = 2200

            client = OpenAI(api_key=openai_api_key)
            resp = client.chat.completions.create(
                model=openai_model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"[ERROR] OpenAI API error: {type(e).__name__}: {e}")
            raise

    # Default: OpenRouter (med fallback till OpenAI om OpenRouter-nyckel saknas)
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/PontusDahlberg",
            "X-Title": "MMM Podcast Generator",
            "Content-Type": "application/json"
        }

        max_tokens_env = os.getenv('MMM_MAX_TOKENS', '').strip()
        try:
            max_tokens = int(max_tokens_env) if max_tokens_env else 2200
        except ValueError:
            max_tokens = 2200

        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=90)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.RequestException as e:
            logger.error(f"[ERROR] OpenRouter API error: {e}")
            raise

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        try:
            from openai import OpenAI

            # OpenRouter-modellnamn kan vara t.ex. "openai/gpt-4o-mini".
            # För OpenAI vill vi oftast ha "gpt-4o-mini".
            default_openai_model = model.split('/', 1)[1] if '/' in model else model
            openai_model = os.getenv('OPENAI_MODEL', '').strip() or default_openai_model
            max_tokens_env = os.getenv('MMM_MAX_TOKENS', '').strip()
            try:
                max_tokens = int(max_tokens_env) if max_tokens_env else 2200
            except ValueError:
                max_tokens = 2200

            client = OpenAI(api_key=openai_api_key)
            resp = client.chat.completions.create(
                model=openai_model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"[ERROR] OpenAI API error (fallback): {type(e).__name__}: {e}")
            raise

    raise ValueError("OPENROUTER_API_KEY saknas i miljövariabler (och OPENAI_API_KEY saknas också)")


def _count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\S+", text))


def _is_probably_english_span(text: str, *, min_word_count: int = 10) -> bool:
    if not text:
        return False

    words = re.findall(r"[A-Za-zÅÄÖåäö][A-Za-zÅÄÖåäö'’-]*", text.lower())
    if len(words) < min_word_count:
        return False

    english_hits = sum(1 for word in words if word in _ENGLISH_FUNCTION_WORDS)
    swedish_hits = sum(1 for word in words if word in _SWEDISH_FUNCTION_WORDS)
    ascii_ratio = sum(1 for ch in text if ch.isascii()) / max(1, len(text))

    return english_hits >= 3 and english_hits > swedish_hits and ascii_ratio >= 0.85


def _parse_weekday_value(value: Any) -> Optional[int]:
    """Parse weekday to Python weekday int (Mon=0..Sun=6)."""
    if value is None:
        return None
    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        return None
    if isinstance(value, str):
        raw = value.strip().lower()
        if not raw:
            return None
        if raw.isdigit():
            try:
                n = int(raw)
            except ValueError:
                return None
            return n if 0 <= n <= 6 else None

        # English + Swedish (common variants)
        mapping = {
            'monday': 0, 'mon': 0, 'måndag': 0,
            'tuesday': 1, 'tue': 1, 'tisdag': 1,
            'wednesday': 2, 'wed': 2, 'onsdag': 2,
            'thursday': 3, 'thu': 3, 'torsdag': 3,
            'friday': 4, 'fri': 4, 'fredag': 4,
            'saturday': 5, 'sat': 5, 'lördag': 5, 'lordag': 5,
            'sunday': 6, 'sun': 6, 'söndag': 6, 'sondag': 6,
        }
        return mapping.get(raw)

    return None


def _aftertalk_config_for_today(today: datetime, config: Dict) -> Dict[str, Any]:
    """Return effective aftertalk config if it should run today, else {}."""
    podcast_settings = (config or {}).get('podcastSettings') or {}
    aftertalk = (podcast_settings.get('aftertalk') or {}) if isinstance(podcast_settings, dict) else {}

    enabled = bool(aftertalk.get('enabled', False))
    if not enabled:
        return {}

    weekdays_raw = aftertalk.get('weekdays', [])
    weekdays: List[int] = []
    if isinstance(weekdays_raw, (list, tuple)):
        for w in weekdays_raw:
            parsed = _parse_weekday_value(w)
            if parsed is not None:
                weekdays.append(parsed)

    # Default: Saturdays (5)
    if not weekdays:
        weekdays = [5]

    if today.weekday() not in set(weekdays):
        return {}

    # Clamp seconds to sane bounds
    def _as_int(v: Any, default: int) -> int:
        try:
            return int(v)
        except Exception:
            return default

    target_s = _as_int(aftertalk.get('target_seconds'), 120)
    min_s = _as_int(aftertalk.get('min_seconds'), max(45, target_s - 30))
    max_s = _as_int(aftertalk.get('max_seconds'), target_s + 30)
    min_s = max(30, min_s)
    max_s = max(min_s, max_s)

    style = (aftertalk.get('style') or '').strip()
    return {
        'enabled': True,
        'weekdays': weekdays,
        'target_seconds': target_s,
        'min_seconds': min_s,
        'max_seconds': max_s,
        'style': style,
    }


def _split_outro_block(script_text: str) -> tuple[str, str]:
    """Best-effort split of (body, outro) so padding can be inserted before outro."""
    if not script_text:
        return "", ""
    lines = script_text.splitlines()
    if not lines:
        return script_text, ""

    outro_markers = (
        'tack för att du lyssnade',
        'tack för idag',
        'det var dagens',
        'vi är ai',
        'ai-röster',
        'dubbelkolla',
        'avsnittsinformationen',
        'människa maskin miljö',
        'mmm senaste nytt',
    )

    last_match = None
    for i in range(len(lines) - 1, -1, -1):
        s = lines[i].strip().lower()
        if not s:
            continue
        if s.startswith('lisa:') or s.startswith('pelle:'):
            if any(m in s for m in outro_markers):
                last_match = i
                break

    if last_match is None:
        return script_text, ""

    # Expand backwards a bit to capture the rest of the outro block.
    start = last_match
    max_back = 10
    while start > 0 and max_back > 0:
        prev = lines[start - 1].strip().lower()
        if not prev:
            start -= 1
            max_back -= 1
            continue
        if prev.startswith('lisa:') or prev.startswith('pelle:'):
            # Stop if it looks like we are back into dense main content.
            if len(prev) > 260 and not any(m in prev for m in outro_markers):
                break
            start -= 1
            max_back -= 1
            continue
        break

    body = "\n".join(lines[:start]).rstrip()
    outro = "\n".join(lines[start:]).lstrip()
    return body, outro


def _fallback_collect_articles_from_scraped(max_per_source: int = 5, max_total: int = 30) -> List[Dict]:
    """Fallback: plocka ett litet urval artiklar direkt från scraped_content.json."""
    available_articles: List[Dict] = []
    try:
        with open('scraped_content.json', 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
            for source_group in scraped_data:
                source_name = source_group.get('source', 'Okänd')
                items = source_group.get('items', [])
                for item in items[:max_per_source]:
                    if item.get('link') and item.get('title'):
                        available_articles.append({
                            'source': source_name,
                            'title': item['title'][:100],
                            'content': _article_text(item, 1600),
                            'link': item['link']
                        })
                    if len(available_articles) >= max_total:
                        return available_articles
    except Exception as e:
        logger.error(f"❌ Fallback-filtrering misslyckades: {e}")
    return available_articles


def _truncate_text(text: str, max_chars: int) -> str:
    if not text:
        return ""
    clean = " ".join(str(text).split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max(0, max_chars - 1)].rstrip() + "…"


def _strip_article_noise(text: str) -> str:
    if not text:
        return ""

    cleaned = html.unescape(str(text))
    cleaned = _strip_spoken_urls(cleaned)
    cleaned = re.sub(
        r'\b(?:Foto|Bild(?:text)?|Fotograf)\s*:\s*[^.!?]{0,220}(?=[.!?]|$)',
        ' ',
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r'\b(?:Arkivbild|Genrebild)\b', ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b[A-Za-z0-9+/]{80,}={0,2}\b', ' ', cleaned)

    lowered = cleaned.lower()
    cut_positions = [lowered.find(marker) for marker in _ARTICLE_HARD_CUT_MARKERS if marker in lowered]
    if cut_positions:
        cleaned = cleaned[:min(cut_positions)]

    sentences = re.split(r'(?<=[.!?])\s+|\s{2,}', cleaned)
    kept_sentences: List[str] = []
    for sentence in sentences:
        candidate = " ".join(sentence.split()).strip(' -|')
        if not candidate:
            continue
        lowered_candidate = candidate.lower()
        if any(re.search(pattern, lowered_candidate, flags=re.IGNORECASE) for pattern in _ARTICLE_DROP_PATTERNS):
            continue
        if len(candidate) < 25 and not re.search(r'\d', candidate):
            continue
        kept_sentences.append(candidate)

    cleaned = " ".join(kept_sentences)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' .,;:-')
    return cleaned


def _is_promotional_article(article: Dict[str, Any]) -> bool:
    title = (article.get('title') or '').strip().lower()
    link = (article.get('link') or '').strip().lower()

    if any(re.search(pattern, title, flags=re.IGNORECASE) for pattern in _PROMOTIONAL_TITLE_PATTERNS):
        return True

    if '/review/' in link or '/gallery/' in link:
        return True

    if 'techcrunch disrupt' in title and ('pass' in title or 'exhibit' in title):
        return True

    return False


def _article_text(article: Dict[str, Any], max_chars: int) -> str:
    """Hämta bästa tillgängliga artikeltext (content -> summary -> description -> snippet)."""
    text = (
        (article.get('content') or '')
        or (article.get('summary') or '')
        or (article.get('description') or '')
        or (article.get('snippet') or '')
    )
    sanitized = _strip_article_noise(text)
    return _truncate_text(sanitized, max_chars)


def _append_article_padding(script_text: str, articles: List[Dict], min_words: int) -> str:
    """Pad:ar upp manuset med källbaserad dialog tills vi når min_words.

    Viktigt: vi hittar inte på fakta; vi återger endast utdrag ur artikelns content-fält och
    säger tydligt när detaljer saknas.
    """
    if not script_text:
        script_text = ""

    current_wc = _count_words(script_text)
    if current_wc >= min_words:
        return script_text

    body, outro = _split_outro_block(script_text)

    # Undvik att pad:en blir oändlig om articles är tom.
    if not articles:
        filler = (
            "\n\nLisa: Då avrundar vi där för i dag och lämnar lite luft i flödet.\n"
            "Pelle: Ja, vi återkommer när vi har mer att bygga vidare på.\n"
        )
        combined = (body + filler).strip() if body else (script_text + filler).strip()
        return (combined + ("\n\n" + outro if outro else "")).strip()

    # Bygg en “snabba nyheter”-sektion som nämner källa + titel-token för bättre RSS-match.
    lines: List[str] = []
    lines.append("\n\nLisa: Innan vi sammanfattar och rundar av – här är några snabba nyheter för att få med helheten i flödet.")
    lines.append("Pelle: Perfekt – kör! Och säg gärna tydligt vilken källa det kommer från.")

    # Iterera artiklar flera varv om det behövs, men med hård cap.
    max_items = min(len(articles), 12)
    safe_articles = articles[:max_items]
    loops = 0
    base_text = (body if body else script_text)
    while _count_words(base_text + "\n" + "\n".join(lines)) < min_words and loops < 3:
        for a in safe_articles:
            if _count_words(base_text + "\n" + "\n".join(lines)) >= min_words:
                break
            source = (a.get('source') or 'Okänd källa').strip()
            title = (a.get('title') or '').strip()
            content_snip = _article_text(a, 260)
            if not content_snip:
                content_snip = "Detaljerna är fortfarande få, men huvudlinjen i utvecklingen är tydlig."

            lines.append(f"\nLisa: Nästa punkt – {source} har en artikel med rubriken \"{_truncate_text(title, 160)}\".")
            lines.append("Pelle: Kortversionen då, vad behöver man förstå?")
            lines.append(
                "Lisa: "
                + content_snip
                + ("" if content_snip.endswith(('.', '!', '?')) else ".")
            )
            lines.append("Pelle: Bra, då har vi kärnan utan att fastna i detaljerna.")
        loops += 1

    combined = (base_text + "\n" + "\n".join(lines)).strip()
    return (combined + ("\n\n" + outro if outro else "")).strip()


def _should_pad_short_scripts() -> bool:
    return os.getenv('MMM_PAD_SHORT_SCRIPTS', '0').strip().lower() in {'1', 'true', 'yes'}

def generate_structured_podcast_content(weather_info: str, today: Optional[datetime] = None) -> tuple[str, List[Dict]]:
    """Generera strukturerat podcast-innehåll med AI och riktig väderdata"""
    
    # Dagens datum för kontext
    today = today or datetime.now()

    # Eftertalk/eftersnack styrs av sources.json (så att GitHub Actions kan styra beteendet)
    config = load_config()
    aftertalk_cfg = _aftertalk_config_for_today(today, config)
    date_str = today.strftime('%Y-%m-%d')
    weekday = today.strftime('%A')
    swedish_weekday = SWEDISH_WEEKDAYS.get(weekday, weekday)
    swedish_month = SWEDISH_MONTHS.get(today.month, today.strftime('%B').lower())
    date_context = f"{swedish_weekday} den {today.day} {swedish_month} {today.year}"
    
    # Läs tidigare använda artiklar för upprepningsfilter (senaste 21 dagarna)
    # (viktigt för att undvika att samma nyhet tas upp dag efter dag)
    dedupe_days = 21
    used_articles = set()
    recent_episode_articles: List[Dict[str, Any]] = []

    memory_days_env = os.getenv('MMM_MEMORY_DAYS', '').strip()
    try:
        memory_days = int(memory_days_env) if memory_days_env else 60
    except ValueError:
        memory_days = 60
    memory_days = max(memory_days, dedupe_days)

    # Primärt: använd en persistent historikfil (fungerar i GitHub Actions via cache)
    history = None
    try:
        from src.news_dedupe import NewsHistory

        history = NewsHistory("news_history.json")
        history.load()
        history.prune(keep_days=60)
        logger.info("[HISTORY] news_history.json loaded (%s keys)", len(history.data.get('items', {})))
    except Exception as e:
        history = None
        logger.warning(f"[HISTORY] Kunde inte initiera news_history.json: {e}")
    try:
        recent_episode_articles = _load_recent_episode_articles(within_days=memory_days, today=today)
        cutoff_date = (today - timedelta(days=dedupe_days)).date()
        for prev in recent_episode_articles:
            try:
                prev_dt = prev.get('date')
                if isinstance(prev_dt, datetime) and prev_dt.date() < cutoff_date:
                    continue
            except Exception:
                continue

            prev_link = prev.get('link', '')
            prev_title = prev.get('title', '')
            url_key = _canonicalize_url(prev_link)
            fp_key = _title_fingerprint(prev_title)
            if url_key:
                used_articles.add(url_key)
            if fp_key:
                used_articles.add(fp_key)

        logger.info(f"[HISTORY] Laddade {len(used_articles)} tidigare använda artiklar för upprepningsfilter")
    except Exception as e:
        logger.warning(f"[HISTORY] Upprepningsfilter misslyckades: {e}")
    
    # ============================================================
    # MULTI-AGENT NEWS CURATION SYSTEM
    # ============================================================
    logger.info("\n" + "="*80)
    logger.info("🤖 AGENT-BASERAD NYHETSKURERING STARTAR")
    logger.info("="*80)
    
    # Importera agent-systemet
    available_articles: List[Dict] = []
    try:
        from news_curation_integration import curate_news_sync

        # Använd agent-systemet för att kurera artiklar
        available_articles = curate_news_sync('scraped_content.json')

        # Viktigt: agent-systemet kan "lyckas" men ändå ge 0 artiklar. Då får vi
        # ett extremt kort avsnitt (ex. 1 minut). Falla tillbaka till enkel filtrering.
        if not available_articles:
            logger.warning("⚠️ Agent-systemet returnerade 0 artiklar. Faller tillbaka på enkel filtrering...")
            available_articles = _fallback_collect_articles_from_scraped()

        logger.info(f"\n✅ Artikelurval klart: {len(available_articles)} artiklar för podcast")
        logger.info("="*80 + "\n")

    except Exception as e:
        logger.error(f"❌ Agent-systemet misslyckades: {e}")
        logger.warning("Faller tillbaka på enkel filtrering...")
        available_articles = _fallback_collect_articles_from_scraped()
    
    # Skapa artikelreferenser för AI
    article_refs = ""
    if available_articles:
        # Filtrera bort upprepningar (men tillåt uppföljningar)
        filtered_articles = []
        skipped_count = 0
        skipped_promotional_count = 0
        skipped_articles: List[Dict] = []
        for a in available_articles:
            if _is_promotional_article(a):
                skipped_promotional_count += 1
                logger.info(f"[CURATION] Skipping promotional/article-marketing item: {a.get('source', '')} - {a.get('title', '')[:80]}")
                log_diagnostic('article_skipped_promotional', {
                    'source': a.get('source', ''),
                    'title': a.get('title', ''),
                    'link': a.get('link', ''),
                })
                continue

            url_key = _canonicalize_url(a.get('link', ''))
            fp_key = _title_fingerprint(a.get('title', ''))

            # Matcha både "legacy" (episode_articles_*.json) och persistent historik (news_history.json)
            hist_url_key = f"url:{url_key}" if url_key else ""
            hist_fp_key = f"title:{fp_key}" if fp_key else ""

            is_repeat_by_url = bool(url_key and url_key in used_articles)
            is_repeat_by_fp = bool(fp_key and fp_key in used_articles)

            if history is not None:
                try:
                    is_repeat_by_url = is_repeat_by_url or bool(hist_url_key and history.seen_within_days(hist_url_key, dedupe_days))
                    is_repeat_by_fp = is_repeat_by_fp or bool(hist_fp_key and history.seen_within_days(hist_fp_key, dedupe_days))
                except Exception:
                    # Historik ska aldrig stoppa körningen
                    pass

            is_repeat = is_repeat_by_url or is_repeat_by_fp
            is_follow_up = _is_follow_up_article(a.get('title', ''), a.get('content', ''))

            if is_repeat and not is_follow_up:
                skipped_count += 1
                skipped_articles.append(a)
                logger.info(f"[HISTORY] Skipping repeat: {a.get('source', '')} - {a.get('title', '')[:80]}")
                log_diagnostic('article_skipped_repeat', {
                    'source': a.get('source', ''),
                    'title': a.get('title', ''),
                    'link': a.get('link', ''),
                    'repeat_by_url': is_repeat_by_url,
                    'repeat_by_title_fingerprint': is_repeat_by_fp,
                    'url_key': url_key,
                    'title_fingerprint': fp_key,
                })
                continue

            if is_repeat and is_follow_up:
                log_diagnostic('article_allowed_follow_up', {
                    'source': a.get('source', ''),
                    'title': a.get('title', ''),
                    'link': a.get('link', ''),
                    'repeat_by_url': is_repeat_by_url,
                    'repeat_by_title_fingerprint': is_repeat_by_fp,
                })

            cleaned_content = _article_text(a, 5000)
            if not cleaned_content:
                logger.info(f"[CURATION] Skipping article without usable editorial text after cleanup: {a.get('source', '')} - {a.get('title', '')[:80]}")
                log_diagnostic('article_skipped_empty_after_cleanup', {
                    'source': a.get('source', ''),
                    'title': a.get('title', ''),
                    'link': a.get('link', ''),
                })
                continue

            a = dict(a)
            a['content'] = cleaned_content
            filtered_articles.append(a)

            # Markera som sedd i persistent historik när vi väljer att behålla artikeln
            if history is not None:
                try:
                    history.mark_seen([hist_url_key, hist_fp_key])
                except Exception:
                    pass

        if skipped_count:
            logger.info(f"[HISTORY] Filtrerade bort {skipped_count} upprepade artiklar")
            log_diagnostic('dedupe_summary', {
                'skipped_repeat_count': skipped_count,
                'remaining_article_count': len(filtered_articles),
            })

        if skipped_promotional_count:
            logger.info(f"[CURATION] Filtrerade bort {skipped_promotional_count} reklam-/promoartiklar")
            log_diagnostic('promotional_filter_summary', {
                'skipped_promotional_count': skipped_promotional_count,
                'remaining_article_count': len(filtered_articles),
            })

        # Om dedupe blir för aggressiv: fyll på med repeats så vi kan skapa ett fullängdsavsnitt.
        # Hellre lite repetition än att publicera ~1 minut.
        min_articles_env = os.getenv('MMM_MIN_ARTICLES', '').strip()
        try:
            min_articles = int(min_articles_env) if min_articles_env else 6
        except ValueError:
            min_articles = 6

        if len(filtered_articles) < min_articles and skipped_articles:
            needed = min_articles - len(filtered_articles)
            logger.warning(f"[HISTORY] För få artiklar efter dedupe ({len(filtered_articles)}<{min_articles}). Återinför {needed} repeats för att nå miniminivå.")
            log_diagnostic('dedupe_relaxed', {
                'min_articles': min_articles,
                'before_count': len(filtered_articles),
                'skipped_available': len(skipped_articles),
            })
            filtered_articles.extend(skipped_articles[:needed])
            log_diagnostic('dedupe_relaxed', {
                'after_count': len(filtered_articles),
            })

        available_articles = filtered_articles

        # Spara persistent historik (om den är aktiverad)
        if history is not None:
            try:
                history.save()
                logger.info("[HISTORY] news_history.json saved")
            except Exception as e:
                logger.warning(f"[HISTORY] Kunde inte spara news_history.json: {e}")

        article_refs = "\n\nTILLGÄNGLIGA ARTIKLAR ATT REFERERA TILL:\n"
        max_article_chars_env = os.getenv('MMM_PROMPT_ARTICLE_CHARS', '').strip()
        try:
            max_article_chars = int(max_article_chars_env) if max_article_chars_env else 320
        except ValueError:
            max_article_chars = 320

        max_prompt_articles_env = os.getenv('MMM_PROMPT_MAX_ARTICLES', '').strip()
        try:
            max_prompt_articles = int(max_prompt_articles_env) if max_prompt_articles_env else 6
        except ValueError:
            max_prompt_articles = 6
        max_prompt_articles = max(3, min(10, max_prompt_articles))

        for i, article in enumerate(available_articles[:max_prompt_articles], 1):
            article_title = _truncate_text(article.get('title', ''), 140)
            article_content = _article_text(article, max_article_chars)
            article_source = article.get('source', 'Okänd källa')
            article_refs += f"{i}. {article_source}: {article_title}\n   Innehåll: {article_content}\n   [Referera som: {article_source}]\n\n"

    callback_refs = ""
    try:
        max_callbacks_env = os.getenv('MMM_MEMORY_MAX_CALLBACKS', '').strip()
        try:
            max_callbacks = int(max_callbacks_env) if max_callbacks_env else 3
        except ValueError:
            max_callbacks = 3
        max_callbacks = max(0, min(6, max_callbacks))

        if max_callbacks and recent_episode_articles:
            min_overlap_env = os.getenv('MMM_MEMORY_MIN_OVERLAP', '').strip()
            min_jaccard_env = os.getenv('MMM_MEMORY_MIN_JACCARD', '').strip()
            max_freq_env = os.getenv('MMM_MEMORY_ANCHOR_MAX_FREQ', '').strip()
            min_len_env = os.getenv('MMM_MEMORY_ANCHOR_MIN_LEN', '').strip()
            try:
                min_overlap = int(min_overlap_env) if min_overlap_env else 4
            except ValueError:
                min_overlap = 4
            try:
                min_jaccard = float(min_jaccard_env) if min_jaccard_env else 0.50
            except ValueError:
                min_jaccard = 0.50
            try:
                anchor_max_freq = int(max_freq_env) if max_freq_env else 2
            except ValueError:
                anchor_max_freq = 2
            try:
                anchor_min_len = int(min_len_env) if min_len_env else 7
            except ValueError:
                anchor_min_len = 7

            debug_env = os.getenv('MMM_MEMORY_DEBUG', '').strip().lower()
            memory_debug = debug_env in {'1', 'true', 'yes', 'on'}
            debug_samples_env = os.getenv('MMM_MEMORY_DEBUG_MAX_SAMPLES', '').strip()
            try:
                debug_max_samples = int(debug_samples_env) if debug_samples_env else 6
            except ValueError:
                debug_max_samples = 6

            hints, debug_info = _build_previous_coverage_hints(
                current_articles=available_articles[:10],
                recent_episode_articles=recent_episode_articles,
                today=today,
                max_hints=max_callbacks,
                min_overlap_tokens=max(2, min_overlap),
                min_jaccard=max(0.10, min(0.90, min_jaccard)),
                informative_max_freq=max(1, anchor_max_freq),
                min_anchor_token_len=max(4, anchor_min_len),
                debug=memory_debug,
                debug_max_samples=max(0, debug_max_samples),
            )

            # Always log a compact summary so we can tune thresholds without guesswork.
            try:
                log_diagnostic('memory_match_summary', {
                    'window_days': memory_days,
                    'max_callbacks': max_callbacks,
                    'min_overlap': min_overlap,
                    'min_jaccard': min_jaccard,
                    'anchor_max_freq': anchor_max_freq,
                    'anchor_min_len': anchor_min_len,
                    'current_considered': int((debug_info or {}).get('current_considered', 0)),
                    'recent_items': int((debug_info or {}).get('recent_items', 0)),
                    'evaluated_pairs': int((debug_info or {}).get('evaluated_pairs', 0)),
                    'reasons': (debug_info or {}).get('reasons', {}),
                    'samples': (debug_info or {}).get('samples', []) if memory_debug else [],
                })
            except Exception:
                pass

            # Optional: print to main log (Actions) for easier tuning.
            if memory_debug:
                try:
                    reasons = (debug_info or {}).get('reasons', {}) or {}
                    logger.info(
                        "[MEMORY][DEBUG] Summary: considered=%s recent=%s pairs=%s emitted=%s no_candidate=%s no_anchor=%s overlap_below=%s sim_below=%s",
                        (debug_info or {}).get('current_considered', 0),
                        (debug_info or {}).get('recent_items', 0),
                        (debug_info or {}).get('evaluated_pairs', 0),
                        reasons.get('hint_emitted', 0),
                        reasons.get('no_candidate', 0),
                        reasons.get('no_anchor_tokens', 0),
                        reasons.get('overlap_below_min', 0),
                        reasons.get('similarity_below_min', 0),
                    )
                    samples = (debug_info or {}).get('samples', []) or []
                    for s in samples[:max(0, debug_max_samples)]:
                        logger.info(
                            "[MEMORY][DEBUG] Sample: '%s' (%s) anchors='%s' best_score=%s prev=%s %s",
                            s.get('current_title', ''),
                            s.get('current_source', ''),
                            s.get('anchor_tokens', ''),
                            s.get('best_any_score', ''),
                            s.get('best_any_prev_date', ''),
                            s.get('best_any_prev_source', ''),
                        )
                except Exception:
                    pass

            if hints:
                callback_refs = "\n\nMINNESKROKAR (INTERNT UNDERLAG – SKA INTE ÅTERGES SOM LISTA I MANUSET):\n"
                callback_refs += (
                    "- Endast om du är MYCKET säker på att det är samma ämne: lägg in EN naturlig mening i förbifarten, "
                    "t.ex. 'Vi var inne på det här ämnet senast den ...'.\n"
                    "- Om du är det minsta osäker: hoppa över återkopplingen helt.\n"
                    "- Säg 'ämnet' (inte 'exakt samma nyhet') och nämn gärna datum, men undvik att återge den gamla rubriken.\n\n"
                )
                for h in hints:
                    topic = (h.get('topic_tokens') or '').strip()
                    topic_part = f" (ämnesord: {topic})" if topic else ""
                    callback_refs += (
                        f"MINNESKROK: Dagens källa {h.get('current_source','')}{topic_part}. "
                        f"Senast vi var inne på ämnet: {h.get('previous_date','')} (källa: {h.get('previous_source','')}).\n"
                    )

                log_diagnostic('memory_callbacks_built', {
                    'count': len(hints),
                    'window_days': memory_days,
                    'min_overlap': min_overlap,
                    'min_jaccard': min_jaccard,
                    'anchor_max_freq': anchor_max_freq,
                    'anchor_min_len': anchor_min_len,
                })
            else:
                log_diagnostic('memory_callbacks_none', {
                    'window_days': memory_days,
                    'min_overlap': min_overlap,
                    'min_jaccard': min_jaccard,
                    'anchor_max_freq': anchor_max_freq,
                    'anchor_min_len': anchor_min_len,
                })
    except Exception as e:
        logger.warning(f"[MEMORY] Kunde inte bygga återkopplingar: {e}")

    # Absolut krav: om vi inte har någon artikel att basera avsnittet på ska vi inte försöka.
    # Detta tenderar annars att ge superkorta/manuslösa avsnitt.
    min_articles_env = os.getenv('MMM_MIN_ARTICLES', '').strip()
    try:
        min_articles = int(min_articles_env) if min_articles_env else 6
    except ValueError:
        min_articles = 6
    if not available_articles or len(available_articles) < 1:
        raise RuntimeError("Inga artiklar tillgängliga efter kurering/filtrering; avbryter för att undvika kort/okällat avsnitt")
    
    aftertalk_instructions = ""
    if aftertalk_cfg:
        style = aftertalk_cfg.get('style', '')
        style_block = f"\nSTIL (eftersnack): {style}\n" if style else ""
        aftertalk_instructions = (
            "\n\nEFTERSNACK (ENBART IDAG - KRITISKT):\n"
            f"- Lägg till ett kort EFTERSNACK precis i slutet, efter ordinarie outro (eller som en tydligt separerad bonus på slutet).\n"
            f"- Längd: cirka {aftertalk_cfg.get('target_seconds', 120)} sekunder (tillåtet spann {aftertalk_cfg.get('min_seconds', 90)}–{aftertalk_cfg.get('max_seconds', 150)} sek).\n"
            "- Innehåll: meta, lätt komiskt, självdistanserat bakom-kulisserna-snack om hur dagens manus byggdes, utan nya fakta eller nya nyheter.\n"
            "- INGA nya källor, inga nya påståenden, inga nya rubriker. Bara reflektion/ton.\n"
            + style_block
        )
    else:
        aftertalk_instructions = (
            "\n\nEFTERSNACK (FÖRBJUDET - KRITISKT):\n"
            "- Lägg INTE till eftersnack/efterprat/bonussegment.\n"
            "- Avsluta när outrot är klart, och skriv inga extra repliker efter sista avslutningen.\n"
        )

    prompt = f"""Skapa ett KOMPLETT men KONCIST manus för dagens avsnitt av "MMM Senaste Nytt" - en svensk daglig nyhetspodcast om teknik, AI och klimat.

DATUM (KRITISKT): {date_str} ({date_context})
VÄDER: {weather_info}
LÄNGD: Absolut mål är 6,5-8 minuter (cirka 850-1050 ord för talat innehåll)
VÄRDAR: Lisa (kvinnlig, professionell men vänlig) och Pelle (manlig, nyfiken och engagerad)

{article_refs}{callback_refs}

DETALJERAD STRUKTUR:
1. INTRO & VÄLKOMST (45-60 sekunder) - Inkludera RIKTIG väderinfo från "{weather_info}"
2. KORT INNEHÅLLSÖVERSIKT (20-30 sekunder) - En snabb orientering, ingen lång uppräkning
3. HUVUDNYHETER (4,5-6 minuter) - 4-5 nyheter med tydlig prioritering och lagom mycket analys
4. KORT ANALYS (60-90 sekunder) - Lisa och Pelle knyter ihop mönster, konsekvenser och möjliga vägval
5. KORT SAMMANFATTNING (20-30 sekunder) - Bara det viktigaste
6. OUTRO & MMM-KOPPLING (30-45 sekunder) - STARK koppling till huvudpodden "Människa Maskin Miljö"

INNEHÅLLSKRAV OCH ÄMNESFÖRDELNING:
- KRITISKT: Utgå från DATUM (KRITISKT) ovan (= dagens datum för denna körning). Nämn inte fel månad (t.ex. "november") eller fel datum.
- Lisa säger "MMM Senaste Nytt" naturligt och professionellt (inte överdrivet)
- Använd RIKTIG väderdata: "{weather_info}" - inte påhittade kommentarer om "fin dag i Stockholm"
- Sikta på 4-5 konkreta nyheter från svenska och internationella källor
- Om underlaget är svagare: välj hellre 3-4 nyheter och gör dem tydliga än att pressa in fler punkter
- OBLIGATORISK ÄMNESFÖRDELNING (mycket viktigt för balans):
  * MINST 50% av nyheterna MÅSTE handla om KLIMAT, MILJÖ och HÅLLBARHET
  * Maximalt 50% får handla om AI och teknologi (inte klimatrelaterad)
  * Prioritera SVENSKA klimat- och miljönyheter när de finns tillgängliga
    * Exempel: Om du har 4 nyheter, MINST 2 ska vara klimat/miljö
- Varje nyhet ska vara kärnfull och tydlig, oftast 90-130 ord inklusive diskussion
- Lisa och Pelle ska ha naturliga konversationer med följdfrågor
- Inkludera siffror, fakta och konkreta exempel
- Nämn specifika företag, forskare eller organisationer
- Tempot ska kännas lugnt och begripligt i örat: kortare repliker, färre fakta per mening och tydliga andningspauser mellan ämnen
- Hellre ett avsnitt på cirka 7 minuter än ett stressat avsnitt som jagar 10 minuter
- MÅLGRUPP: smarta lyssnare och beslutsfattare inom människa, maskin och miljö som vill förstå vad nyheten betyder i praktiken
- PROGRAMLEDARROLL: de ska inte bara återge nyheten, utan hjälpa lyssnaren att orientera sig och förstå vad man kan göra med informationen
- För 1-2 av dagens viktigaste nyheter ska programledarna lägga in TRE MÖJLIGA VÄGAR FRAMÅT eller scenarier
- Varje scenario måste vara kort, konkret och förankrat i det som faktiskt står i källorna eller i tydliga följder av källfakta
- Formulera scenarierna som handlings- eller utvecklingsspår, till exempel: "en väg är...", "en annan möjlighet är...", "en tredje riktning att hålla ögonen på är..."
- Scenarierna ska hjälpa beslutsfattare att tänka framåt, inte låta som löst tyckande eller science fiction
- Om källstödet inte räcker för tre tydliga scenarier: nöj er med två eller hoppa över helt

REDATIONELL LINJE (KRITISKT):
- MMM Senaste Nytt är INTE för kärnkraft som klimatlösning. Presentera inte kärnkraft som "lösningen".
- Om kärnkraft nämns: var saklig och kritisk (mycket höga kostnader, långa byggtider som försenar fossil undanträngning,
  avfallsfrågan/slutförvar i mycket lång tid, och att det riskerar tränga undan snabbare alternativ).

KÄLLHÄNVISNING - MYCKET VIKTIGT:
- ANVÄND ENDAST artiklarna listade ovan som källor för dina nyheter - ALDRIG sociala medier eller opålitliga källor
- VARJE nyhet MÅSTE baseras på en specifik artikel från seriösa medier (SVT, DN, BBC, Reuters etc.)
- FÖRBJUDET: Facebook, Twitter/X, Instagram, TikTok, YouTube eller andra sociala medier som källor
- Referera tydligt: "SVT Nyheter rapporterar att...", "BBC News skriver att...", "Reuters meddelar att..."
- Specifika personer MÅSTE namnges när de finns i artiklarna (t.ex. "Miljöminister Romina Pourmokhtari säger...", "Enligt statsminister Ulf kristersson...")
- Konkreta detaljer MÅSTE tas från artiklarna - påhitta ALDRIG fakta
- När möjligt: använd siffror och fakta från artiklarna
- Om underlaget är tunt: håll delen kort och konkret. Säg bara vad som är bekräftat och gå vidare utan att prata om "underlag", "källtext", "vad vet vi faktiskt" eller att ni "inte hittar på".
- Läs aldrig upp webbadresser, domännamn, artikellänkar, prenumerationsvillkor, kampanjer, rabatter, biljettpriser eller andra kommersiella erbjudanden.
- Om en källa innehåller navigationsbrus, inloggningsrutor, "läs mer", reklam eller prisinformation ska det ignoreras helt och aldrig återges i manuset.
- Om originalartikeln är på engelska eller annat språk: sammanfatta ALLTID innehållet på naturlig svenska.
- Korta originalcitat är tillåtna bara om de är helt centrala, och då högst 6 ord i originalspråk.
- Läs ALDRIG upp längre engelska meningar eller stycken ur artikeln. Parafrasera i stället på svenska.
- Undvik vaga termer - var specifik baserat på vad som faktiskt står i artiklarna
- Lyssnarna ska kunna förstå att nyheten kommer från en etablerad, trovärdig nyhetskälla

OUTRO-KRAV (MYCKET VIKTIGT):
- INGEN teasing av "nästa avsnitt" 
- INGA påhittade lyssnarfrågor
- STARK koppling till huvudpodden "Människa Maskin Miljö"
- Förklara att MMM Senaste Nytt är en del av Människa Maskin Miljö-familjen
- Uppmana lyssnare att kolla in huvudpodden för djupare analyser
- Ingen AI-brasklapp eller metakommentar om att ni är AI-röster, hur ni verifierar uppgifter eller att lyssnaren ska dubbelkolla länkar

SLUTREGLER (KRITISKT):
- Ingen utfyllnad efter outrot (om inte EFTERSNACK är explicit tillåtet idag).
- Ingen "vi fortsätter", "en sista grej", "bonus" eller liknande efter att ni sagt tack och rundat av.
- Prata aldrig om er arbetsmetod, om "underliggande information", om vad ni "vet faktiskt" eller om att ni "inte hittar på".
{aftertalk_instructions}

DIALOGREGLER:
- Använd naturliga övergångar: "Det påminner mig om...", "Apropå det...", "Interessant nog..."
- Lisa och Pelle ska ibland avbryta varandra naturligt
- Inkludera korta pauser för eftertanke: "Hmm, det är en bra poäng..."
- Använd svenska uttryck och vardagligt språk
- Variera meningslängderna för naturligt flyt
- Håll replikerna till 1-3 meningar i taget i normalfallet. Undvik långa stycken som måste läsas snabbt.
- KRITISKT: Varje replik måste logiskt följa föregående - ingen får svara på något som inte sagts ännu
- KRITISKT: Om någon nämner en siffra/statistik, måste den först ha presenterats i tidigare replik
- Kontrollera att alla hänvisningar ("det", "den siffran", "som du sa") faktiskt refererar till något som redan sagts

FORMAT: Skriv ENDAST som ren dialog med "Talarnamn: Text" - INGEN markdown eller formatering!
FÖRBJUDET: **, ##, ---, ###, rubriker, markeringar, lyssnarfrågor, "nästa avsnitt" - bara ren dialog!

EXEMPEL INTRO:
Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.
Pelle: Och jag heter Pelle. Idag är det {swedish_weekday} den {today.day} {swedish_month} {today.year}, och {weather_info.lower()}.
Lisa: Ja, det stämmer! Men vi har mycket spännande att prata om idag inom teknik, AI och klimat.

VIKTIGT: Endast dialog - inga rubriker eller formatering! Bara "Namn: Text" rad för rad.

Skapa nu ett komplett manus för dagens avsnitt. Sikta på cirka 900 ord och gå inte över 1050 ord om underlaget inte verkligen kräver det:"""

    messages = [{"role": "user", "content": prompt}]

    podcast_settings = config.get('podcastSettings', {}) if isinstance(config.get('podcastSettings'), dict) else {}
    env_provider = os.getenv('MMM_AI_PROVIDER', '').strip().lower()
    cfg_provider = str(podcast_settings.get('ai_provider', '') or '').strip().lower()
    llm_provider = env_provider or cfg_provider or 'gemini'

    env_model = os.getenv('MMM_LLM_MODEL', '').strip()
    cfg_gemini_model = str(podcast_settings.get('gemini_model', '') or '').strip()
    cfg_openrouter_model = str(podcast_settings.get('openrouter_model', '') or '').strip()
    cfg_openai_model = str(podcast_settings.get('openai_model', '') or '').strip()

    if llm_provider == 'gemini':
        llm_model = env_model or cfg_gemini_model or cfg_openrouter_model or 'gemini-2.5-flash'
    elif llm_provider == 'openai':
        llm_model = env_model or cfg_openai_model or 'gpt-5-mini'
    else:
        llm_provider = 'openrouter'
        llm_model = env_model or cfg_openrouter_model or 'google/gemini-2.5-flash'
    
    def generate_fallback_content_from_articles() -> str:
        # Bygg ett längre, källbaserat manus utan LLM så att vi inte publicerar ~1 minut.
        chosen = list(available_articles or [])
        if not chosen:
            chosen = _fallback_collect_articles_from_scraped(max_per_source=4, max_total=20)

        # Håll fallback-läget kort och tydligt i stället för att maxa antalet punkter.
        chosen = chosen[:5]

        intro = (
            f"Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.\n\n"
            f"Pelle: Och jag heter Pelle. Idag är det {swedish_weekday} den {today.day} {swedish_month} {today.year}, och {weather_info.lower()}.\n\n"
            "Lisa: Vi går igenom dagens viktigaste nyheter inom teknik, AI, klimat och miljö.\n\n"
            "Pelle: Bra! Vi kör igång.\n"
        )

        overview_parts = []
        for a in chosen[:5]:
            overview_parts.append(f"{a.get('source','')}: {a.get('title','')}")
        overview = (
            "\nLisa: Här är en snabb översikt på vad vi tar upp idag.\n"
            f"Pelle: { ' | '.join([p for p in overview_parts if p]) }.\n"
        )

        lead_templates = [
            'Lisa: Från {source} kommer en nyhet om "{title}".',
            'Pelle: {source} lyfter i dag fram "{title}".',
            'Lisa: Vi stannar till vid {source}, som rapporterar om "{title}".',
            'Pelle: En annan utveckling som sticker ut kommer från {source} och gäller "{title}".',
        ]
        bridge_templates = [
            'Pelle: Det viktiga här är vad det här kan betyda i praktiken.',
            'Lisa: Det här är intressant eftersom följderna kan bli större än rubriken först antyder.',
            'Pelle: Här finns det flera spår att hålla ögonen på framåt.',
            'Lisa: Det som fastnar här är hur snabbt läget kan förändras beroende på nästa besked.',
        ]
        wrap_templates = [
            'Pelle: Det här är en fråga vi lär återkomma till.',
            'Lisa: Det här kan få större följder längre fram.',
            'Pelle: Nu blir det intressant att se vad nästa steg blir.',
            'Lisa: Den här utvecklingen är värd att hålla ögonen på.',
        ]

        body_lines: List[str] = []
        for idx, a in enumerate(chosen[:5], 1):
            source = a.get('source', 'Okänd källa')
            title = (a.get('title') or '').strip()
            content_snip = _article_text(a, 360)
            if not content_snip:
                content_snip = "Detaljerna är fortfarande få, men rubriken pekar tydligt på vad som står på spel."

            lead_line = lead_templates[(idx - 1) % len(lead_templates)].format(source=source, title=title)
            bridge_line = bridge_templates[(idx - 1) % len(bridge_templates)]
            wrap_line = wrap_templates[(idx - 1) % len(wrap_templates)]

            body_lines.append(f"\n{lead_line}")
            body_lines.append(bridge_line)
            body_lines.append(
                "Lisa: "
                + content_snip
                + ("" if content_snip.endswith(('.', '!', '?')) else ".")
            )
            body_lines.append(wrap_line)

        outro = (
            "\nLisa: Det var dagens genomgång av läget just nu.\n"
            "Pelle: Vill du ha mer djup och sammanhang finns huvudpodden Människa Maskin Miljö, där vi går längre i analysen.\n"
            "Lisa: Tack för att du lyssnade på MMM Senaste Nytt!\n"
        )

        draft = (intro + "\n" + overview + "\n" + "\n".join(body_lines) + "\n" + outro).strip()

        # Säkerställ minlängd även i fallback-läget.
        min_words_env_local = os.getenv('MMM_MIN_SCRIPT_WORDS', '').strip()
        try:
            min_words_local = int(min_words_env_local) if min_words_env_local else 900
        except ValueError:
            min_words_local = 900
        if _should_pad_short_scripts():
            return _append_article_padding(draft, chosen, min_words_local)
        return draft

    try:
        logger.info(f"[AI] Using LLM provider/model: {llm_provider}/{llm_model}")
        content = get_openrouter_response(messages, model=llm_model, provider=llm_provider)
        # Guard: ibland svarar modellen alldeles för kort (t.ex. när källistan är tunn).
        # Gör retry endast vid extremt kort svar för att minska extra API-kostnad.
        min_words_env = os.getenv('MMM_MIN_SCRIPT_WORDS', '').strip()
        try:
            min_words = int(min_words_env) if min_words_env else 900
        except ValueError:
            min_words = 900
        retry_threshold_env = os.getenv('MMM_RETRY_IF_BELOW_WORDS', '').strip()
        try:
            retry_if_below_words = int(retry_threshold_env) if retry_threshold_env else 700
        except ValueError:
            retry_if_below_words = 700
        wc = _count_words(content)
        if wc < retry_if_below_words:
            logger.warning(f"[AI] Manus för kort ({wc} ord < {min_words}). Försöker en gång till med förtydligad prompt...")
            log_diagnostic('ai_script_too_short_retry', {
                'word_count': wc,
                'min_words': min_words,
                'retry_if_below_words': retry_if_below_words,
                'provider': llm_provider,
                'model': llm_model,
            })
            retry_prompt = prompt + "\n\nVIKTIGT: Ditt förra svar blev för kort. Skriv om manuset till minst " + str(min_words) + " ord. Behåll exakt samma FORMAT (bara 'Namn: text') och använd de listade källorna."
            content = get_openrouter_response([{"role": "user", "content": retry_prompt}], model=llm_model, provider=llm_provider)
            wc2 = _count_words(content)
            logger.info(f"[AI] Retry word count: {wc2}")
            if wc2 < min_words:
                if _should_pad_short_scripts():
                    logger.warning(
                        f"[AI] Retry fortfarande kort ({wc2} < {min_words}). Pad:ar upp med rubrikrunda (MMM_PAD_SHORT_SCRIPTS=1)."
                    )
                    log_diagnostic('ai_script_padded', {
                        'word_count_before': wc2,
                        'min_words': min_words,
                    })
                    content = _append_article_padding(content, available_articles, min_words)
                else:
                    logger.warning(
                        f"[AI] Retry fortfarande kort ({wc2} < {min_words}) och padding är av. Faller tillbaka till källbaserat manus."
                    )
                    log_diagnostic('ai_script_short_fallback', {
                        'word_count': wc2,
                        'min_words': min_words,
                        'provider': llm_provider,
                        'model': llm_model,
                        'fallback': 'article_based',
                    })
                    content = generate_fallback_content_from_articles()
        logger.info("[AI] Genererade podcast-innehåll med väderdata")
        return content, available_articles
    except Exception as e:
        logger.error(f"[ERROR] Kunde inte generera AI-innehåll: {e}")
        log_diagnostic('ai_script_generation_failed', {
            'error': f"{type(e).__name__}: {e}",
            'fallback': 'article_based',
        })
        # Fallback till källbaserat (längre) innehåll
        return generate_fallback_content_from_articles(), available_articles

def generate_fallback_content(date_str: str, weekday: str, weather_info: str) -> str:
    """Fallback-innehåll om AI inte fungerar"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        month_swedish = SWEDISH_MONTHS.get(dt.month, dt.strftime('%B').lower())
        day = dt.day
        year = dt.year
    except Exception:
        month_swedish = datetime.now().strftime('%B').lower()
        day = int(datetime.now().strftime('%d'))
        year = datetime.now().year

    return f"""Lisa: Hej och välkommen till MMM Senaste Nytt! Jag heter Lisa.

Pelle: Och jag heter Pelle. Idag är det {weekday} den {day} {month_swedish} {year}, och {weather_info.lower()}.

Lisa: Precis! Vi har mycket att prata om idag inom teknik, AI och klimat.

Pelle: Vi börjar med att OpenAI har lanserat en förbättrad version av GPT-4 som de kallar GPT-4 Turbo. Modellen är inte bara snabbare, utan också betydligt billigare att använda för utvecklare.

Lisa: Det är verkligen stora nyheter, Pelle. Vad tror du det betyder för svenska företag som använder AI?

Pelle: Jag tror det kommer att demokratisera AI-användningen. Mindre företag kommer nu ha råd att bygga avancerade AI-lösningar.

Lisa: Spännande! Vi fortsätter med klimatnyheter. Tesla har presenterat sina nya 4680-batterier som påstås ha 50% bättre energidensitet.

Pelle: Det är riktigt intressanta nyheter. Bättre batterier är nyckeln till både elbilar och energilagring.

Lisa: För att sammanfatta har vi pratat om OpenAI:s nya modell och Teslas batteriteknik.

Pelle: Det här avsnittet av MMM Senaste Nytt är en del av vårt större program Människa Maskin Miljö, där vi går djupare in på hur teknik, klimat och samhälle påverkar varandra.

Lisa: Tack för att ni lyssnade! Vi hörs imorgon med fler nyheter."""

def clean_text_for_tts(text: str) -> str:
    """Ta bort markdown-formattering och andra tecken som inte ska läsas upp"""
    # Ta bort markdown-formattering
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **text** -> text
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *text* -> text
    text = re.sub(r'#{1,6}\s*', '', text)           # ### headings -> 
    text = re.sub(r'---+', '', text)                # --- -> 
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)  # list items
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](link) -> text
    
    # Ta bort andra formattering
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `code` -> code
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)  # __text__ -> text
    text = _strip_spoken_urls(text)
    
    # Rensa extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def _strip_spoken_urls(text: str) -> str:
    """Ta bort webbadresser och bara domännamn som annars läses upp bokstav för bokstav."""
    if not text:
        return ""

    cleaned = text
    for pattern in _SPOKEN_URL_PATTERNS:
        cleaned = pattern.sub(' ', cleaned)

    cleaned = re.sub(r'\s+([,.;:!?])', r'\1', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip()


def _normalize_inline_speaker_turns(text: str) -> str:
    """Bryt ut inline-dialog så Lisa/Pelle alltid hamnar på egna rader."""
    if not text:
        return ""

    return re.sub(
        r'(?<!^)(?<!\n)\s+(?=(?:\*{1,2})?(?:Lisa|Pelle|LISA|PELLE)(?:\*{1,2})?\s*:)',
        '\n',
        text,
    )

def split_long_text_for_tts(text: str, speaker: str, max_bytes: int = 4000) -> List[Dict]:
    """Dela upp lång text i TTS-kompatibla segment"""
    segments = []
    
    # Om texten är kort nog, returnera som ett segment
    if len(text.encode('utf-8')) <= max_bytes:
        return [{'speaker': speaker, 'text': text}]
    
    # Dela vid meningar först
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_bytes = len(sentence.encode('utf-8'))
        
        # Om en enskild mening är för lång, dela den hårdare
        if sentence_bytes > max_bytes:
            # Spara nuvarande chunk först
            if current_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(current_chunk).strip()
                })
                current_chunk = []
                current_size = 0
            
            # Dela den långa meningen vid komma eller ord
            words = sentence.split()
            word_chunk = []
            word_size = 0
            
            for word in words:
                word_bytes = len((word + ' ').encode('utf-8'))
                if word_size + word_bytes > max_bytes and word_chunk:
                    segments.append({
                        'speaker': speaker,
                        'text': ' '.join(word_chunk).strip()
                    })
                    word_chunk = [word]
                    word_size = word_bytes
                else:
                    word_chunk.append(word)
                    word_size += word_bytes
            
            if word_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(word_chunk).strip()
                })
        else:
            # Kontrollera om vi kan lägga till meningen
            if current_size + sentence_bytes > max_bytes and current_chunk:
                segments.append({
                    'speaker': speaker,
                    'text': ' '.join(current_chunk).strip()
                })
                current_chunk = [sentence]
                current_size = sentence_bytes
            else:
                current_chunk.append(sentence)
                current_size += sentence_bytes
    
    # Lägg till sista chunk
    if current_chunk:
        segments.append({
            'speaker': speaker,
            'text': ' '.join(current_chunk).strip()
        })
    
    return segments

def parse_podcast_text(text: str) -> List[Dict]:
    """Parsa podcast-text i segment med talare och repliker"""
    segments = []
    lines = _normalize_inline_speaker_turns(text or '').strip().split('\n')
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Hoppa över rena formattering-rader
        if line.startswith('#') or line.startswith('---') or line.startswith('### '):
            continue
            
        # Identifiera talare-rader (med eller utan markdown-formattering)
        if ':' in line and len(line.split(':', 1)) == 2:
            speaker_part, text_part = line.split(':', 1)
            
            # Rensa speaker-namnet från formattering
            speaker_name = clean_text_for_tts(speaker_part).strip()
            
            # Hoppa över om det inte ser ut som ett talare-namn
            if not speaker_name or len(speaker_name.split()) > 2:
                if current_speaker:
                    current_text.append(clean_text_for_tts(line))
                continue
            
            # Spara föregående segment
            if current_speaker and current_text:
                clean_text = ' '.join(current_text).strip()
                if clean_text:  # Endast om det finns text
                    # Dela upp långa segment för TTS-kompatibilitet (max 4000 bytes)
                    split_segments = split_long_text_for_tts(clean_text, current_speaker)
                    segments.extend(split_segments)
            
            # Starta nytt segment
            current_speaker = speaker_name
            text_part_clean = clean_text_for_tts(text_part).strip()
            current_text = [text_part_clean] if text_part_clean else []
        else:
            # Fortsätt med samma talare
            if current_speaker:
                clean_line = clean_text_for_tts(line)
                if clean_line:  # Endast lägg till om det finns text
                    current_text.append(clean_line)
    
    # Lägg till sista segmentet
    if current_speaker and current_text:
        clean_text = ' '.join(current_text).strip()
        if clean_text:  # Endast om det finns text
            # Dela upp långa segment för TTS-kompatibilitet (max 4000 bytes)
            split_segments = split_long_text_for_tts(clean_text, current_speaker)
            segments.extend(split_segments)
    
    return segments

def generate_audio_with_gemini_dialog(script_content: str, weather_info: str, output_file: str) -> bool:
    """Generera audio med Gemini TTS för naturlig dialog mellan Lisa och Pelle"""
    if not GEMINI_TTS_AVAILABLE:
        logger.info("[AUDIO] Gemini TTS inte tillgänglig, använder standard-metod")
        _set_last_gemini_error("GEMINI_TTS_AVAILABLE=False (importfel eller saknade dependencies)")
        return False
    
    try:
        logger.info("[AUDIO] Genererar naturlig dialog med Gemini TTS...")
        
        generator = GeminiTTSDialogGenerator()
        lisa_voice = generator.voices.get('Lisa', {})
        pelle_voice = generator.voices.get('Pelle', {})
        logger.info(
            "[AUDIO] Gemini voice mapping: Lisa=%s, Pelle=%s",
            lisa_voice.get('speaker_id', 'okänd'),
            pelle_voice.get('speaker_id', 'okänd'),
        )
        log_diagnostic('tts_voice_mapping', {
            'provider': 'gemini',
            'lisa_speaker_id': lisa_voice.get('speaker_id', ''),
            'pelle_speaker_id': pelle_voice.get('speaker_id', ''),
        })
        
        # Om manus redan är en dialog (Lisa:/Pelle:), använd det i stället för att
        # bygga om via heuristisk split (som kan skapa rader utan talarprefix).
        if any(tag in script_content for tag in ("Lisa:", "Pelle:", "LISA:", "PELLE:")):
            parsed_segments = parse_podcast_text(script_content)

            dialog_lines = []
            fallback_speaker = "Lisa"
            for seg in parsed_segments:
                speaker_raw = (seg.get('speaker') or '').strip()
                text = (seg.get('text') or '').strip()
                if not text:
                    continue

                speaker_lower = speaker_raw.lower()
                if 'lisa' in speaker_lower:
                    speaker = "Lisa"
                elif 'pelle' in speaker_lower:
                    speaker = "Pelle"
                else:
                    # Skulle bara inträffa om manus innehåller annan talare.
                    speaker = fallback_speaker
                    fallback_speaker = "Pelle" if fallback_speaker == "Lisa" else "Lisa"

                dialog_lines.append(f"{speaker}: {text}")

            dialog_script = "\n".join(dialog_lines).strip()
            logger.info(f"[AUDIO] Dialog-script byggt från {len(dialog_lines)} parsade repliker")
        else:
            # Skapa dialog-script från innehåll (fallback)
            dialog_script = generator.create_dialog_script(script_content, weather_info)
            logger.info("[AUDIO] Dialog-script skapat för Lisa och Pelle")

        if not dialog_script:
            logger.warning("[AUDIO] Tomt dialog-script för Gemini, faller tillbaka")
            return False
        
        # Structured turns ger stabilare röstkoppling och undviker att talarnamn läses upp.
        success = generator.synthesize_dialog_script_structured(
            dialog_script=dialog_script,
            output_file=output_file
        )

        if not success:
            logger.warning("[AUDIO] Structured Gemini TTS misslyckades, provar freeform som fallback")
            success = generator.synthesize_dialog_freeform(
                dialog_script=dialog_script,
                output_file=output_file
            )
        
        if success:
            logger.info(f"[AUDIO] ✅ Gemini TTS dialog sparad: {output_file}")
            _set_last_gemini_error(None)
            return True
        else:
            logger.warning("[AUDIO] Gemini TTS misslyckades, faller tillbaka till standard")
            _set_last_gemini_error("synthesize_dialog_freeform returned False (see [GEMINI-TTS] logs)")
            return False
            
    except Exception as e:
        _set_last_gemini_error(f"{type(e).__name__}: {e}")
        logger.exception("[AUDIO] Gemini TTS fel")
        logger.info("[AUDIO] Faller tillbaka till standard TTS")
        return False

def generate_audio_google_cloud(segments: List[Dict], output_file: str) -> bool:
    """Generera audio med Google Cloud TTS (fallback-metod)"""
    try:
        # Använd rätt TTS-klass
        from google_cloud_tts import GoogleCloudTTS
        
        # Konvertera segments till rätt format
        audio_segments = []
        for i, segment in enumerate(segments):
            speaker = segment['speaker'].lower()
            
            # Mappa talare till röster
            if 'lisa' in speaker:
                voice = 'lisa'
            elif 'pelle' in speaker:
                voice = 'pelle'
            else:
                # Alternerande röster
                voice = 'lisa' if i % 2 == 0 else 'pelle'
            
            audio_segments.append({
                'voice': voice,
                'text': segment['text']
            })
        
        # Skapa TTS-instans och generera audio
        tts = GoogleCloudTTS()
        audio_file = tts.generate_podcast_audio(audio_segments)
        
        if audio_file and os.path.exists(audio_file):
            shutil.move(audio_file, output_file)
            logger.info(f"[TTS] Audio genererad: {output_file}")
            return True
        else:
            logger.error("[ERROR] TTS-generering misslyckades")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] TTS-fel: {e}")
        return False


def _resolve_tts_provider() -> Tuple[str, Dict[str, Any]]:
    """Resolve active TTS provider with Gemini as explicit production default."""
    require_gemini = os.getenv('MMM_FORCE_GEMINI_TTS', '').strip().lower() in {'1', 'true', 'yes', 'y'}
    configured_provider = os.getenv('MMM_TTS_PROVIDER', '').strip().lower()

    if require_gemini:
        provider = 'gemini'
        reason = 'forced_gemini'
    elif configured_provider in {'gemini', 'google_cloud'}:
        provider = configured_provider
        reason = 'env_configured'
    elif configured_provider:
        logger.warning(f"[TTS] Okänd MMM_TTS_PROVIDER='{configured_provider}', använder gemini")
        provider = 'gemini'
        reason = 'invalid_env_fallback_to_gemini'
    else:
        provider = 'gemini'
        reason = 'default_gemini'

    details = {
        'provider': provider,
        'reason': reason,
        'require_gemini': require_gemini,
        'configured_provider': configured_provider or None,
        'gemini_available': bool(GEMINI_TTS_AVAILABLE),
    }
    return provider, details

def add_music_to_podcast(audio_file: str) -> str:
    """Lägg till musik och bryggkor till podcast med MusicMixer"""
    try:
        logger.info("[MUSIC] Lägger till musik och bryggkor...")
        
        # Skapa en MusicMixer-instans
        mixer = MusicMixer()
        
        # Skanna alla mp3-filer i music-mappen automatiskt
        music_dir = "audio/music"
        available_music = []
        
        if os.path.exists(music_dir):
            for filename in os.listdir(music_dir):
                if filename.lower().endswith('.mp3'):
                    full_path = os.path.join(music_dir, filename)
                    available_music.append(full_path)
        
        logger.info(f"[MUSIC] Hittade {len(available_music)} musikfiler: {[os.path.basename(f) for f in available_music]}")
        
        if not available_music:
            logger.warning("[MUSIC] Inga musikfiler hittades")
            return audio_file
            
        # Skapa varierad musikmix för hela avsnittet
        import random
        music_output = audio_file.replace('.mp3', '_with_music.mp3')
        
        # Nya förbättrade musikmixning med variation
        success = mixer.create_varied_music_background(
            speech_file=audio_file,
            available_music=available_music,
            output_file=music_output,
            music_volume=-15,  # Låg volym i dB
            segment_duration=60,  # Byt musik var 60:e sekund
            fade_duration=3000    # 3 sekunder crossfade mellan låtar
        )
        
        if success and os.path.exists(music_output):
            # Ersätt original med musikversion
            shutil.move(music_output, audio_file)
            logger.info(f"[MUSIC] Musik tillagd till {audio_file}")
            return audio_file
        else:
            logger.warning("[MUSIC] Kunde inte lägga till musik, använder original")
            return audio_file
            
    except Exception as e:
        logger.error(f"[MUSIC] Fel vid musiktillägg: {e}")
        return audio_file  # Returnera original om musik misslyckas


def enforce_intro_date(script_text: str, weekday: str, day: int, month: str) -> str:
    """Replace incorrect intro date phrases with the actual Swedish date."""
    if not script_text:
        return script_text

    def _replace_intro(match: re.Match) -> str:
        intro_line = match.group(0)
        comma_index = intro_line.find(',')
        suffix = intro_line[comma_index:] if comma_index != -1 else ''
        logger.info("[SCRIPT] Uppdaterar intro-datum till dagens datum")
        return f"Idag är det {weekday} den {day} {month}{suffix}"

    return re.sub(r"Idag är det[^\n]*", _replace_intro, script_text, count=1)


def clean_xml_text(text: Optional[str]) -> str:
    """Sanitize text for safe XML output"""
    if not text:
        return ""

    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    normalized = html.unescape(cleaned)
    return html.escape(normalized, quote=True)


def _linkify_text_line(line: str) -> str:
    """Convert plain URLs in a text line into safe HTML links."""
    if not line:
        return ""

    url_pattern = re.compile(r'(https?://[^\s<>"]+)')
    parts = url_pattern.split(line)
    html_parts = []

    for index, part in enumerate(parts):
        if not part:
            continue

        if index % 2 == 1:
            safe_url = html.escape(part, quote=True)
            html_parts.append(f'<a href="{safe_url}">{safe_url}</a>')
        else:
            html_parts.append(html.escape(part))

    return ''.join(html_parts)


def description_to_html_show_notes(description: Optional[str]) -> str:
    """Build lightweight HTML show notes from plain text description."""
    if not description:
        return ""

    lines = str(description).splitlines()
    rendered_lines = []
    for line in lines:
        if not line.strip():
            rendered_lines.append("<br/>")
        else:
            rendered_lines.append(_linkify_text_line(line))

    return '<p>' + '<br/>'.join(rendered_lines) + '</p>'


def generate_github_rss(episodes_data: List[Dict], base_url: str) -> str:
    """Generera RSS-feed.

    Metadata för kanalen hämtas från sources.json (podcastSettings) för att
    ändringar i "Podcast Settings" ska slå igenom i produktion.
    """
    config = load_config() or {}
    ps = (config.get('podcastSettings') or {}) if isinstance(config.get('podcastSettings'), dict) else {}
    maintenance_message = (ps.get('maintenanceMessage') or "").strip()
    podcast_paused = bool(ps.get('paused'))

    channel_title = (ps.get('title') or "MMM Senaste Nytt").strip()
    channel_description = (ps.get('description') or "").strip() or (
        "Dagliga nyheter från världen av människa, maskin och miljö - med Lisa och Pelle. "
        "En del av Människa Maskin Miljö-familjen."
    )
    if podcast_paused and maintenance_message:
        channel_description = maintenance_message
    itunes_author = (ps.get('author') or "").strip() or "Pontus Dahlberg"
    itunes_explicit = bool(ps.get('explicit', False))
    itunes_category = (ps.get('category') or "Technology").strip()
    itunes_email = os.getenv('PODCAST_EMAIL', '').strip() or "podcast@example.com"
    rss_items = []
    
    for episode in episodes_data:
        # Hantera båda gamla (date) och nya (pub_date) format
        if 'pub_date' in episode:
            pub_date = episode['pub_date']  # Redan i rätt format
        elif 'date' in episode:
            pub_date = datetime.strptime(episode['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S +0000')
        else:
            pub_date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Hantera både gamla och nya format för audio URL och storlek
        if 'audio_url' in episode:
            # Nytt format från episodhistorik
            audio_url = episode['audio_url']
            file_size = episode.get('file_size', 7000000)
            guid = episode.get('guid', audio_url)
        else:
            # Gammalt format från direct generation
            audio_url = f"{base_url}/audio/{episode['filename']}"
            file_size = episode.get('size', 7000000)
            guid = audio_url
        
        safe_title = clean_xml_text(episode.get('title', ''))
        raw_description = episode.get('description', '')
        safe_description = clean_xml_text(raw_description)
        safe_summary = clean_xml_text(raw_description)
        content_encoded_html = description_to_html_show_notes(raw_description)
        safe_audio_url = html.escape(audio_url, quote=True)
        safe_guid = clean_xml_text(guid)

        rss_items.append(f"""        <item>
            <title>{safe_title}</title>
            <description>{safe_description}</description>
            <itunes:summary>{safe_summary}</itunes:summary>
            <content:encoded><![CDATA[{content_encoded_html}]]></content:encoded>
            <pubDate>{pub_date}</pubDate>
            <enclosure url="{safe_audio_url}" length="{file_size}" type="audio/mpeg"/>
            <guid>{safe_guid}</guid>
        </item>""")
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
        <title>{clean_xml_text(channel_title)}</title>
        <description>{clean_xml_text(channel_description)}</description>
        <link>{base_url}</link>
        <language>sv-SE</language>
        <itunes:category text="{clean_xml_text(itunes_category)}"/>
        <itunes:explicit>{'true' if itunes_explicit else 'false'}</itunes:explicit>
        <itunes:author>{clean_xml_text(itunes_author)}</itunes:author>
        <itunes:summary>{clean_xml_text(channel_description)}</itunes:summary>
        <itunes:owner>
            <itunes:name>{clean_xml_text(itunes_author)}</itunes:name>
            <itunes:email>{clean_xml_text(itunes_email)}</itunes:email>
        </itunes:owner>
        <itunes:image href="{base_url}/cover.jpg"/>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>"""
    
    return rss_content

def main():
    """Huvudfunktion för komplett podcast-generering med musik och väder"""
    logger.info("[PODCAST] Startar MMM Senaste Nytt med musik och väder...")
    
    # Log Gemini TTS status after logger is initialized
    if GEMINI_TTS_AVAILABLE:
        logger.info("[SYSTEM] Gemini TTS tillgänglig för naturlig dialog")
    else:
        logger.warning("[SYSTEM] Gemini TTS inte tillgänglig - använder standard TTS")

    log_diagnostic('system_tts_capabilities', {
        'gemini_tts_available': bool(GEMINI_TTS_AVAILABLE),
        'gemini_tts_import_error': GEMINI_TTS_IMPORT_ERROR,
    })
    
    # Log Fact Checker status
    if FACT_CHECKER_AVAILABLE:
        logger.info("[SYSTEM] 🛡️ KRITISK faktakontroll-agent aktiverad för säkerhet")
    else:
        logger.error("[SYSTEM] ⚠️ VARNING: Faktakontroll-agent inte tillgänglig - RISK FÖR FELAKTIG INFO!")
    
    try:
        # Hämta väderdata först
        logger.info("[WEATHER] Hämtar aktuell väderdata...")
        weather_info = get_swedish_weather()
        logger.info(f"[WEATHER] {weather_info}")
        
        # Ladda konfiguration
        config = load_config()
        
        # Generera datum och filnamn
        today = datetime.now()
        timestamp = today.strftime('%Y%m%d_%H%M%S')

        # Sätt run-id så att diagnostics kan korreleras mellan moduler
        set_run_id(timestamp)
        os.environ['MMM_RUN_ID'] = timestamp
        
        # Skapa output-mappar
        os.makedirs('audio', exist_ok=True)
        os.makedirs('public/audio', exist_ok=True)
        
        # Generera strukturerat podcast-innehåll med riktig väderdata
        logger.info("[AI] Genererar strukturerat podcast-innehåll...")
        podcast_content, referenced_articles = generate_structured_podcast_content(weather_info, today=today)

        weekday_swedish = SWEDISH_WEEKDAYS.get(today.strftime('%A'), today.strftime('%A'))
        month_swedish = SWEDISH_MONTHS.get(today.month, today.strftime('%B').lower())
        podcast_content = enforce_intro_date(podcast_content, weekday_swedish, today.day, month_swedish)
        
        # Spara manus för referens
        script_path = f"podcast_script_{timestamp}.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(podcast_content)
        logger.info(f"[SCRIPT] Manus sparat: {script_path}")
        
        # Spara artikelreferenser för senare användning
        articles_path = f"episode_articles_{timestamp}.json"
        with open(articles_path, 'w', encoding='utf-8') as f:
            json.dump(referenced_articles, f, indent=2, ensure_ascii=False)
        logger.info(f"[ARTICLES] Artikelreferenser sparade: {articles_path}")
        
        # 🛡️ SJÄLVKORRIGERANDE FAKTAKONTROLL - Automatisk korrigering av problem
        final_podcast_content = podcast_content
        max_correction_attempts = 3

        # Sammanfattning som kan användas i kvalitetsrapport
        fact_check_summary = {
            'status': 'UNKNOWN',
            'warnings': [],
            'critical_issues_count': None,
            'correction_attempts': 0,
            'auto_correct_used': False,
        }
        
        for correction_attempt in range(max_correction_attempts):
            logger.info(f"[FACT-CHECK] 🛡️ Faktakontroll försök {correction_attempt + 1}/{max_correction_attempts}")
            fact_check_summary['correction_attempts'] = correction_attempt + 1
            
            # Grundläggande faktakontroll först (snabbast)
            fact_check_passed = False
            if BASIC_FACT_CHECKER_AVAILABLE:
                basic_checker = BasicFactChecker()
                basic_result = basic_checker.basic_fact_check(final_podcast_content)
                
                if basic_result['safe_to_publish']:
                    # Visa varningar men godkänn ändå
                    warnings = basic_result.get('warnings', [])
                    fact_check_summary['warnings'] = warnings
                    fact_check_summary['critical_issues_count'] = 0
                    if warnings:
                        logger.info(f"[FACT-CHECK] ✅ Faktakontroll godkänd med varningar: {warnings}")
                    else:
                        logger.info("[FACT-CHECK] ✅ Faktakontroll godkänd helt")
                    fact_check_summary['status'] = 'SAFE'
                    fact_check_passed = True
                    break
                else:
                    critical_issues = basic_result.get('critical_issues', [])
                    warnings = basic_result.get('warnings', [])
                    fact_check_summary['warnings'] = warnings
                    fact_check_summary['critical_issues_count'] = len(critical_issues)
                    fact_check_summary['status'] = 'REQUIRES_REVIEW'
                    logger.error(f"[FACT-CHECK] ❌ Kritiska problem hittade: {critical_issues}")
                    if warnings:
                        logger.info(f"[FACT-CHECK] ℹ️ Varningar (blockerar inte): {warnings}")
                    
                    # Försök automatisk korrigering
                    if SELF_CORRECTING_AVAILABLE and correction_attempt < max_correction_attempts - 1:
                        logger.info("[FACT-CHECK] 🔧 Startar automatisk korrigering...")
                        
                        corrected_content, correction_success = auto_correct_podcast_content(
                            final_podcast_content, basic_result.get('critical_issues', [])
                        )
                        
                        if correction_success:
                            logger.info("[FACT-CHECK] ✅ Automatisk korrigering lyckades!")
                            final_podcast_content = corrected_content
                            fact_check_summary['auto_correct_used'] = True
                            
                            # Spara korrigerat manus
                            corrected_script_path = f"podcast_script_{timestamp}_corrected_v{correction_attempt + 1}.txt"
                            with open(corrected_script_path, 'w', encoding='utf-8') as f:
                                f.write(final_podcast_content)
                            logger.info(f"[SCRIPT] Korrigerat manus sparat: {corrected_script_path}")
                            continue
                        else:
                            logger.warning("[FACT-CHECK] ⚠️ Automatisk korrigering misslyckades")
                    else:
                        logger.warning("[FACT-CHECK] ⚠️ Självkorrigering inte tillgänglig")
            
            # Om vi når hit har korrigering misslyckats eller är sista försöket
            break
        
        # Final kontroll
        if not fact_check_passed:
            logger.error("🚨 PUBLICERING STOPPAD - FAKTAKONTROLL MISSLYCKADES!")
            fact_check_summary['status'] = 'FAILED'
            
            # Spara rapport för manuell granskning
            final_report_path = f"fact_check_failed_{timestamp}.txt"
            with open(final_report_path, 'w', encoding='utf-8') as f:
                f.write("FAKTAKONTROLL MISSLYCKADES\n")
                f.write(f"Datum: {datetime.now().isoformat()}\n")
                f.write(f"Försök gjorda: {correction_attempt + 1}\n\n")
                if 'basic_result' in locals():
                    f.write("SENASTE PROBLEM:\n")
                    for issue in basic_result['issues_found']:
                        f.write(f"- {issue}\n")
            
            print(f"\n🚨 SÄKERHETSVARNING: Automatisk korrigering misslyckades!")
            print(f"Rapport sparad: {final_report_path}")
            print("Manuell granskning krävs. Se MANUAL_FACT_CHECK_GUIDE.md")
            return False
        else:
            logger.info("[FACT-CHECK] ✅ Faktakontroll godkänd - säkert att publicera")
            # Uppdatera innehållet om det korrigerades
            if final_podcast_content != podcast_content:
                logger.info("[FACT-CHECK] 📝 Använder automatiskt korrigerat innehåll")
                podcast_content = final_podcast_content

        podcast_content = cleanup_generated_dialogue(podcast_content)
        
        # Parsa innehållet i segment
        segments = parse_podcast_text(podcast_content)
        logger.info(f"[PARSE] Hittade {len(segments)} segment att generera audio för")
        
        # Räkna ord för att uppskatta längd
        total_words = sum(len(segment['text'].split()) for segment in segments)
        estimated_minutes = total_words / 150  # Ungefär 150 ord per minut i tal
        logger.info(f"[ESTIMATE] {total_words} ord, uppskattad längd: {estimated_minutes:.1f} minuter")
        
        # Generera filnamn
        audio_filename = f"MMM_senaste_nytt_{timestamp}.mp3"
        audio_filepath = os.path.join('audio', audio_filename)

        tts_provider, tts_resolution = _resolve_tts_provider()
        logger.info(
            "[TTS] Aktiv provider: %s (reason=%s, configured=%s, gemini_available=%s)",
            tts_provider,
            tts_resolution['reason'],
            tts_resolution['configured_provider'] or 'unset',
            tts_resolution['gemini_available'],
        )
        log_diagnostic('tts_provider_attempt', {
            'provider': tts_provider,
            'output_file': audio_filepath,
            'require_gemini': tts_resolution['require_gemini'],
            'reason': tts_resolution['reason'],
            'configured_provider': tts_resolution['configured_provider'],
            'gemini_available': tts_resolution['gemini_available'],
        })

        if tts_provider == 'gemini':
            gemini_success = generate_audio_with_gemini_dialog(podcast_content, weather_info, audio_filepath)
            log_diagnostic('tts_provider_result', {
                'provider': 'gemini',
                'success': bool(gemini_success),
                'error': _LAST_GEMINI_ERROR if not gemini_success else None,
            })
            if not gemini_success:
                logger.error("[ERROR] Gemini TTS misslyckades")
                return False
            logger.info("[TTS] ✅ Naturlig dialog genererad med Gemini TTS!")
        else:
            success = generate_audio_google_cloud(segments, audio_filepath)
            log_diagnostic('tts_provider_result', {
                'provider': 'google_cloud',
                'success': bool(success),
            })
            if not success:
                logger.error("[ERROR] Audio-generering misslyckades")
                return False
        
        # Lägg till musik och bryggkor
        audio_filepath = add_music_to_podcast(audio_filepath)
        
        # Kopiera till public/audio för GitHub Pages
        public_audio_path = os.path.join('public', 'audio', audio_filename)
        shutil.copy2(audio_filepath, public_audio_path)
        logger.info(f"[FILES] Kopierade audio till {public_audio_path}")
        
        # Skapa episode data med artiklar som faktiskt refererades i avsnittet
        file_size = os.path.getsize(audio_filepath)
        
        # För RSS: lista bara källor som sannolikt faktiskt nämns i manuset
        logger.info(f"[RSS] Antal kandidat-artiklar: {len(referenced_articles)}")

        rss_referenced_articles = extract_referenced_articles(podcast_content, referenced_articles, max_results=6)
        logger.info(f"[RSS] Antal matchade artiklar i manus: {len(rss_referenced_articles)}")

        if not rss_referenced_articles and referenced_articles:
            logger.warning("[RSS] 0 matchade artiklar i manus; faller tillbaka till topp-kandidater för källor i beskrivningen")
            log_diagnostic('rss_sources_fallback_used', {
                'candidate_count': len(referenced_articles),
                'fallback_count': min(6, len(referenced_articles)),
            })
            rss_referenced_articles = referenced_articles[:6]

        # Diagnostics: visa vilka som inte matchades (hjälper felsöka "källor som inte var med")
        try:
            matched_keys = set()
            for a in rss_referenced_articles:
                key = _canonicalize_url(a.get('link', '')) or _title_fingerprint(a.get('title', ''))
                if key:
                    matched_keys.add(key)

            unmatched = []
            for a in referenced_articles:
                key = _canonicalize_url(a.get('link', '')) or _title_fingerprint(a.get('title', ''))
                if key and key not in matched_keys:
                    unmatched.append({'source': a.get('source', ''), 'title': a.get('title', ''), 'link': a.get('link', '')})

            if unmatched:
                log_diagnostic('rss_sources_unmatched', {
                    'candidate_count': len(referenced_articles),
                    'matched_count': len(rss_referenced_articles),
                    'unmatched_count': len(unmatched),
                    'examples': unmatched[:10],
                })
        except Exception:
            pass

        article_links = []
        for i, article in enumerate(rss_referenced_articles):
            logger.info(f"[RSS] Artikel {i+1}: {article.get('source', 'N/A')} - {article.get('title', 'N/A')[:50]}...")
            if article.get('link') and article.get('title'):
                short_title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                source_name = article.get('source', 'Okänd källa')
                article_links.append(f"{source_name}: {short_title}\n{article['link']}")
        
        sources_text = ""
        if article_links:
            sources_text = f"\n\nKällor som refereras i detta avsnitt:\n• " + "\n• ".join(article_links)
            logger.info(f"[RSS] Lade till {len(article_links)} källor i RSS-beskrivning")
        else:
            logger.warning("[RSS] Inga källor att visa i RSS-beskrivning!")
        
        month_swedish = SWEDISH_MONTHS[today.month]
        weekday_swedish = SWEDISH_WEEKDAYS.get(today.strftime('%A'), today.strftime('%A'))
        
        episode_data = {
            'title': f"MMM Senaste Nytt - {today.day} {month_swedish} {today.year}",
            'description': f"Dagens nyheter inom AI, teknik och klimat - {weekday_swedish} den {today.day} {month_swedish} {today.year}. Med detaljerade källhänvisningar från svenska och internationella medier.{sources_text}",
            'date': today.strftime('%Y-%m-%d'),
            'filename': audio_filename,
            'size': file_size,
            'duration': f"{estimated_minutes:.0f}:00"
        }
        
        # Lägg till episod till historik och generera RSS-feed med alla episoder
        logger.info("[HISTORY] Lägger till episod till historik...")
        history = EpisodeHistory()
        all_episodes = history.add_episode(episode_data)
        
        # Generera RSS-feed med alla episoder (max 10 senaste för RSS-prestanda)
        base_url = "https://pontusdahlberg.github.io/morgonpodden"
        recent_episodes = all_episodes[:10]  # Ta bara 10 senaste för RSS-feed
        rss_content = generate_github_rss(recent_episodes, base_url)
        
        # Spara RSS-feed
        rss_path = os.path.join('public', 'feed.xml')
        with open(rss_path, 'w', encoding='utf-8') as f:
            f.write(rss_content)
        logger.info(f"[RSS] RSS-feed sparad med {len(recent_episodes)} episoder: {rss_path}")

        # ============================================================
        # KVALITETSRAPPORT (relevans/korrekthet/körningsproblem)
        # ============================================================
        try:
            from src.episode_quality import generate_episode_quality_report, write_quality_reports

            scraped_data_for_report = None
            try:
                with open('scraped_content.json', 'r', encoding='utf-8') as f:
                    scraped_data_for_report = json.load(f)
            except Exception:
                scraped_data_for_report = None

            quality_report = generate_episode_quality_report(
                run_id=timestamp,
                script_text=podcast_content,
                referenced_articles=referenced_articles,
                scraped_content=scraped_data_for_report,
                diagnostics_file=DIAGNOSTICS_FILE,
                fact_check_summary=fact_check_summary,
            )
            paths = write_quality_reports(report=quality_report, output_dir='episodes')
            logger.info(f"[QUALITY] Rapport sparad: {paths.get('markdown')} | {paths.get('json')}")

            # Valfritt: mejla rapporten om SMTP/MMM_REPORT_EMAIL_* är konfigurerat
            try:
                from src.report_emailer import maybe_email_quality_report

                diag_max_env = os.getenv('MMM_EMAIL_DIAG_MAX_LINES', '').strip()
                log_tail_env = os.getenv('MMM_EMAIL_LOG_TAIL_LINES', '').strip()
                try:
                    diag_max_lines = int(diag_max_env) if diag_max_env else 2000
                except ValueError:
                    diag_max_lines = 2000
                try:
                    log_tail_lines = int(log_tail_env) if log_tail_env else 600
                except ValueError:
                    log_tail_lines = 600

                diag_extract = _write_run_diagnostics_extract(
                    run_id=timestamp,
                    diagnostics_file=DIAGNOSTICS_FILE,
                    output_dir='episodes',
                    max_lines=max(200, diag_max_lines),
                )
                log_tail = _write_log_tail(
                    run_id=timestamp,
                    log_path='podcast_generation.log',
                    output_dir='episodes',
                    max_lines=max(200, log_tail_lines),
                )

                extra_attachments = [p for p in [diag_extract, log_tail] if p]

                emailed = maybe_email_quality_report(
                    run_id=timestamp,
                    markdown_path=paths.get('markdown'),
                    json_path=paths.get('json'),
                    extra_attachments=extra_attachments,
                )
                if emailed:
                    logger.info("[QUALITY] ✅ Kvalitetsrapport mejlad")
            except Exception as e:
                logger.warning(f"[QUALITY] Kunde inte mejla kvalitetsrapport: {e}")
        except Exception as e:
            logger.warning(f"[QUALITY] Kunde inte skapa kvalitetsrapport: {e}")
        
        # Logga framgång
        logger.info("[SUCCESS] Komplett podcast-generering slutförd!")
        logger.info(f"[AUDIO] Audio: {audio_filepath}")
        logger.info(f"[SCRIPT] Manus: {script_path}")
        logger.info(f"[RSS] RSS: {rss_path}")
        logger.info(f"[WEATHER] Väder: {weather_info}")
        logger.info(f"[STATS] Segment: {len(segments)}, Ord: {total_words}, Längd: ~{estimated_minutes:.1f} min")
        logger.info(f"[GITHUB] GitHub Pages URL: {base_url}")
        logger.info(f"[FEED] RSS URL: {base_url}/feed.xml")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Oväntat fel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
        if any(arg in {'-h', '--help'} for arg in sys.argv[1:]):
                print(
                        """Usage:
    python run_podcast_complete.py

Genererar MMM Senaste Nytt (nyheter + väder + TTS + musik + RSS).

Valfria env vars (felsökning):
    MMM_FORCE_GEMINI_TTS=1
        - Avbryter körningen om Gemini-TTS misslyckas (ingen tyst fallback).

    GEMINI_TTS_PROMPT_MAX_BYTES=850
        - Maxstorlek för prompt (UTF-8 bytes).

    GEMINI_TTS_MAX_BYTES=3900
        - Maxstorlek per chunk i TTS-input (UTF-8 bytes).
"""
                )
                sys.exit(0)

        success = main()
        sys.exit(0 if success else 1)