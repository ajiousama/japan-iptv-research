#!/usr/bin/env python3
"""Suggest possible XMLTV EPG IDs for local-station candidates.

This is metadata-only. It parses a local XMLTV file and compares channel IDs
and display names against the URL-free local-station EPG map.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Set, Tuple


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = re.sub(r"[\s_\-・/()（）\[\]【】.,:;!！?？'\"`]+", "", value)
    return value


def split_field(value: str) -> List[str]:
    if not value:
        return []
    out: List[str] = []
    for part in re.split(r"[;|/]", value):
        item = part.strip()
        if item:
            out.append(item)
    return out


def tag_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def read_epg_channels(epg_path: Path) -> List[Dict[str, str]]:
    if not epg_path.exists():
        raise FileNotFoundError(f"EPG file not found: {epg_path}")

    channels: List[Dict[str, str]] = []
    for _event, elem in ET.iterparse(epg_path, events=("end",)):
        if tag_name(elem.tag) != "channel":
            continue
        channel_id = (elem.attrib.get("id") or "").strip()
        display_names: List[str] = []
        for child in elem:
            if tag_name(child.tag) == "display-name" and child.text:
                text = child.text.strip()
                if text and text not in display_names:
                    display_names.append(text)
        if channel_id:
            channels.append(
                {
                    "epg_id": channel_id,
                    "display_names": ";".join(display_names),
                    "search_text": " ".join([channel_id] + display_names),
                }
            )
        elem.clear()
    return channels


def read_map_rows(map_path: Path) -> List[Dict[str, str]]:
    if not map_path.exists():
        raise FileNotFoundError(f"map CSV not found: {map_path}")
    with map_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def terms_for_row(row: Dict[str, str]) -> List[str]:
    terms: List[str] = []
    for key in (
        "channel_key",
        "display_name",
        "tvg_id_preferred",
        "tvg_id_alternates",
        "display_aliases",
        "notes",
    ):
        value = row.get(key, "")
        if key in {"tvg_id_alternates", "display_aliases"}:
            terms.extend(split_field(value))
        elif value:
            terms.append(value)

    display_name = row.get("display_name", "")
    extras = {
        "チバテレ": ["千葉テレビ", "chiba", "chibatv"],
        "tvk": ["テレビ神奈川", "kanagawa", "tvk"],
        "テレ玉": ["テレビ埼玉", "saitama", "tvs", "teletama"],
        "TOKYO MX2": ["tokyo mx", "mx2", "tokyo_mx"],
        "テレビ新広島": ["新広島", "tss", "hiroshima"],
        "KBS京都": ["京都", "kbs", "kyoto"],
        "サンテレビ": ["sun", "suntv", "サン", "兵庫"],
        "MBS": ["毎日放送", "mbs", "osaka"],
        "ABC": ["朝日放送", "abc", "asahi"],
        "YTV": ["読売テレビ", "ytv", "yomiuri"],
    }
    terms.extend(extras.get(display_name, []))

    dedup: List[str] = []
    seen: Set[str] = set()
    for term in terms:
        norm = normalize(term)
        if norm and norm not in seen:
            dedup.append(term)
            seen.add(norm)
    return dedup


def score_candidate(terms: List[str], epg: Dict[str, str]) -> Tuple[int, str]:
    epg_text = epg["search_text"]
    epg_norm = normalize(epg_text)
    epg_id_norm = normalize(epg["epg_id"])
    best = 0
    reasons: List[str] = []

    for term in terms:
        term_norm = normalize(term)
        if not term_norm:
            continue
        if term_norm == epg_id_norm:
            best = max(best, 100)
            reasons.append(f"exact-id:{term}")
        elif term_norm in epg_id_norm or epg_id_norm in term_norm:
            best = max(best, 92)
            reasons.append(f"id-contains:{term}")
        elif term_norm in epg_norm:
            best = max(best, 86)
            reasons.append(f"text-contains:{term}")
        else:
            ratio = SequenceMatcher(None, term_norm, epg_norm).ratio()
            if ratio >= 0.55:
                score = int(60 + ratio * 25)
                best = max(best, score)
                reasons.append(f"fuzzy:{term}:{ratio:.2f}")

    return best, ";".join(reasons[:4])


def build_suggestions(rows: List[Dict[str, str]], epg_channels: List[Dict[str, str]], top_n: int) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for row in rows:
        terms = terms_for_row(row)
        scored: List[Tuple[int, str, Dict[str, str]]] = []
        for epg in epg_channels:
            score, reason = score_candidate(terms, epg)
            if score > 0:
                scored.append((score, reason, epg))
        scored.sort(key=lambda item: (-item[0], item[2]["epg_id"]))
        if not scored:
            output.append(
                {
                    "channel_key": row.get("channel_key", ""),
                    "display_name": row.get("display_name", ""),
                    "rank": "",
                    "score": "0",
                    "suggested_epg_id": "",
                    "epg_display_names": "",
                    "reason": "no candidate",
                    "search_terms": ";".join(terms),
                }
            )
            continue
        for rank, (score, reason, epg) in enumerate(scored[:top_n], start=1):
            output.append(
                {
                    "channel_key": row.get("channel_key", ""),
                    "display_name": row.get("display_name", ""),
                    "rank": str(rank),
                    "score": str(score),
                    "suggested_epg_id": epg["epg_id"],
                    "epg_display_names": epg["display_names"],
                    "reason": reason,
                    "search_terms": ";".join(terms),
                }
            )
    return output


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "channel_key",
        "display_name",
        "rank",
        "score",
        "suggested_epg_id",
        "epg_display_names",
        "reason",
        "search_terms",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest EPG IDs for local-station candidates.")
    parser.add_argument("--epg", required=True, help="Path to XMLTV EPG file")
    parser.add_argument("--map", default="japan_iptv_local_station_epg_map.csv")
    parser.add_argument("--out", default="local_station_epg_id_suggestions.csv")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    try:
        epg_channels = read_epg_channels(Path(args.epg))
        rows = read_map_rows(Path(args.map))
        suggestions = build_suggestions(rows, epg_channels, args.top)
        write_csv(Path(args.out), suggestions)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    nonempty = sum(1 for row in suggestions if row["suggested_epg_id"])
    print(f"EPG channels loaded: {len(epg_channels)}")
    print(f"Map rows checked: {len(rows)}")
    print(f"Suggestion rows: {len(suggestions)}")
    print(f"Rows with suggestions: {nonempty}")
    print(f"Wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
