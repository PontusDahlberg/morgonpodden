import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


_DEFAULT_HISTORY_PATH = "news_history.json"


_TITLE_STOPWORDS = {
    "och", "att", "det", "som", "för", "från", "med", "till", "har", "här", "den", "detta",
    "samt", "även", "inte", "mer", "mot", "nya", "ny", "nu", "idag", "i", "på", "av",
    "en", "ett", "om", "ur", "vid", "efter", "under", "över", "kring", "sin", "sitt", "sina",
    "sverige", "svenska", "stockholm", "göteborg", "malmö",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonicalize_url(url: str) -> str:
    """Create a stable key for URLs by removing common tracking parameters."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        query_pairs = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
            and k.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
        ]
        cleaned = parsed._replace(query=urlencode(query_pairs, doseq=True), fragment="")
        normalized = urlunparse(cleaned).rstrip("/")
        return normalized
    except Exception:
        return url.strip().rstrip("/")


def title_fingerprint(title: str) -> str:
    if not title:
        return ""
    text = title.lower()
    text = re.sub(r"[^\w\såäöÅÄÖ-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [
        t
        for t in text.split(" ")
        if len(t) >= 4 and t not in _TITLE_STOPWORDS and not t.isdigit()
    ]
    if not tokens:
        return ""
    tokens = sorted(set(tokens))
    return " ".join(tokens[:12])


def is_weather_source(source_type: str) -> bool:
    return (source_type or "").lower() == "weather"


def is_follow_up_text(title: str, summary: str) -> bool:
    """Heuristic: allow some repeats if clearly framed as new development."""
    text = f"{title} {summary}".lower()
    markers = [
        "uppdater", "uppfölj", "nya uppgifter", "fortsatt", "ytterligare",
        "rättegång", "dom", "dömd", "åtal", "utred",
        "follow-up", "update", "new details",
    ]
    return any(m in text for m in markers)


@dataclass
class DedupeStats:
    total_items_in: int
    total_items_out: int
    skipped_repeats: int
    sources: Dict[str, Dict[str, int]]


class NewsHistory:
    def __init__(self, path: str = _DEFAULT_HISTORY_PATH):
        self.path = path
        self.data: Dict[str, Any] = {"version": 1, "items": {}}

    def load(self) -> None:
        if not os.path.exists(self.path):
            self.data = {"version": 1, "items": {}}
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            if not isinstance(self.data, dict) or "items" not in self.data:
                self.data = {"version": 1, "items": {}}
        except Exception:
            self.data = {"version": 1, "items": {}}

    def save(self) -> None:
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)

    def prune(self, keep_days: int = 60) -> int:
        items = self.data.get("items", {})
        if not isinstance(items, dict):
            self.data["items"] = {}
            return 0

        cutoff = _utc_now() - timedelta(days=keep_days)
        removed = 0
        for k in list(items.keys()):
            try:
                last_seen = datetime.fromisoformat(items[k].get("last_seen"))
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                if last_seen < cutoff:
                    items.pop(k, None)
                    removed += 1
            except Exception:
                items.pop(k, None)
                removed += 1
        return removed

    def seen_within_days(self, key: str, days: int) -> bool:
        if not key:
            return False
        items = self.data.get("items", {})
        if not isinstance(items, dict) or key not in items:
            return False
        try:
            last_seen = datetime.fromisoformat(items[key].get("last_seen"))
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            return last_seen >= (_utc_now() - timedelta(days=days))
        except Exception:
            return False

    def mark_seen(self, keys: List[str]) -> None:
        items = self.data.setdefault("items", {})
        if not isinstance(items, dict):
            self.data["items"] = {}
            items = self.data["items"]

        now = _utc_now().isoformat()
        for key in keys:
            if not key:
                continue
            entry = items.get(key)
            if not isinstance(entry, dict):
                items[key] = {"first_seen": now, "last_seen": now, "count": 1}
            else:
                entry["last_seen"] = now
                entry["count"] = int(entry.get("count", 0)) + 1


def filter_scraped_data_for_freshness(
    scraped_data: List[Dict[str, Any]],
    history_path: str = _DEFAULT_HISTORY_PATH,
    dedupe_days: int = 21,
    retain_days: int = 60,
    allow_followups: bool = True,
) -> Tuple[List[Dict[str, Any]], DedupeStats]:
    history = NewsHistory(history_path)
    history.load()
    history.prune(keep_days=retain_days)

    total_in = 0
    total_out = 0
    skipped = 0
    per_source: Dict[str, Dict[str, int]] = {}

    filtered: List[Dict[str, Any]] = []

    for source_group in scraped_data or []:
        source_name = source_group.get("source", "Unknown")
        source_type = source_group.get("type", "")
        items = source_group.get("items", []) or []

        total_in += len(items)
        per_source.setdefault(source_name, {"in": 0, "out": 0, "skipped": 0})
        per_source[source_name]["in"] += len(items)

        if is_weather_source(source_type):
            filtered.append(source_group)
            total_out += len(items)
            per_source[source_name]["out"] += len(items)
            continue

        kept_items: List[Dict[str, Any]] = []
        used_keys_to_mark: List[str] = []

        for item in items:
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip()
            summary = (item.get("summary") or "").strip()

            url_key = canonicalize_url(link)
            fp = title_fingerprint(title)

            key_url = f"url:{url_key}" if url_key else ""
            key_title = f"title:{fp}" if fp else ""

            is_repeat = (
                (key_url and history.seen_within_days(key_url, dedupe_days))
                or (key_title and history.seen_within_days(key_title, dedupe_days))
            )

            followup_ok = allow_followups and is_follow_up_text(title, summary)

            if is_repeat and not followup_ok:
                skipped += 1
                per_source[source_name]["skipped"] += 1
                continue

            kept_items.append(item)
            if key_url:
                used_keys_to_mark.append(key_url)
            if key_title:
                used_keys_to_mark.append(key_title)

        # If we filtered everything for a source, keep at least one item (best-effort)
        if not kept_items and items:
            kept_items = [items[0]]
            title = (items[0].get("title") or "").strip()
            link = (items[0].get("link") or "").strip()
            summary = (items[0].get("summary") or "").strip()
            url_key = canonicalize_url(link)
            fp = title_fingerprint(title)
            key_url = f"url:{url_key}" if url_key else ""
            key_title = f"title:{fp}" if fp else ""
            if key_url:
                used_keys_to_mark.append(key_url)
            if key_title:
                used_keys_to_mark.append(key_title)

        history.mark_seen(used_keys_to_mark)

        new_group = dict(source_group)
        new_group["items"] = kept_items
        filtered.append(new_group)

        total_out += len(kept_items)
        per_source[source_name]["out"] += len(kept_items)

    history.save()

    return filtered, DedupeStats(
        total_items_in=total_in,
        total_items_out=total_out,
        skipped_repeats=skipped,
        sources=per_source,
    )
