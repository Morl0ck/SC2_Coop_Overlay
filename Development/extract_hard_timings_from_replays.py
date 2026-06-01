"""Extract Hard-difficulty attack-wave timings from co-op replays.

Usage (repo root):
    python Development/extract_hard_timings_from_replays.py "C:\\path\\to\\Replays\\Multiplayer"

Prints per-mission median wave times and optional JSON snippet for MissionTimelines.json.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.IdentifyMap import map_checks
from SCOFunctions.S2Parser import s2_parse_replay
from SCOFunctions.SC2Dictionaries import UnitsInWaves, amon_player_ids

COOP_MISSIONS = set(map_checks.keys())
UNIT_SPAWN_EVENTS = (
    'NNet.Replay.Tracker.SUnitBornEvent',
    'NNet.Replay.Tracker.SUnitInitEvent',
)
MIN_WAVE_UNITS = 6  # matches ReplayAnalysis (>5)
WAVE_GRACE = 60  # ignore spawns in first 60s after start


def extract_wave_times(replay: Dict[str, Any], events: List[Dict[str, Any]]) -> List[int]:
    start = replay['start_time']
    mission = replay['map_name']
    amon_pids = amon_player_ids.get(mission, {3, 4, 5, 6})
    wave_units: Dict[str, Any] = {'second': 0, 'units': []}
    identified: Dict[int, List[str]] = {}

    for event in events:
        if event['_event'] not in UNIT_SPAWN_EVENTS:
            continue
        pid = event.get('m_controlPlayerId')
        if pid not in amon_pids:
            continue
        t = event['_gameloop'] / 16
        if t <= start + WAVE_GRACE:
            continue
        unit_type = event['m_unitTypeName'].decode()
        if unit_type not in UnitsInWaves:
            continue

        sec = int(t)
        if wave_units['second'] == sec:
            wave_units['units'].append(unit_type)
        else:
            wave_units['second'] = sec
            wave_units['units'] = [unit_type]

        if len(wave_units['units']) >= MIN_WAVE_UNITS:
            identified[sec] = list(wave_units['units'])

    return sorted(int(s - start) for s in identified.keys())


def scan_replay_dir(replay_dir: str, difficulty: str = 'Hard') -> Dict[str, Any]:
    files = [
        os.path.join(replay_dir, f)
        for f in os.listdir(replay_dir)
        if f.lower().endswith('.sc2replay')
    ]
    files.sort(key=os.path.getmtime)

    summary: Dict[str, Any] = {
        'replay_dir': replay_dir,
        'total_replays': len(files),
        'difficulty': difficulty,
        'parsed_ok': 0,
        'coop_mission_replays': 0,
        'target_replays': 0,
        'failed': [],
        'by_mission': {},
    }

    # Pass 1: metadata only
    candidates: List[str] = []
    for path in files:
        try:
            replay = s2_parse_replay(path, parse_events=False, onlyBlizzard=True)
        except Exception:
            continue
        if replay is None:
            continue
        summary['parsed_ok'] += 1
        mission = replay.get('map_name')
        if mission not in COOP_MISSIONS:
            continue
        summary['coop_mission_replays'] += 1
        d1, d2 = replay.get('difficulty', ('', ''))
        if d1 != difficulty or d2 != difficulty:
            continue
        if replay.get('mutators'):
            continue
        if replay.get('brutal_plus', 0) > 0:
            continue
        candidates.append(path)

    summary['target_replays'] = len(candidates)

    waves_by_mission: Dict[str, List[tuple[str, List[int]]]] = defaultdict(list)
    replay_counts: Dict[str, int] = defaultdict(int)

    for path in candidates:
        try:
            replay = s2_parse_replay(path, parse_events=True, return_events=True, onlyBlizzard=True)
        except Exception:
            summary['failed'].append(os.path.basename(path))
            continue
        if replay is None or 'events' not in replay:
            summary['failed'].append(os.path.basename(path))
            continue
        mission = replay['map_name']
        waves = extract_wave_times(replay, replay['events'])
        if not waves:
            continue
        waves_by_mission[mission].append((path, waves))
        replay_counts[mission] += 1

    for mission, wave_entries in sorted(waves_by_mission.items()):
        wave_lists = [w for _, w in wave_entries]
        max_len = max(len(w) for w in wave_lists)
        slot_times: List[Optional[int]] = []
        slot_counts: List[int] = []
        for idx in range(max_len):
            vals = [w[idx] for w in wave_lists if idx < len(w)]
            if not vals:
                slot_times.append(None)
                slot_counts.append(0)
                continue
            slot_times.append(int(round(statistics.median(vals))))
            slot_counts.append(len(vals))

        summary['by_mission'][mission] = {
            'replay_count': replay_counts[mission],
            'wave_counts_per_replay': [len(w) for w in wave_lists],
            'median_wave_times_sec': slot_times,
            'sample_replay': os.path.basename(wave_entries[0][0]) if wave_entries else '',
            'raw_samples': wave_lists[:3],
        }

    return summary


def seconds_to_mmss(seconds: int) -> str:
    return f'{seconds // 60}:{seconds % 60:02d}'


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    replay_dir = sys.argv[1]
    if not os.path.isdir(replay_dir):
        print(f'Not a directory: {replay_dir}')
        sys.exit(1)

    summary = scan_replay_dir(replay_dir)
    out_json = os.path.join(os.path.dirname(__file__), 'hard_timings_summary.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(json.dumps({
        'replay_dir': summary['replay_dir'],
        'total_replays': summary['total_replays'],
        'parsed_ok': summary['parsed_ok'],
        'coop_mission_replays': summary['coop_mission_replays'],
        'target_replays': summary['target_replays'],
        'failed_parse_with_events': len(summary['failed']),
    }, indent=2))
    print()

    if not summary['by_mission']:
        print('No Hard co-op attack waves extracted.')
        return

    for mission, data in summary['by_mission'].items():
        times = data['median_wave_times_sec']
        readable = [seconds_to_mmss(t) if t is not None else '-' for t in times]
        print(f'=== {mission} ({data["replay_count"]} replays) ===')
        print(f'  Waves per replay: {data["wave_counts_per_replay"]}')
        print(f'  Median times (sec): {times}')
        print(f'  Median times (mm:ss): {readable}')
        print()
    print(f'Full summary written to {out_json}')


if __name__ == '__main__':
    main()
