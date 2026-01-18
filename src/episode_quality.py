import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


_TITLE_STOPWORDS = {
    'och', 'eller', 'men', 'att', 'som', 'det', 'den', 'detta', 'dessa', 'en', 'ett', 'i', 'på', 'av', 'till',
    'för', 'med', 'utan', 'över', 'under', 'efter', 'före', 'om', 'när', 'där', 'här', 'från', 'mot',
    'säger', 'sa', 'uppger', 'enligt', 'nya', 'ny', 'nu', 'idag', 'igår', 'imorgon',
    'the', 'a', 'an', 'and', 'or', 'but', 'to', 'of', 'in', 'on', 'for', 'with', 'from', 'by', 'as', 'at',
}


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _title_fingerprint(title: str) -> str:
    if not title:
        return ""
    text = title.lower()
    text = re.sub(r"[^\w\såäöÅÄÖ-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split(" ") if len(t) >= 4 and t not in _TITLE_STOPWORDS and not t.isdigit()]
    if not tokens:
        return ""
    tokens = sorted(set(tokens))
    return " ".join(tokens[:12])


def _infer_sport_label(title: str, link: str) -> Optional[str]:
    title_l = (title or "").lower()
    link_l = (link or "").lower()

    # Prefer explicit sport words in title
    sport_keywords = [
        ("bandy", "bandy"),
        ("fotboll", "fotboll"),
        ("ishockey", "ishockey"),
        ("hockey", "ishockey"),
        ("handboll", "handboll"),
        ("curling", "curling"),
        ("skidskytte", "skidskytte"),
        ("alpint", "alpint"),
        ("friidrott", "friidrott"),
        ("tennis", "tennis"),
        ("golf", "golf"),
        ("basket", "basket"),
        ("innebandy", "innebandy"),
    ]
    for kw, label in sport_keywords:
        if kw in title_l:
            return label

    # Fallback: infer from SVT-style URL path: /sport/<gren>/...
    if "/sport/" in link_l:
        try:
            after = link_l.split("/sport/", 1)[1]
            candidate = after.split("/", 1)[0].strip()
            if candidate in {"fotboll", "bandy", "handboll", "ishockey", "hockey", "curling", "friidrott", "alpint", "skidskytte"}:
                return "ishockey" if candidate == "hockey" else candidate
        except Exception:
            return None

    return None


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []

    def _iter() -> Iterable[Dict[str, Any]]:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    return _iter()


def _extract_script_flags(script_text: str) -> Dict[str, Any]:
    text = script_text or ""
    flags: Dict[str, Any] = {
        'word_count': len(text.split()),
        'contains_svt_js_disabled_leak': bool(re.search(r"javascript är avstängt", text, re.I)),
        'contains_placeholder_music': bool(re.search(r"\[MUSIK:\s*[^\]]*\]", text)),
    }
    return flags


def _summarize_diagnostics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        'events_total': len(entries),
        'dedupe': {
            'skipped_repeat_count': 0,
            'remaining_article_count': None,
        },
        'tts': {
            'attempts': [],
            'results': [],
            'fallbacks': [],
            'final_provider': None,
            'final_success': None,
        },
        'rss': {
            'candidate_count': None,
            'matched_count': None,
            'unmatched_count': None,
        },
    }

    for e in entries:
        ev = e.get('event')
        if ev == 'article_skipped_repeat':
            summary['dedupe']['skipped_repeat_count'] += 1
        elif ev == 'dedupe_summary':
            summary['dedupe']['skipped_repeat_count'] = _safe_int(e.get('skipped_repeat_count')) or summary['dedupe']['skipped_repeat_count']
            summary['dedupe']['remaining_article_count'] = _safe_int(e.get('remaining_article_count'))
        elif ev == 'tts_provider_attempt':
            summary['tts']['attempts'].append({
                'provider': e.get('provider'),
                'output_file': e.get('output_file'),
                'require_gemini': e.get('require_gemini'),
            })
        elif ev == 'tts_provider_result':
            summary['tts']['results'].append({
                'provider': e.get('provider'),
                'success': e.get('success'),
                'error': e.get('error'),
            })
            summary['tts']['final_provider'] = e.get('provider')
            summary['tts']['final_success'] = e.get('success')
        elif ev == 'tts_provider_fallback':
            summary['tts']['fallbacks'].append({
                'from_provider': e.get('from_provider'),
                'to_provider': e.get('to_provider'),
            })
        elif ev == 'rss_sources_unmatched':
            summary['rss']['candidate_count'] = _safe_int(e.get('candidate_count'))
            summary['rss']['matched_count'] = _safe_int(e.get('matched_count'))
            summary['rss']['unmatched_count'] = _safe_int(e.get('unmatched_count'))

    return summary


