"""Print co-op difficulty parsed from the live SC2 stream API.

Run while SC2 is in a co-op game (or on the score screen after one):
    .\\venv\\Scripts\\python.exe Development/probe_live_difficulty.py
"""
from __future__ import annotations

import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.CoopDifficulty import parse_coop_difficulty, resolve_mission_difficulty
from SCOFunctions.IdentifyMap import identify_map

URL = 'http://localhost:6119/game'


def main() -> None:
    print(f'Polling {URL} (Ctrl+C to stop)...')
    session = requests.Session()
    last_sig = None

    while True:
        try:
            resp = session.get(URL, timeout=3).json()
        except requests.exceptions.ConnectionError:
            print('SC2 not running or API unreachable')
            time.sleep(3)
            continue
        except Exception as exc:
            print(f'Error: {exc}')
            time.sleep(3)
            continue

        players = resp.get('players', [])
        parsed = parse_coop_difficulty(players, resp)
        resolved = resolve_mission_difficulty(players, resp)
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
                'difficulty': p.get('difficulty'),
            }
            for p in players
            if p.get('id') in (3, 4) or p.get('type') in ('computer', 'Computer')
        ]

        sig = (resp.get('displayTime'), resp.get('isReplay'), parsed, resolved, mission)
        if sig != last_sig:
            last_sig = sig
            print('-' * 60)
            print(f"displayTime={resp.get('displayTime')}  isReplay={resp.get('isReplay')}")
            print(f'map={mission or "?"}  parsed={parsed}  resolved={resolved}')
            if amon:
                print('computer/amon players:')
                for row in amon:
                    print(f"  {row}")
            top_keys = {k: resp[k] for k in resp if k not in ('players',) and 'difficulty' in k.lower()}
            if top_keys:
                print('top-level difficulty fields:', top_keys)
            if parsed is None and players:
                print('raw player keys sample:', sorted(set().union(*(p.keys() for p in players))))

        time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped.')
