"""Apply Hard attack-wave medians from hard_timings_summary.json to MissionTimelines.json.

Writes replay-derived Hard waves as standalone time-only entries. Nearby detections
are merged and the list is capped at the Brutal wave count when Brutal data exists.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.MissionTimelineStore import MTS

SUMMARY_PATH = os.path.join(os.path.dirname(__file__), 'hard_timings_summary.json')
TIMELINES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MissionTimelines.json')

# Collapse replay noise (double spawns, hybrid overlaps) before capping wave count.
WAVE_MERGE_GAP_SEC = 90


def merge_close_times(times: list[int], gap: int = WAVE_MERGE_GAP_SEC) -> list[int]:
    if not times:
        return []
    merged = [times[0]]
    for t in times[1:]:
        if t - merged[-1] >= gap:
            merged.append(t)
    return merged


def subsample_times(times: list[int], count: int) -> list[int]:
    if count <= 0 or not times:
        return []
    if len(times) <= count:
        return list(times)
    if count == 1:
        return [times[0]]
    picked = [times[round(i * (len(times) - 1) / (count - 1))] for i in range(count)]
    deduped: list[int] = []
    seen: set[int] = set()
    for t in picked:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def build_hard_attack_waves(hard_times: list, max_waves: int | None = None) -> list[dict]:
    cleaned = merge_close_times(sorted(int(t) for t in hard_times if t is not None))
    if max_waves is not None and len(cleaned) > max_waves:
        cleaned = subsample_times(cleaned, max_waves)
    return [{'label': 'Attack wave', 'time': t} for t in cleaned]


def apply_hard_timings(summary_path: str = SUMMARY_PATH, timelines_path: str = TIMELINES_PATH) -> dict:
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    MTS.load(timelines_path)
    stats = {'missions_updated': 0, 'waves_written': 0, 'missions': {}}

    for mission, mission_data in summary.get('by_mission', {}).items():
        if mission not in MTS.timelines:
            continue

        brutal_waves = MTS.timelines[mission]['attack_waves'].get('Brutal', [])
        max_waves = len(brutal_waves) if brutal_waves else None

        hard_times = mission_data.get('median_wave_times_sec') or []
        hard_waves = build_hard_attack_waves(hard_times, max_waves=max_waves)
        if not hard_waves:
            continue

        MTS.timelines[mission]['attack_waves']['Hard'] = hard_waves
        stats['missions_updated'] += 1
        stats['waves_written'] += len(hard_waves)
        stats['missions'][mission] = {
            'hard_waves': len(hard_waves),
            'brutal_waves': len(brutal_waves),
            'replay_count': mission_data.get('replay_count', 0),
        }

    MTS.save()
    return stats


def main() -> None:
    stats = apply_hard_timings()
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
