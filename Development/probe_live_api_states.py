"""Log :6119/game state transitions during lobby -> load -> in-game.

Run while joining a co-op match:
    python Development/probe_live_api_states.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.CoopDifficulty import parse_coop_difficulty, resolve_mission_difficulty
from SCOFunctions.IdentifyMap import identify_map

URL = 'http://localhost:6119/game'
OUT = os.path.join(os.path.dirname(__file__), 'probe_live_api_output.jsonl')


def phase(display_time, is_replay, players) -> str:
    if is_replay:
        return 'replay'
    n = len(players)
    if display_time and display_time > 0:
        return 'in_game'
    if n > 2:
        return 'lobby_or_loading'
    if n > 0:
        return 'menu_with_players'
    return 'idle'


def snapshot(resp: dict) -> dict:
    players = resp.get('players', [])
    mission = None
    try:
        mission = identify_map(players)
    except Exception:
        pass
    amon = [
        {
            'id': p.get('id'),
            'name': p.get('name'),
            'type': p.get('type'),
            'race': p.get('race'),
            'difficulty': p.get('difficulty'),
        }
        for p in players
        if p.get('id') in (3, 4) or str(p.get('type', '')).lower() == 'computer'
    ]
    humans = [
        {'id': p.get('id'), 'name': p.get('name'), 'type': p.get('type'), 'race': p.get('race')}
        for p in players
        if p.get('id') in (1, 2)
    ]
    top = {k: resp[k] for k in resp if k != 'players'}
    return {
        'ts': datetime.now().isoformat(timespec='seconds'),
        'phase': phase(resp.get('displayTime', 0), resp.get('isReplay', True), players),
        'displayTime': resp.get('displayTime'),
        'isReplay': resp.get('isReplay'),
        'player_count': len(players),
        'mission': mission,
        'parsed_difficulty': parse_coop_difficulty(players, resp),
        'resolved_difficulty': resolve_mission_difficulty(players, resp),
        'humans': humans,
        'amon': amon,
        'top_level': top,
    }


def main() -> None:
    print(f'Polling {URL} -> {OUT}')
    print('Join a co-op match now. Ctrl+C to stop.\n')
    session = requests.Session()
    last_sig = None

    with open(OUT, 'w', encoding='utf-8') as f:
        while True:
            try:
                resp = session.get(URL, timeout=3).json()
            except requests.exceptions.ConnectionError:
                if last_sig != ('down',):
                    last_sig = ('down',)
                    print(f"[{datetime.now():%H:%M:%S}] SC2 not running / API unreachable")
                time.sleep(3)
                continue
            except Exception as exc:
                print(f'Error: {exc}')
                time.sleep(3)
                continue

            snap = snapshot(resp)
            sig = (
                snap['phase'],
                snap['displayTime'],
                snap['isReplay'],
                snap['mission'],
                snap['parsed_difficulty'],
                snap['player_count'],
                tuple((a['id'], a.get('difficulty')) for a in snap['amon']),
            )
            if sig != last_sig:
                last_sig = sig
                line = json.dumps(snap, ensure_ascii=False)
                f.write(line + '\n')
                f.flush()
                print('-' * 72)
                print(
                    f"[{snap['ts']}] phase={snap['phase']}  displayTime={snap['displayTime']}  "
                    f"mission={snap['mission'] or '?'}  parsed_diff={snap['parsed_difficulty']}  "
                    f"resolved={snap['resolved_difficulty']}"
                )
                if snap['humans']:
                    print('  humans:', snap['humans'])
                if snap['amon']:
                    print('  amon/computer:', snap['amon'])
                diff_keys = {k: v for k, v in snap['top_level'].items() if 'difficult' in k.lower() or 'brutal' in k.lower()}
                if diff_keys:
                    print('  top-level difficulty fields:', diff_keys)
                if snap['phase'] in ('lobby_or_loading', 'in_game') and not snap['parsed_difficulty']:
                    print('  NOTE: no difficulty parsed yet')

            time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\nStopped. Full log: {OUT}')
