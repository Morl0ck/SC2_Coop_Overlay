"""Mission timelines for the live "what's next" overlay.

Timing data (attack waves + mission objectives) is derived from the Brutal
difficulty mission guides on starcraft2coop.com.

    Source:      https://starcraft2coop.com/missions/
    Author:      Aommaster (starcraft2coop.com)
    License:     CC-BY-NC-SA-4.0
    Source date: 2026-05-31

ShareAlike notice: this derivative timing data is distributed under the same
CC-BY-NC-SA-4.0 license as the original source. All timings are for Brutal
difficulty and are given in in-game clock seconds (the value reported by the
SC2 client API `displayTime`). They may differ on lower difficulties and can
desync after balance patches or for randomized attack-wave patterns.

Event schema (each event is a dict):
    kind      str   - "attack_wave" | "objective"
    label     str   - user-facing text
    times     dict  - Casual / Normal / Hard / Brutal -> seconds or None (Brutal required in defaults)
    tech      int   - (optional) enemy tech level
    strength  int   - (optional) enemy strength level
    spawn     str   - (optional) spawn point / attack direction (e.g. "Top Rail")
    pattern   str   - (optional) "A" / "B" for split-pattern missions
    notes     str   - (optional) extra detail for the overlay
"""

MISSION_TIMELINE_VERSION = "1.1"
MISSION_TIMELINE_SOURCE = "starcraft2coop.com/missions (Aommaster), CC-BY-NC-SA-4.0"
MISSION_TIMELINE_SOURCE_DATE = "2026-05-31"

DIFFICULTIES = ('Casual', 'Normal', 'Hard', 'Brutal')


def _times(brutal, casual=None, normal=None, hard=None):
    return {'Casual': casual, 'Normal': normal, 'Hard': hard, 'Brutal': brutal}


def _aw(t, tech, strength, spawn=None, pattern=None, notes=None, label='Attack wave'):
    e = {'kind': 'attack_wave', 'label': label, 'tech': tech, 'strength': strength, 'times': _times(t)}
    if spawn:
        e['spawn'] = spawn
    if pattern:
        e['pattern'] = pattern
    if notes:
        e['notes'] = notes
    return e


def _obj(t, label, **kw):
    e = {'kind': 'objective', 'label': label, 'times': _times(t)}
    e.update(kw)
    return e


def _th(t, direction, pattern, notes=None):
    e = {'kind': 'objective', 'label': 'Void Thrasher', 'spawn': direction, 'pattern': pattern, 'times': _times(t)}
    if notes:
        e['notes'] = notes
    return e


def _pattern_rows(rows, pattern):
    events = []
    for t, tech, strength, direction in rows:
        if tech is None:
            events.append(_th(t, direction, pattern))
        else:
            events.append(_aw(t, tech, strength, spawn=direction, pattern=pattern))
    return events


