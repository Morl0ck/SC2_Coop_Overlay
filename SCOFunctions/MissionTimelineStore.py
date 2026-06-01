"""User-editable mission timeline persistence (MissionTimelines.json)."""
import copy
import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional

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


def _migrate_mission(data: Dict[str, Any]) -> Dict[str, Any]:
    events = [_migrate_event(e) for e in data.get('events', [])]
    return {'events': events}


class CMissionTimelineStore:
    def __init__(self):
        self.filepath: Optional[str] = None
        self.timelines: Dict[str, Dict[str, Any]] = {}
        self.defaults: Dict[str, Dict[str, Any]] = {}

    def _seed_defaults(self) -> Dict[str, Dict[str, Any]]:
        seeded = copy.deepcopy(mission_timelines_defaults)
        for mission in map_checks:
            seeded.setdefault(mission, {'events': []})
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
        for mission, data in timelines.items():
            if isinstance(data, dict) and 'events' in data:
                self.timelines[mission] = _migrate_mission(data)

        if not os.path.isfile(filepath):
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
            self.timelines[map_name] = {'events': []}

    def reset_all(self) -> None:
        self.timelines = copy.deepcopy(self.defaults)

    def get_events(self, map_name: str, difficulty: str = 'Brutal') -> Optional[Dict[str, List[Dict[str, Any]]]]:
        data = self.timelines.get(map_name)
        if data is None:
            return None

        resolved: List[Dict[str, Any]] = []
        for ev in data.get('events', []):
            times = ev.get('times', {})
            t = times.get(difficulty)
            if t is None:
                t = times.get('Brutal')
            if t is None:
                continue
            out = {k: v for k, v in ev.items() if k != 'times'}
            out['time'] = int(t)
            resolved.append(out)

        resolved.sort(key=lambda e: e['time'])
        return {'events': resolved}

    def mission_names(self) -> List[str]:
        return sorted(self.timelines.keys())


MissionTimeline_manager = CMissionTimelineStore()
MTS = MissionTimeline_manager
