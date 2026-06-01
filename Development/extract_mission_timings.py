"""Fetch Brutal attack-wave / fixed-time objective tables from starcraft2coop.com.

Run from repo root: python Development/extract_mission_timings.py

Output is printed as Python snippets for MissionTimelines.py (not written automatically).
"""
from __future__ import annotations

import re
import urllib.request

MISSION_PAGES = {
    'Chain of Ascension': 'chainofascension.html',
    'Cradle of Death': 'cradleofdeath.html',
    'Dead of Night': 'deadofnight.html',
    'Lock & Load': 'lockload.html',
    'Malwarfare': 'malwarfare.html',
    'Miner Evacuation': 'minerevacuation.html',
    'Mist Opportunities': 'mistopportunities.html',
    'Oblivion Express': 'oblivionexpress.html',
    'Part and Parcel': 'partparcel.html',
    'Rifts to Korhal': 'riftstokorhal.html',
    'Scythe of Amon': 'scytheofamon.html',
    'Temple of the Past': 'templeofthepast.html',
    'The Vermillion Problem': 'thevermillionproblem.html',
    'Void Launch': 'voidlaunch.html',
    'Void Thrashing': 'voidthrashing.html',
}

BASE = 'https://starcraft2coop.com/missions/'


def mmss_to_seconds(s: str) -> int | None:
    s = s.strip()
    if not s or s in ('-', '—'):
        return None
    s = re.sub(r'\s*±.*', '', s)
    s = re.sub(r'\*+', '', s)
    m = re.match(r'^(\d+):(\d{2})(?::(\d{2}))?$', s)
    if not m:
        return None
    if m.group(3):
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    return int(m.group(1)) * 60 + int(m.group(2))


def parse_int_field(val: str) -> int | None:
    val = val.strip()
    if not val or val == '-':
        return None
    m = re.match(r'^(\d+)', val)
    return int(m.group(1)) if m else None