# Temple of the Past — Pattern A/B (time_sec, tech, strength, direction); None tech => thrasher only
_TEMPLE_A = [
    (180, 1, 1, '↗'), (240, 2, 2, '↗'), (360, 2, 2, '↗'), (405, 1, 2, '↗'), (450, 2, 2, '↗'),
    (495, 2, 2, '↗'), (540, 3, 3, '↘↖'), (600, 4, 3, '↘↖'), (660, 4, 4, '↘↖'), (720, 3, 4, '↗'),
    (750, 4, 4, '↗'), (795, 5, 4, '↗'), (825, None, None, '↖'), (900, 3, 3, '↙'), (920, 4, 4, '↙'),
    (970, 2, 2, '↙'), (1000, 3, 3, '↙'), (1015, None, None, '↘'), (1080, 5, 5, '↘'), (1095, 3, 5, '↖'),
    (1155, 4, 4, '↙'), (1200, 5, 5, '↗'), (1215, 3, 3, '↙↙'), (1245, 2, 4, '↖↖'), (1275, 3, 3, '↗↗'),
    (1290, 2, 3, '↙↙'), (1320, 6, 5, '↗'), (1350, 4, 6, '↘↖'), (1410, 5, 5, '↘'), (1420, 3, 5, '↖'),
    (1480, 5, 6, '↘↖↗'),
]
_TEMPLE_B = [
    (180, 1, 1, '↗'), (250, 2, 2, '↗'), (360, 2, 2, '↗'), (405, 1, 1, '↗'), (450, 2, 3, '↗'),
    (495, None, None, '↗'), (540, 3, 3, '↘ or ↖'), (600, 4, 3, '↘↖'), (660, 4, 4, '↖ or ↘'),
    (720, 3, 4, '↗'), (750, 4, 4, '↗'), (815, 5, 4, '↖'), (825, None, None, '↖'), (900, 2, 2, '↙'),
    (930, 3, 3, '↙'), (945, None, None, '↘'), (995, 3, 3, '↙'), (1015, 4, 4, '↙'), (1080, 5, 5, '↘ or ↗'),
    (1095, 3, 5, '↖ or ↗'), (1155, 4, 4, '↙'), (1200, 4, 5, '↗'), (1220, 3, 3, '↙'), (1240, 2, 3, '↙'),
    (1350, 4, 6, '↘↖'), (1410, 5, 5, '↘'), (1420, 3, 5, '↖'), (1480, 5, 6, '↘↖↗'),
]

