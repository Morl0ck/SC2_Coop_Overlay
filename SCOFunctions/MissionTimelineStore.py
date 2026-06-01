"""User-editable mission timeline persistence (MissionTimelines.json)."""
import copy
import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple

from SCOFunctions.IdentifyMap import map_checks
from SCOFunctions.MLogging import Logger
from SCOFunctions.SC2Dictionaries.MissionTimelines import (
    DIFFICULTIES,
    MISSION_TIMELINE_VERSION,
    mission_timelines_defaults,
)

logger = Logger('MTS', Logger.levels.INFO)

MMSS_RE = re.compile(r'^(\d+):(\d{2})$')


def seconds_to_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return ''
    return f'{int(seconds) // 60}:{int(seconds) % 60:02d}'


def mmss_to_seconds(text: str) -> Optional[int]:
    text = (text or '').strip()
    if not text:
        return None
    m = MMSS_RE.match(text)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def empty_mission_data() -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    empty = {d: [] for d in DIFFICULTIES}
    return {'attack_waves': copy.deepcopy(empty), 'objectives': copy.deepcopy(empty)}


def _migrate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Convert legacy single ``time`` field to ``times`` map."""
    if 'times' in event:
        out = copy.deepcopy(event)
    else:
        out = copy.deepcopy(event)
        brutal = out.pop('time', None)
        out['times'] = {d: None for d in DIFFICULTIES}
        out['times']['Brutal'] = brutal
    for d in DIFFICULTIES:
        out['times'].setdefault(d, None)
    return out


def _normalize_entry(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ev = copy.deepcopy(raw)
    ev.pop('kind', None)
    if 'times' in ev:
        times = ev.pop('times')
        t = times.get('Brutal')
        if t is None:
            t = next((v for v in times.values() if v is not None), None)
        if t is None:
            return None
        ev['time'] = int(t)
    elif 'time' in ev and ev['time'] is not None:
        ev['time'] = int(ev['time'])
    else:
        return None
    return ev


def _list_to_by_difficulty(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_diff = {d: [] for d in DIFFICULTIES}
    for raw in items:
        ev = _migrate_event(raw)
        times = ev.pop('times', {})
        base = {k: v for k, v in ev.items()}
        for diff in DIFFICULTIES:
            t = times.get(diff)
            if t is not None:
                entry = dict(base)
                entry['time'] = int(t)
                by_diff[diff].append(entry)
    for diff in DIFFICULTIES:
        by_diff[diff].sort(key=lambda e: e['time'])
    return by_diff


def _normalize_section(section: Any) -> Dict[str, List[Dict[str, Any]]]:
    if isinstance(section, list):
        return _list_to_by_difficulty(section)

    out = {d: [] for d in DIFFICULTIES}
    if not isinstance(section, dict):
        return out

    for diff in DIFFICULTIES:
        items = section.get(diff, [])
        if not isinstance(items, list):
            continue
        normalized = []
        for raw in items:
            entry = _normalize_entry(raw)
            if entry is not None:
                normalized.append(entry)
        out[diff] = sorted(normalized, key=lambda e: e['time'])
    return out


def _split_legacy_events(events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    waves, objectives = [], []
    for raw in events:
        ev = _migrate_event(raw)
        kind = ev.pop('kind', 'attack_wave')
        if kind == 'objective':
            objectives.append(ev)
        else:
            waves.append(ev)
    return waves, objectives


def _migrate_mission(data: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(data.get('attack_waves'), dict) or isinstance(data.get('objectives'), dict):
        return {
            'attack_waves': _normalize_section(data.get('attack_waves', {})),
            'objectives': _normalize_section(data.get('objectives', {})),
        }
    if 'attack_waves' in data or 'objectives' in data:
        return {
            'attack_waves': _normalize_section(data.get('attack_waves', [])),
            'objectives': _normalize_section(data.get('objectives', [])),
        }
    if 'events' in data:
        waves, objectives = _split_legacy_events(data['events'])
        return {
            'attack_waves': _list_to_by_difficulty(waves),
            'objectives': _list_to_by_difficulty(objectives),
        }
    return empty_mission_data()


def _mission_needs_resave(data: Dict[str, Any]) -> bool:
    if 'events' in data:
        return True
    for key in ('attack_waves', 'objectives'):
        section = data.get(key)
        if isinstance(section, list):
            return True
        if isinstance(section, dict):
            for items in section.values():
                if not isinstance(items, list):
                    continue
                for ev in items:
                    if isinstance(ev, dict) and 'times' in ev:
                        return True
    return False


def _resolve_section(
    section: Dict[str, List[Dict[str, Any]]],
    difficulty: str,
    kind: str,
    *,
    brutal_fallback: bool = False,
) -> List[Dict[str, Any]]:
    if not isinstance(section, dict):
        section = {}

    items = section.get(difficulty) or []
    if brutal_fallback and not items and difficulty != 'Brutal':
        items = section.get('Brutal') or []

    resolved: List[Dict[str, Any]] = []
    for ev in items:
        t = ev.get('time')
        if t is None:
            continue
        out = {k: v for k, v in ev.items() if k != 'time'}
        out['time'] = int(t)
        out['kind'] = kind
        resolved.append(out)
    return resolved


def difficulty_fallback_chain(requested: str) -> List[str]:
    """Walk upward from requested difficulty through Brutal."""
    if requested not in DIFFICULTIES:
        return ['Brutal']
    idx = DIFFICULTIES.index(requested)
    return list(DIFFICULTIES[idx:])


class CMissionTimelineStore:
    def __init__(self):
        self.filepath: Optional[str] = None
        self.timelines: Dict[str, Dict[str, Any]] = {}
        self.defaults: Dict[str, Dict[str, Any]] = {}

    def _seed_defaults(self) -> Dict[str, Dict[str, Any]]:
        seeded = copy.deepcopy(mission_timelines_defaults)
        for mission in map_checks:
            seeded.setdefault(mission, empty_mission_data())
        return seeded

    def load(self, filepath: str) -> None:
        self.filepath = filepath
        self.defaults = self._seed_defaults()
        loaded: Dict[str, Any] = {}

        try:
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
        except Exception:
            logger.error(f'Error loading mission timelines:\n{traceback.format_exc()}')
            if os.path.isfile(filepath):
                base = filepath.replace('.json', '')
                corrupt = f'{base}_corrupted.json'
                try:
                    os.replace(filepath, corrupt)
                except OSError:
                    pass

        timelines = loaded.get('timelines', loaded) if isinstance(loaded, dict) else {}
        if not isinstance(timelines, dict):
            timelines = {}

        self.timelines = copy.deepcopy(self.defaults)
        needs_resave = not os.path.isfile(filepath)
        for mission, data in timelines.items():
            if not isinstance(data, dict):
                continue
            if _mission_needs_resave(data):
                needs_resave = True
            self.timelines[mission] = _migrate_mission(data)

        if needs_resave:
            self.save()

    def save(self) -> None:
        if not self.filepath:
            return
        try:
            payload = {
                'version': MISSION_TIMELINE_VERSION,
                'timelines': self.timelines,
            }
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            logger.info('Mission timelines saved')
        except Exception:
            logger.error(f'Error saving mission timelines:\n{traceback.format_exc()}')

    def reset_mission(self, map_name: str) -> None:
        if map_name in self.defaults:
            self.timelines[map_name] = copy.deepcopy(self.defaults[map_name])
        else:
            self.timelines[map_name] = empty_mission_data()

    def reset_all(self) -> None:
        self.timelines = copy.deepcopy(self.defaults)

    def get_events(self, map_name: str, difficulty: str = 'Brutal') -> Optional[Dict[str, Any]]:
        data = self.timelines.get(map_name)
        if data is None:
            return None

        attack_waves = data.get('attack_waves', {})
        objectives = data.get('objectives', {})

        for timing_difficulty in difficulty_fallback_chain(difficulty):
            waves = _resolve_section(attack_waves, timing_difficulty, 'attack_wave')
            objectives_resolved = _resolve_section(
                objectives,
                timing_difficulty,
                'objective',
                brutal_fallback=True,
            )
            merged = waves + objectives_resolved
            if not merged:
                continue

            merged.sort(key=lambda e: e['time'])
            return {
                'events': merged,
                'requested_difficulty': difficulty,
                'timing_difficulty': timing_difficulty,
            }

        return None

    def mission_names(self) -> List[str]:
        return sorted(self.timelines.keys())


MissionTimeline_manager = CMissionTimelineStore()
MTS = MissionTimeline_manager
