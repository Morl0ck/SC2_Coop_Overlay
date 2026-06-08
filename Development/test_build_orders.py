"""Smoke tests for build order overlay modules."""
from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.BuildOrderStore import BOS, parse_build_order_text
from SCOFunctions.BuildOrderTracker import BuildOrderTracker
from SCOFunctions.CommanderOCR import _match_in_text, _normalize_text
from SCOFunctions.CommanderSelection import SELECTION, _SelectionState
from SCOFunctions.MissionTracker import MissionTracker
from SCOFunctions.SC2Dictionaries.BuildOrders import build_orders_defaults
from SCOFunctions.Settings import CSettings, Setting_manager as SM, update_with_defaults


def test_bundled_commanders_have_steps() -> None:
    missing = [name for name, data in build_orders_defaults.items() if not data.get('steps')]
    assert not missing, f'Missing build order steps: {missing}'


def test_custom_override() -> None:
    original = copy.deepcopy(SM.settings)
    try:
        SM.settings.setdefault('build_orders', {})
        SM.settings['build_orders']['use_custom'] = {'Raynor': True}
        SM.settings['build_orders']['custom'] = {'Raynor': '14 Supply Depot\n16 Barracks'}
        order = BOS.get('Raynor')
        assert order is not None
        assert order['source'] == 'custom'
        assert order['steps'] == ['14 Supply Depot', '16 Barracks']
    finally:
        SM.settings = original


def test_tracker_display_cutoff() -> None:
    events = []

    tracker = BuildOrderTracker(send_event=events.append)
    tracker.in_game = True
    tracker.current_commander = 'Raynor'
    tracker.display_cutoff = 300
    tracker.last_display_time = 301

    tracker.update({
        'players': [{'id': 1, 'type': 'user', 'name': 'Me'}, {'id': 2, 'type': 'user', 'name': 'Ally'}, {'id': 3, 'type': 'computer'}],
        'isReplay': False,
        'displayTime': 301,
    })
    assert any(e.get('buildOrderEndEvent') for e in events)
    assert tracker.done is True


def test_ocr_fuzzy_match() -> None:
    text = _normalize_text('Commander: Stetmann  Ally: Raynor')
    match = _match_in_text(text, list(build_orders_defaults.keys()))
    assert match is not None
    assert match[0] in {'Stetmann', 'Raynor'}


def test_selection_cache_expires() -> None:
    state = _SelectionState()
    state.update({'commander': 'Raynor'})
    assert state.get() is not None
    assert state.get(max_age=-1) is None


def test_build_tracker_consumes_selection() -> None:
    original = copy.deepcopy(SM.settings)
    events = []
    try:
        SM.settings['build_orders'] = {
            'default_commander': 'Artanis',
            'display_minutes': 5,
            'ocr_enabled': True,
            'use_custom': {},
            'custom': {},
        }
        SELECTION.update({'commander': 'Raynor', 'difficulty': 'Hard'})
        tracker = BuildOrderTracker(send_event=events.append)
        tracker._startup_seen = True
        tracker.update({
            'players': [
                {'id': 1, 'type': 'user'},
                {'id': 2, 'type': 'user'},
                {'id': 3, 'type': 'computer'},
            ],
            'isReplay': False,
            'displayTime': 1,
        })
        assert any(e.get('commander') == 'Raynor' for e in events)
        assert SELECTION.get(max_age=None) is None
    finally:
        SELECTION.clear()
        SM.settings = original


def test_mission_difficulty_snapshot_survives_cache_clear() -> None:
    original = copy.deepcopy(SM.settings)
    try:
        SM.settings.setdefault('mission_overlay', {})['difficulty'] = 'auto'
        SELECTION.update({'commander': 'Raynor', 'difficulty': 'Hard'})
        tracker = MissionTracker(send_event=lambda event: None)
        assert tracker._settings_requested_difficulty([], {}) == 'Hard'
        SELECTION.clear()
        assert tracker._settings_requested_difficulty([], {}) == 'Hard'
    finally:
        SELECTION.clear()
        SM.settings = original


def test_idle_disconnect_does_not_clear_selection() -> None:
    SELECTION.update({'commander': 'Raynor', 'difficulty': 'Hard'})
    BuildOrderTracker(send_event=lambda event: None).on_disconnect()
    assert SELECTION.get(max_age=None) is not None
    SELECTION.clear()


def test_pending_mission_clears_selection_on_menu_return() -> None:
    SELECTION.update({'commander': 'Raynor', 'difficulty': 'Hard'})
    tracker = MissionTracker(send_event=lambda event: None)
    tracker.pending_game = True
    tracker.update({'players': [], 'isReplay': False, 'displayTime': 0})
    assert SELECTION.get(max_age=None) is None


def test_settings_repair_malformed_nested_values() -> None:
    settings = CSettings()
    loaded = {
        'mission_overlay': None,
        'build_orders': {'custom': None},
    }
    update_with_defaults(loaded, settings.default_settings)
    assert isinstance(loaded['mission_overlay'], dict)
    assert isinstance(loaded['build_orders']['custom'], dict)

    loaded['mission_overlay']['opacity'] = 0.1
    assert settings.default_settings['mission_overlay']['opacity'] == 0.9


if __name__ == '__main__':
    test_bundled_commanders_have_steps()
    test_custom_override()
    test_tracker_display_cutoff()
    test_ocr_fuzzy_match()
    test_selection_cache_expires()
    test_build_tracker_consumes_selection()
    test_mission_difficulty_snapshot_survives_cache_clear()
    test_idle_disconnect_does_not_clear_selection()
    test_pending_mission_clears_selection_on_menu_return()
    test_settings_repair_malformed_nested_values()
    print('All build order smoke tests passed.')