def _analyze_news_items(referenced_articles: List[Dict[str, Any]], script_text: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    script_lines = (script_text or "").splitlines()
    script_lower = script_text.lower() if script_text else ""

    items_out: List[Dict[str, Any]] = []
    relevance_scores: List[int] = []
    category_counts: Dict[str, int] = {}
    category_group_counts_all: Dict[str, int] = {'climate_environment': 0, 'tech_ai': 0, 'other': 0}
    category_group_counts_referenced: Dict[str, int] = {'climate_environment': 0, 'tech_ai': 0, 'other': 0}
    sport_mismatch_warnings: List[Dict[str, Any]] = []

    def category_to_group(category: str) -> str:
        cat = (category or '').strip().lower()

        # Agent-systemets kategorier (se news_agent_system.NewsCategory)
        climate_env = {
            'climate_sweden', 'climate_global',
            'environment_sweden', 'environment_global',
            # Tech med klimatkoppling ska räknas som klimat/miljö för 50%-kravet
            'tech_climate',
        }
        tech_ai = {'tech_ai', 'tech_general'}

        if cat in climate_env:
            return 'climate_environment'
        if cat in tech_ai:
            return 'tech_ai'
        return 'other'

    for a in referenced_articles or []:
        title = (a.get('title') or '').strip()
        source = (a.get('source') or '').strip()
        link = (a.get('link') or '').strip()
        category = (a.get('category') or '').strip() or 'unknown'
        rs = _safe_int(a.get('relevance_score'))
        if rs is not None:
            relevance_scores.append(rs)

        category_counts[category] = category_counts.get(category, 0) + 1

        group = category_to_group(category)
        category_group_counts_all[group] = category_group_counts_all.get(group, 0) + 1

        fp = _title_fingerprint(title)
        fp_tokens = fp.split(' ') if fp else []

        # Simple “is it actually in the script” check (line-level)
        referenced_in_script = False
        matched_lines: List[str] = []
        if fp_tokens:
            for ln in script_lines:
                ln_l = ln.lower()
                token_hits = sum(1 for t in fp_tokens if t and t in ln_l)
                if token_hits >= 2:
                    referenced_in_script = True
                    matched_lines.append(ln.strip())
                    if len(matched_lines) >= 3:
                        break

        sport_label = _infer_sport_label(title, link)

        # Sport mismatch heuristic: if this specific article seems referenced on a line
        # and that line contains another sport word.
        if referenced_in_script and sport_label in {"bandy", "fotboll", "ishockey", "handboll", "innebandy"}:
            for ln in matched_lines:
                ln_l = ln.lower()
                if sport_label == 'bandy' and 'fotboll' in ln_l:
                    sport_mismatch_warnings.append({
                        'title': title,
                        'expected': 'bandy',
                        'found': 'fotboll',
                        'line': ln,
                    })
                if sport_label == 'fotboll' and 'bandy' in ln_l:
                    sport_mismatch_warnings.append({
                        'title': title,
                        'expected': 'fotboll',
                        'found': 'bandy',
                        'line': ln,
                    })

        items_out.append({
            'source': source,
            'title': title,
            'link': link,
            'category': category,
            'relevance_score': rs,
            'sport_label': sport_label,
            'referenced_in_script': referenced_in_script,
            'match_examples': matched_lines,
        })

        if referenced_in_script:
            category_group_counts_referenced[group] = category_group_counts_referenced.get(group, 0) + 1

    # Quick global warning: script talks about football but no football stories in refs
    has_fotboll_in_script = 'fotboll' in script_lower
    has_fotboll_story = any(i.get('sport_label') == 'fotboll' for i in items_out)
    has_bandy_story = any(i.get('sport_label') == 'bandy' for i in items_out)

    total_all = sum(category_group_counts_all.values())
    total_ref = sum(category_group_counts_referenced.values())

    def to_percent(count: int, total: int) -> Optional[float]:
        if not total:
            return None
        return round((count / total) * 100.0, 1)

    climate_target_min = 50.0
    climate_share_all = to_percent(category_group_counts_all.get('climate_environment', 0), total_all)
    climate_share_ref = to_percent(category_group_counts_referenced.get('climate_environment', 0), total_ref)

    global_flags: Dict[str, Any] = {
        'avg_relevance_score': (sum(relevance_scores) / len(relevance_scores)) if relevance_scores else None,
        'min_relevance_score': min(relevance_scores) if relevance_scores else None,
        'max_relevance_score': max(relevance_scores) if relevance_scores else None,
        'category_counts': category_counts,
        'category_group_counts_all': category_group_counts_all,
        'category_group_counts_referenced': category_group_counts_referenced,
        'category_group_percent_all': {
            k: to_percent(v, total_all) for k, v in category_group_counts_all.items()
        },
        'category_group_percent_referenced': {
            k: to_percent(v, total_ref) for k, v in category_group_counts_referenced.items()
        },
        'climate_minimum_target_percent': climate_target_min,
        'climate_share_percent_all': climate_share_all,
        'climate_share_percent_referenced': climate_share_ref,
        'meets_climate_minimum_all': None if climate_share_all is None else (climate_share_all >= climate_target_min),
        'meets_climate_minimum_referenced': None if climate_share_ref is None else (climate_share_ref >= climate_target_min),
        'sport_mismatch_warnings': sport_mismatch_warnings,
        'script_mentions_fotboll_without_fotboll_story': bool(has_fotboll_in_script and not has_fotboll_story and has_bandy_story),
    }

    return items_out, global_flags


@dataclass
class EpisodeQualityReport:
    run_id: str
    created_at: str
    inputs: Dict[str, Any]
    script: Dict[str, Any]
    diagnostics: Dict[str, Any]
    news_items: List[Dict[str, Any]]
    news_summary: Dict[str, Any]
    fact_check: Dict[str, Any]
    grades: Dict[str, Any]


def generate_episode_quality_report(
    *,
    run_id: str,
    script_text: str,
    referenced_articles: List[Dict[str, Any]],
    scraped_content: Optional[List[Dict[str, Any]]] = None,
    diagnostics_file: str = 'diagnostics.jsonl',
    fact_check_summary: Optional[Dict[str, Any]] = None,
) -> EpisodeQualityReport:
    fact_check_summary = fact_check_summary or {}

    diag_entries = [e for e in _read_jsonl(diagnostics_file) if e.get('run_id') == run_id]
    diag_summary = _summarize_diagnostics(diag_entries)
    script_flags = _extract_script_flags(script_text)
    news_items, news_summary = _analyze_news_items(referenced_articles, script_text)

    # Scrape summary is “nice to have” but not required
    scrape_summary: Dict[str, Any] = {}
    if isinstance(scraped_content, list):
        sources_total = len(scraped_content)
        sources_with_items = sum(1 for g in scraped_content if (g.get('items') or []))
        empty_sources = [g.get('source', 'Okänd') for g in scraped_content if not (g.get('items') or [])]
        total_items = sum(len(g.get('items') or []) for g in scraped_content)
        scrape_summary = {
            'sources_total': sources_total,
            'sources_with_items': sources_with_items,
            'sources_empty': empty_sources[:25],
            'total_items': total_items,
        }

    # Simple grading (transparent + conservative):
    # - correctness penalized by fact-check issues + obvious leakage + sport mismatch warnings
    # - relevance approximated by avg relevance score if present
    correctness_penalty = 0
    if script_flags.get('contains_svt_js_disabled_leak'):
        correctness_penalty += 20
    if news_summary.get('sport_mismatch_warnings'):
        correctness_penalty += 25
    if fact_check_summary.get('status') in {'REQUIRES_REVIEW', 'FAILED'}:
        correctness_penalty += 40
    if diag_summary.get('tts', {}).get('final_success') is False:
        correctness_penalty += 30

    correctness_score = max(0, 100 - correctness_penalty)
    relevance_score = news_summary.get('avg_relevance_score')
    relevance_score = int(relevance_score) if isinstance(relevance_score, (int, float)) else None

    grades = {
        'relevance': {
            'score_0_100': relevance_score,
            'basis': 'avg(relevance_score) from agent curation' if relevance_score is not None else 'no relevance_score present in referenced_articles',
        },
        'correctness': {
            'score_0_100': correctness_score,
            'penalty_points': correctness_penalty,
        },
    }

    return EpisodeQualityReport(
        run_id=run_id,
        created_at=datetime.now().isoformat(timespec='seconds'),
        inputs={
            'diagnostics_file': diagnostics_file,
            'scrape_summary': scrape_summary,
            'referenced_articles_count': len(referenced_articles or []),
        },
        script=script_flags,
        diagnostics=diag_summary,
        news_items=news_items,
        news_summary=news_summary,
        fact_check=fact_check_summary,
        grades=grades,
    )


def _render_markdown(report: EpisodeQualityReport) -> str:
    d = report.diagnostics
    tts = d.get('tts', {})
    rss = d.get('rss', {})
    dedupe = d.get('dedupe', {})

    rel = report.grades.get('relevance', {})
    corr = report.grades.get('correctness', {})
    avg_rel = rel.get('score_0_100')
    corr_score = corr.get('score_0_100')

    lines: List[str] = []
    lines.append(f"# Kvalitetsrapport")
    lines.append("")
    lines.append(f"**Run ID**: {report.run_id}")
    lines.append(f"**Skapad**: {report.created_at}")
    lines.append("")
    lines.append("## Betyg")
    lines.append(f"- Relevans: {avg_rel if avg_rel is not None else 'N/A'}/100")
    lines.append(f"- Korrekthet: {corr_score}/100")

    lines.append("")
    lines.append("## Körning")
    lines.append(f"- Manus: {report.script.get('word_count')} ord")
    if report.script.get('contains_svt_js_disabled_leak'):
        lines.append("- Varning: 'Javascript är avstängt' läckte in i manus")

    lines.append(f"- Dedupe: hoppade över {dedupe.get('skipped_repeat_count', 0)} upprepade artiklar")

    if tts.get('final_provider') is not None:
        lines.append(f"- TTS: {tts.get('final_provider')} (success={tts.get('final_success')})")
    if tts.get('fallbacks'):
        lines.append(f"- TTS fallback: {tts.get('fallbacks')}")

    if rss.get('candidate_count') is not None:
        lines.append(f"- RSS-källor matchade: {rss.get('matched_count')}/{rss.get('candidate_count')} (unmatched={rss.get('unmatched_count')})")

    lines.append("")
    lines.append("## Nyhetsinslag")
    lines.append(f"- Antal kandidatinslag: {report.inputs.get('referenced_articles_count')}")
    lines.append(f"- Kategorier: {report.news_summary.get('category_counts', {})}")

    group_pct_all = report.news_summary.get('category_group_percent_all', {})
    group_pct_ref = report.news_summary.get('category_group_percent_referenced', {})
    climate_min = report.news_summary.get('climate_minimum_target_percent')
    climate_all = report.news_summary.get('climate_share_percent_all')
    climate_ref = report.news_summary.get('climate_share_percent_referenced')
    meets_all = report.news_summary.get('meets_climate_minimum_all')
    meets_ref = report.news_summary.get('meets_climate_minimum_referenced')

    def fmt_pct(value: Any) -> str:
        return 'N/A' if value is None else f"{value}%"

    if group_pct_all:
        lines.append(
            "- Fördelning (alla valda): "
            f"klimat/miljö={fmt_pct(group_pct_all.get('climate_environment'))}, "
            f"tech/AI={fmt_pct(group_pct_all.get('tech_ai'))}, "
            f"övrigt={fmt_pct(group_pct_all.get('other'))}"
        )

    ref_counts = report.news_summary.get('category_group_counts_referenced', {})
    if group_pct_ref and isinstance(ref_counts, dict) and sum((ref_counts.get(k, 0) or 0) for k in ref_counts.keys()) > 0:
        lines.append(
            "- Fördelning (verifierat i manus): "
            f"klimat/miljö={fmt_pct(group_pct_ref.get('climate_environment'))}, "
            f"tech/AI={fmt_pct(group_pct_ref.get('tech_ai'))}, "
            f"övrigt={fmt_pct(group_pct_ref.get('other'))}"
        )

    # Flagga om klimat/miljö-andelen understiger målet
    if climate_min is not None and climate_all is not None and meets_all is False:
        lines.append(f"- Varning: klimat/miljö-andel under mål ({climate_all}% < {climate_min}%)")
    if climate_min is not None and climate_ref is not None and meets_ref is False:
        lines.append(f"- Varning: klimat/miljö-andel i manus under mål ({climate_ref}% < {climate_min}%)")
    if report.news_summary.get('sport_mismatch_warnings'):
        lines.append("")
        lines.append("### Sport-varningar")
        for w in report.news_summary.get('sport_mismatch_warnings', [])[:10]:
            lines.append(f"- Möjlig sport-mismatch: '{w.get('title')}' (förväntade {w.get('expected')}, hittade {w.get('found')})")

    lines.append("")
    lines.append("## Faktakontroll")
    if report.fact_check:
        lines.append(f"- Status: {report.fact_check.get('status')}")
        if report.fact_check.get('warnings'):
            lines.append(f"- Varningar: {report.fact_check.get('warnings')}")
        if report.fact_check.get('critical_issues_count') is not None:
            lines.append(f"- Kritiska issues: {report.fact_check.get('critical_issues_count')}")
    else:
        lines.append("- Ingen faktakontroll-sammanfattning tillgänglig")

    lines.append("")
    lines.append("## Rådata")
    lines.append("- Se JSON-filen för full detalj per inslag")

    return "\n".join(lines) + "\n"


def write_quality_reports(
    *,
    report: EpisodeQualityReport,
    output_dir: str = 'episodes',
    basename: Optional[str] = None,
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    basename = basename or f"quality_report_{report.run_id}"
    json_path = os.path.join(output_dir, f"{basename}.json")
    md_path = os.path.join(output_dir, f"{basename}.md")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(_render_markdown(report))

    return {'json': json_path, 'markdown': md_path}