# Keys MUST use SCO canonical mission names (see IdentifyMap.py).
_raw_mission_timelines = {
    'Chain of Ascension': {
        'events': [
            _obj(540, 'Hybrid wave 1', tech=3, strength=3),
            _obj(600, 'Slayn Elemental 1'),
            _obj(900, 'Hybrid wave 2', tech=4, strength=4),
            _obj(960, 'Slayn Elemental 2'),
            _obj(1380, 'Hybrid wave 3', tech=6, strength=6),
            _obj(1800, 'Hybrid wave 4', tech=6, strength=6),
            _aw(210, 2, 2, notes='Single'),
            _aw(420, 5, 5, notes='Single'),
            _aw(660, 4, 4, notes='Single'),
            _aw(840, 5, 5, notes='Single'),
            _aw(1080, 4, 4, notes='Double'),
            _aw(1290, 7, 5, notes='Double'),
            _aw(1530, 7, 6, notes='Double'),
        ]
    },
    'Cradle of Death': {
        'events': [
            _aw(240, 1, 1),
            _aw(360, 1, 2),
            _aw(540, 2, 2),
            _aw(720, 3, 2),
            _aw(900, 4, 4),
            _aw(1080, 4, 4),
            _aw(1260, 5, 5),
            _aw(1500, 6, 5),
            _aw(1740, 7, 6),
        ]
    },
    'Dead of Night': {
        # Attack waves spawn 1:00 before the night clock ends (Brutal day/night cycle).
        'events': [
            _aw(390, 0, 0, spawn='South'),
            _aw(840, 2, 2, spawn='South + North'),
            _aw(1290, 3, 3, spawn='All sides'),
            _aw(1740, 4, 4, spawn='All sides'),
        ]
    },
    'Lock & Load': {
        'events': [
            _aw(240, 1, 3, spawn='Left', notes='Single wave'),
            _aw(480, 2, 4, spawn='Right', notes='Single wave'),
            _aw(660, 3, 5, notes='Double wave'),
            _aw(840, 3, 5, notes='Double wave'),
            _aw(1020, 4, 6, notes='Double wave'),
            _aw(1140, 5, 6, notes='Repeating cycle'),
            _aw(1260, 6, 6, notes='Repeating cycle'),
            _aw(1380, 4, 6, notes='Repeating cycle'),
            _aw(1500, 4, 6, notes='Repeating cycle'),
        ]
    },
    'Malwarfare': {
        # Attack waves 2–3 are transport-position triggered; only wave 1 has a fixed clock time.
        'events': [
            _aw(216, 1, 1),
        ]
    },
    'Miner Evacuation': {
        'events': [
            _aw(390, 2, 2),
            _aw(480, 1, 1, label='Claimer wave'),
            _aw(780, 3, 3),
            _aw(912, 2, 2, label='Claimer wave'),
            _aw(1050, 4, 4),
            _aw(1158, 1, 1, label='Claimer wave'),
            _aw(1164, 1, 1, label='Claimer wave'),
            _aw(1380, 5, 5),
            _aw(1560, 4, 4, label='Claimer wave'),
            _aw(1590, 4, 4),
            _aw(1680, 6, 6),
            _aw(1920, 6, 6),
        ]
    },
    'Mist Opportunities': {
        'events': [
            _obj(255, 'Harvester bot wave 1 leaves'),
            _obj(475, 'Harvester bot wave 2 leaves'),
            _obj(730, 'Harvester bot wave 3 leaves'),
            _obj(1100, 'Harvester bot wave 4 leaves'),
            _obj(1500, 'Harvester bot wave 5 leaves'),
            _aw(180, 1, 1),
            _aw(600, 3, 3),
            _aw(930, 4, 4),
            _aw(1275, 5, 5),
            _aw(1686, 6, 6),
        ]
    },
    'Oblivion Express': {
        'events': [
            # Train spawns (bonus trains excluded per scope)
            _obj(300, 'Train 1', spawn='Top Rail', tech=2, strength=2),
            _obj(480, 'Train 2', spawn='Mid Rail', tech=3, strength=4),
            _obj(660, 'Train 3', spawn='Top Rail', tech=4, strength=5),
            _obj(840, 'Trains 4 & 5', spawn='Top/Mid Rail', tech=6, strength=6),
            _obj(1020, 'Train 6', spawn='Mid Rail', tech=7, strength=6),
            _obj(1200, 'Trains 7 & 8', spawn='Top/Mid Rail', tech=5, strength=5),
            _obj(1380, 'Train 9', spawn='Mid Rail', tech=7, strength=7),
            _obj(1500, 'Train 10', spawn='Top/Mid Rail', tech=7, strength=7),
            _aw(240, 1, 1, spawn='North'),
            _aw(360, 2, 2, spawn='South'),
            _aw(420, 1, 1, spawn='North'),
            _aw(600, 3, 3, spawn='South'),
            _aw(780, 4, 4, spawn='North'),
            _aw(960, 5, 5, spawn='North'),
            _aw(1140, 6, 6, spawn='South'),
            _aw(1320, 7, 7, spawn='North'),
            _aw(1440, 7, 7, spawn='South'),
        ]
    },
    'Part and Parcel': {
        'events': [
            _obj(480, 'Bonus train 1', spawn='Left'),
            _obj(900, 'Bonus train 2', spawn='Right'),
            _aw(225, 1, 1, spawn='Main Base'),
            _aw(390, 2, 2, spawn='Main Base'),
            _aw(600, 3, 3, spawn='Expansion'),
            _aw(846, 4, 4, spawn='Main Base'),
            _aw(1032, 5, 5, spawn='Expansion'),
            _aw(1200, 6, 6, spawn='Main Base'),
            _aw(1440, 7, 7, spawn='Army'),
            _aw(1620, 5, 5, spawn='Main Base'),
            _aw(1800, 6, 6, spawn='Main Base'),
        ]
    },
    'Rifts to Korhal': {
        'events': [
            _obj(700, 'Pirate ship 1'),
            _aw(120, 1, 1),
            _aw(300, 2, 2),
            _aw(480, 3, 3),
            _aw(660, 4, 4),
            _aw(840, 5, 5),
            _aw(1020, 6, 6),
            _aw(1230, 7, 7),
            _aw(1470, 7, 7),
            _aw(1590, 7, 7),
            _aw(1710, 7, 7),
            _aw(1800, 7, 7),
        ]
    },
    'Scythe of Amon': {
        'events': [
            _aw(168, 1, 1),
            _aw(420, 2, 2),
            _aw(540, 3, 3),
            _aw(750, 4, 4),
            _aw(960, 5, 5),
            _aw(1140, 6, 6),
            _aw(1320, 5, 5),
            _aw(1440, 6, 6),
            _aw(1560, 6, 6),
        ]
    },
    'Temple of the Past': {
        'events': (
            _pattern_rows(_TEMPLE_A, 'A')
            + _pattern_rows(_TEMPLE_B, 'B')
            + [_obj(1560, 'Defend temple timer ends')]
        ),
    },
    'The Vermillion Problem': {
        'events': [
            _aw(210, 1, 1, spawn='Main'),
            _aw(360, 2, 2, spawn='Main'),
            _aw(540, 3, 4, spawn='Expansion', notes='±1:30 variance'),
            _aw(720, 3, 4, spawn='Expansion', notes='±1:30 variance'),
            _aw(900, 5, 5, spawn='Main', notes='±1:30 variance'),
            _aw(1080, 5, 5, spawn='Main', notes='±1:30 variance'),
            _aw(1260, 5, 5, spawn='Expansion', notes='±1:30 variance'),
            _aw(1440, 6, 6, spawn='Expansion', notes='±1:30 variance'),
            _aw(1620, 5, 5, spawn='Expansion'),
        ]
    },
    'Void Launch': {
        'events': [
            _obj(378, 'Shuttle wave 1', spawn='Middle', tech=1, strength=1),
            _obj(540, 'Shuttle wave 2', tech=2, strength=2),
            _obj(750, 'Shuttle wave 3', tech=3, strength=3),
            _obj(930, 'Shuttle wave 4', tech=3, strength=3),
            _obj(1080, 'Shuttle wave 5', tech=3, strength=3),
            _obj(1230, 'Shuttle wave 6', tech=6, strength=6),
            _obj(1380, 'Shuttle wave 7', tech=7, strength=6),
            _aw(180, 1, 1, spawn='Right'),
            _aw(300, 2, 2, spawn='Left'),
            _aw(450, 2, 2),
            _aw(600, 3, 3, spawn='Right'),
            _aw(660, 3, 3, spawn='Left'),
            _aw(840, 3, 3),
            _aw(1008, 4, 4, spawn='Left'),
            _aw(1158, 5, 5, spawn='Right'),
            _aw(1308, 6, 6, spawn='Right'),
            _aw(1458, 7, 7, spawn='Right'),
        ]
    },
    'Void Thrashing': {
        'events': [
            _obj(270, 'Void Thrasher set 1'),
            _obj(560, 'Void Thrasher set 2'),
            _obj(820, 'Void Thrasher set 3'),
            _obj(1080, 'Void Thrasher set 4'),
            # Pattern A
            _aw(180, 1, 1, spawn='Right', pattern='A'),
            _aw(360, 2, 2, spawn='Right', pattern='A'),
            _aw(540, 3, 3, spawn='Left', pattern='A'),
            _aw(720, 4, 4, spawn='Left', pattern='A'),
            _aw(900, 5, 5, spawn='Right', pattern='A'),
            _aw(1080, 6, 6, spawn='Right', pattern='A'),
            _aw(1260, 7, 7, spawn='Left', pattern='A'),
            _aw(1440, 7, 7, spawn='Right', pattern='A'),
            # Pattern B
            _aw(240, 1, 2, spawn='Left', pattern='B'),
            _aw(480, 2, 3, spawn='Right', pattern='B'),
            _aw(600, 3, 3, spawn='Left', pattern='B'),
            _aw(840, 4, 5, spawn='Left', pattern='B'),
            _aw(960, 5, 4, spawn='Right', pattern='B'),
            _aw(1200, 6, 7, spawn='Left', pattern='B'),
            _aw(1320, 7, 7, spawn='Right', pattern='B'),
            _aw(1560, 7, 7, spawn='Left', pattern='B'),
        ]
    },
}


def _brutal_time(event):
    return event['times']['Brutal']


def _build(raw):
    """ Pre-sort each mission's events by Brutal time once at import. """
    out = {}
    for mission, data in raw.items():
        events = sorted(data['events'], key=_brutal_time)
        out[mission] = {'events': events}
    return out


mission_timelines_defaults = _build(_raw_mission_timelines)
# Back-compat alias for imports that expect bundled defaults under this name.
mission_timelines = mission_timelines_defaults
