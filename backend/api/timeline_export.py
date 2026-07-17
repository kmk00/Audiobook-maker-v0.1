"""
timeline_export.py

Bierze finalną listę segmentów (wynik alignmentu z alignment.py, wzbogaconą
o character_id/character_name/avatar_path z bloków) i produkuje DWA pliki:

1. captions.srt   — napisy zdanie-po-zdaniu, do zaimportowania w DaVinci jako
                     osobna ścieżka napisów (File > Import > Subtitle, albo
                     przeciągnięcie na timeline).

2. nameplates.fcpxml — GOTOWY timeline (tylko ścieżka wideo) z kartami postaci
                        (avatar+nazwa) w odpowiednich momentach, do zaimportowania
                        jako nowy projekt/timeline w DaVinci.

FCPXML celowo NIE zawiera audio ani napisów — testy pokazały, że mieszanie
audio+wideo w jednym FCPXML przez OTIO tworzy niestabilne "connected clips"
(lanes). Zamiast tego: audio dokładasz ręcznie na oś 0:00 (1 przeciągnięcie),
SRT importujesz osobno. To eliminuje ryzyko błędnego importu.

Wymagane zależności (u siebie):
    pip install opentimelineio otio-fcpx-xml-adapter --break-system-packages

Oczekiwany kształt wejściowych segmentów (lista dictów):
[
    {
        "start": 12.4,              # sekundy, globalne (już po doliczeniu offsetu)
        "end": 14.9,
        "text": "Ludicrous…",
        "character_id": 3,          # None dla narratora
        "character_name": "Russell",
        "avatar_path": "/abs/path/to/avatar.png",  # None dla narratora
        "is_narrator": False,
    },
    ...
]
"""

import os
from typing import List, Dict, Optional

import opentimelineio as otio

from .nameplate_generator import get_or_create_nameplate

FPS = 30


def _sec_to_rt(seconds: float) -> otio.opentime.RationalTime:
    return otio.opentime.RationalTime(round(seconds * FPS), FPS)


def _format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_srt(segments: List[Dict], output_path: str) -> str:
    """Generuje plik .srt z segmentów (zdanie po zdaniu)."""
    lines = []
    for idx, seg in enumerate(segments, start=1):
        start_ts = _format_srt_timestamp(seg["start"])
        end_ts = _format_srt_timestamp(seg["end"])
        text = seg["text"]
        # Dla kwestii dialogowych dorzucamy nazwę postaci nad tekstem w napisach
        if not seg.get("is_narrator") and seg.get("character_name"):
            display_text = f"{seg['character_name'].upper()}\n{text}"
        else:
            display_text = text

        lines.append(str(idx))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(display_text)
        lines.append("")  # pusta linia między wpisami

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def _merge_into_character_blocks(segments: List[Dict]) -> List[Dict]:
    """
    Łączy kolejne zdania należące do tego samego bloku postaci w JEDEN
    zakres czasu (karta postaci ma być widoczna przez cały blok, a nie
    migać między zdaniami tej samej kwestii).

    Zwraca listę: [{"start", "end", "character_id", "character_name",
                     "avatar_path", "is_narrator"}]
    """
    if not segments:
        return []

    blocks = []
    current = None

    for seg in segments:
        char_id = seg.get("character_id")
        is_narrator = seg.get("is_narrator", char_id is None)

        if current is not None and current["character_id"] == char_id:
            # ten sam mówca -> rozszerzamy zakres
            current["end"] = seg["end"]
        else:
            if current is not None:
                blocks.append(current)
            current = {
                "start": seg["start"],
                "end": seg["end"],
                "character_id": char_id,
                "character_name": seg.get("character_name"),
                "avatar_path": seg.get("avatar_path"),
                "is_narrator": is_narrator,
            }
    if current is not None:
        blocks.append(current)

    return blocks


def export_nameplates_fcpxml(
    segments: List[Dict],
    output_path: str,
    nameplate_cache_dir: str,
) -> Optional[str]:
    """
    Generuje FCPXML z jedną ścieżką wideo: karty postaci (avatar+nazwa) w
    momentach, gdy dana postać mówi. Bloki narratora = przerwa (Gap), karta
    znika z ekranu (zgodnie z ustaleniami).

    Zwraca None (zamiast pustego pliku) jeśli w segmentach nie ma ani jednej
    kwestii z przypisaną postacią — np. w trybie czysto-lektorskim, gdzie
    karta postaci nie miałaby czego pokazywać przez cały odcinek.
    """
    blocks = _merge_into_character_blocks(segments)

    has_any_character = any(
        not b["is_narrator"] and b["character_id"] is not None for b in blocks
    )
    if not has_any_character:
        return None

    timeline = otio.schema.Timeline(name="Nameplates")
    video_track = otio.schema.Track(name="Nameplates", kind=otio.schema.TrackKind.Video)

    for block in blocks:
        duration_sec = max(block["end"] - block["start"], 0.05)
        dur = _sec_to_rt(duration_sec)

        if block["is_narrator"] or block["character_id"] is None:
            video_track.append(otio.schema.Gap(duration=dur))
            continue

        nameplate_path = get_or_create_nameplate(
            character_id=block["character_id"],
            character_name=block["character_name"] or "???",
            avatar_path=block["avatar_path"],
            cache_dir=nameplate_cache_dir,
        )
        abs_path = os.path.abspath(nameplate_path)

        media_ref = otio.schema.ExternalReference(
            target_url=f"file://{abs_path}",
            available_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, FPS), duration=dur
            ),
        )
        clip = otio.schema.Clip(
            name=block["character_name"] or "nameplate",
            media_reference=media_ref,
            source_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, FPS), duration=dur
            ),
        )
        video_track.append(clip)

    timeline.tracks.append(video_track)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    otio.adapters.write_to_file(timeline, output_path)
    return output_path


def export_all(
    segments: List[Dict],
    output_dir: str,
    task_id: str,
    nameplate_cache_dir: str,
) -> Dict[str, Optional[str]]:
    """
    Wygodny wrapper: generuje SRT zawsze, FCPXML tylko jeśli jest sens
    (patrz export_nameplates_fcpxml — zwraca None w trybie czysto-lektorskim).
    """
    srt_path = export_srt(segments, os.path.join(output_dir, f"captions_{task_id}.srt"))
    fcpxml_path = export_nameplates_fcpxml(
        segments,
        os.path.join(output_dir, f"nameplates_{task_id}.fcpxml"),
        nameplate_cache_dir,
    )
    return {"srt_path": srt_path, "fcpxml_path": fcpxml_path}