def fetch_html(name: str) -> str:
    url = BASE + MISSION_PAGES[name]
    req = urllib.request.Request(url, headers={'User-Agent': 'SCO-MissionTimeline-Extractor/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='replace')


def strip_tags(html: str) -> str:
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    html = re.sub(r'<[^>]+>', '', html)
    return html.replace('&nbsp;', ' ').strip()


def extract_tables(html: str) -> list[list[list[str]]]:
    tables = []
    for tbl in re.findall(r'<table[^>]*>(.*?)</table>', html, flags=re.I | re.S):
        rows = []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, flags=re.I | re.S):
            cells = [strip_tags(td) for td in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, flags=re.I | re.S)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def find_attack_wave_tables(html: str) -> list[tuple[str | None, list[list[str]]]]:
    """Return (pattern_label, rows) for attack-wave timing tables."""
    out = []
    # Split by pattern headers in plain text
    chunks = re.split(
        r'(Pattern [AB]:|The Attack Wave Timings for this mission are:|Attack Wave Timings for this mission are:|'
        r'The timings, Strength and Tech levels for the attack waves|'
        r'The Attack Wave Timings for this mission are:)',
        html,
        flags=re.I,
    )
    pattern = None
    for i, chunk in enumerate(chunks):
        if re.match(r'Pattern [AB]:', chunk, re.I):
            pattern = chunk.strip().split()[1].rstrip(':')
            continue
        if 'attack wave' not in chunk.lower() and 'attack waves' not in chunk.lower():
            continue
        for table in extract_tables(chunk):
            header = ' '.join(table[0]).lower()
            if 'time' not in header:
                continue
            if 'tech' not in header and 'strength' not in header:
                continue
            if 'wave' in header or header.startswith('| time') or 'time' in table[0][0].lower():
                out.append((pattern, table))
    return out


def rows_to_events(rows: list[list[str]], pattern: str | None) -> list[dict]:
    header = [c.lower() for c in rows[0]]
    try:
        time_i = next(i for i, c in enumerate(header) if 'time' in c)
        tech_i = next((i for i, c in enumerate(header) if 'tech' in c), None)
        str_i = next((i for i, c in enumerate(header) if 'strength' in c), None)
        spawn_i = next((i for i, c in enumerate(header) if 'spawn' in c or 'direction' in c or 'target' in c or 'lock' in c), None)
        notes_i = next((i for i, c in enumerate(header) if 'note' in c), None)
    except StopIteration:
        return []

    events = []
    for row in rows[1:]:
        if len(row) <= time_i:
            continue
        t = mmss_to_seconds(row[time_i])
        if t is None:
            continue
        tech = parse_int_field(row[tech_i]) if tech_i is not None and tech_i < len(row) else None
        strength = parse_int_field(row[str_i]) if str_i is not None and str_i < len(row) else None
        ev = {'time': t, 'kind': 'attack_wave', 'label': 'Attack wave'}
        if tech is not None:
            ev['tech'] = tech
        if strength is not None:
            ev['strength'] = strength
        if spawn_i is not None and spawn_i < len(row) and row[spawn_i].strip():
            ev['spawn'] = row[spawn_i].strip()
        if pattern:
            ev['pattern'] = pattern
        if notes_i is not None and notes_i < len(row) and row[notes_i].strip():
            ev['notes'] = row[notes_i].strip()
        events.append(ev)
    return events


def manual_extra(mission: str) -> list[dict]:
    """Fixed-time objectives / mission-specific tables not caught by generic parser."""
    M = mission
    if M == 'Chain of Ascension':
        return [
            {'time': 540, 'kind': 'objective', 'label': 'Hybrid wave 1'},
            {'time': 900, 'kind': 'objective', 'label': 'Hybrid wave 2'},
            {'time': 1380, 'kind': 'objective', 'label': 'Hybrid wave 3'},
            {'time': 1800, 'kind': 'objective', 'label': 'Hybrid wave 4'},
            {'time': 600, 'kind': 'objective', 'label': 'Slayn Elemental 1'},
            {'time': 960, 'kind': 'objective', 'label': 'Slayn Elemental 2'},
        ]
    if M == 'Void Launch':
        return [
            {'time': 378, 'kind': 'objective', 'label': 'Shuttle wave 1', 'spawn': 'Middle'},
            {'time': 540, 'kind': 'objective', 'label': 'Shuttle wave 2'},
            {'time': 750, 'kind': 'objective', 'label': 'Shuttle wave 3'},
            {'time': 930, 'kind': 'objective', 'label': 'Shuttle wave 4'},
            {'time': 1080, 'kind': 'objective', 'label': 'Shuttle wave 5'},
            {'time': 1230, 'kind': 'objective', 'label': 'Shuttle wave 6'},
            {'time': 1380, 'kind': 'objective', 'label': 'Shuttle wave 7'},
        ]
    if M == 'Mist Opportunities':
        return [
            {'time': 255, 'kind': 'objective', 'label': 'Harvester bot wave 1 leaves'},
            {'time': 475, 'kind': 'objective', 'label': 'Harvester bot wave 2 leaves'},
            {'time': 730, 'kind': 'objective', 'label': 'Harvester bot wave 3 leaves'},
            {'time': 1100, 'kind': 'objective', 'label': 'Harvester bot wave 4 leaves'},
            {'time': 1500, 'kind': 'objective', 'label': 'Harvester bot wave 5 leaves'},
        ]
    if M == 'Part and Parcel':
        return [
            {'time': 480, 'kind': 'objective', 'label': 'Bonus train 1', 'spawn': 'Left'},
            {'time': 900, 'kind': 'objective', 'label': 'Bonus train 2', 'spawn': 'Right'},
        ]
    if M == 'Malwarfare':
        return [{'time': 216, 'kind': 'attack_wave', 'label': 'Attack wave', 'tech': 1, 'strength': 1}]
    if M == 'Lock & Load':
        return [
            {'time': 1140, 'kind': 'attack_wave', 'label': 'Attack wave', 'tech': 5, 'strength': 6, 'notes': 'Repeating cycle'},
            {'time': 1260, 'kind': 'attack_wave', 'label': 'Attack wave', 'tech': 6, 'strength': 6, 'notes': 'Repeating cycle'},
            {'time': 1380, 'kind': 'attack_wave', 'label': 'Attack wave', 'tech': 4, 'strength': 6, 'notes': 'Repeating cycle'},
            {'time': 1500, 'kind': 'attack_wave', 'label': 'Attack wave', 'tech': 4, 'strength': 6, 'notes': 'Repeating cycle'},
        ]
    if M == 'Miner Evacuation':
        return [
            {'time': 480, 'kind': 'attack_wave', 'label': 'Claimer wave', 'tech': 1, 'strength': 1},
            {'time': 912, 'kind': 'attack_wave', 'label': 'Claimer wave', 'tech': 2, 'strength': 2},
            {'time': 1158, 'kind': 'attack_wave', 'label': 'Claimer wave', 'tech': 1, 'strength': 1},
            {'time': 1164, 'kind': 'attack_wave', 'label': 'Claimer wave', 'tech': 1, 'strength': 1},
            {'time': 1560, 'kind': 'attack_wave', 'label': 'Claimer wave', 'tech': 4, 'strength': 4},
        ]
    if M == 'Rifts to Korhal':
        return [{'time': 700, 'kind': 'objective', 'label': 'Pirate ship 1'}]
    return []


def format_event(ev: dict) -> str:
    parts = [f"'label': '{ev['label']}'", f"'time': {ev['time']}"]
    for k in ('tech', 'strength', 'spawn', 'pattern', 'notes'):
        if k in ev:
            parts.append(f"'{k}': {ev[k]!r}" if k in ('spawn', 'pattern', 'notes', 'label') else f"'{k}': {ev[k]}")
    return '{' + ', '.join(parts) + '}'


def format_section(events: list) -> None:
    print("            'Brutal': [")
    for e in events:
        print(f"                {format_event(e)},")
    print("            ],")


def main():
    for mission in MISSION_PAGES:
        html = fetch_html(mission)
        events = []
        for pattern, table in find_attack_wave_tables(html):
            events.extend(rows_to_events(table, pattern))
        events.extend(manual_extra(mission))
        # dedupe by time+kind+label+pattern
        seen = set()
        unique = []
        for e in sorted(events, key=lambda x: (x['time'], x.get('pattern', ''), x['label'])):
            key = (e['time'], e['kind'], e['label'], e.get('pattern'))
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)

        attack_waves = [e for e in unique if e.get('kind') != 'objective']
        objectives = [e for e in unique if e.get('kind') == 'objective']

        print(f"\n    '{mission}': {{")
        print("        'attack_waves': {")
        format_section(attack_waves)
        print("        },")
        print("        'objectives': {")
        format_section(objectives)
        print("        }")
        print("    },")


if __name__ == '__main__':
    main()
