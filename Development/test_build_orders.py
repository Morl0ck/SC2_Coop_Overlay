"""Smoke tests for build order overlay modules."""
from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SCOFunctions.BuildOrderStore import BOS, parse_build_order_text
from SCOFunctions.BuildOrderTracker import BuildOrderTracker
from SCOFunctions.CommanderOCR import _match_in_text, _normalize_text
import SCOFunctions.CommanderSelection as CommanderSelection
from SCOFunctions.CommanderSelection import (
    SELECTION,
    _SelectionState,
    _commander_from_prestige,
    _match_difficulty,
    _match_prestige,
    _ocr_difficulty,
    _ocr_prestige,
)
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
    tracker.emitted = True
    tracker.current_commander = 'Raynor'
    tracker.display_cutoff = 300
    tracker.stall.reset(301)

    tracker.update({
        'players': [{'id': 1, 'type': 'user', 'name': 'Me'}, {'id': 2, 'type': 'user', 'name': 'Ally'}, {'id': 3, 'type': 'computer'}],
        'isReplay': False,
        'displayTime': 301,
    })
    assert any(e.get('buildOrderEndEvent') for e in events)
    assert tracker.done is True


def test_tracker_retries_when_no_steps() -> None:
    """A commander without steps at game start is retried within the display
    window instead of being marked done for the whole game."""
    original_settings = copy.deepcopy(SM.settings)
    original_entry = build_orders_defaults['Raynor']
    events = []
    try:
        SM.settings['build_orders'] = {
            'default_commander': 'Raynor',
            'display_minutes': 5,
            'ocr_enabled': False,
            'use_custom': {},
            'custom': {},
        }
        build_orders_defaults['Raynor'] = dict(original_entry, steps=[])

        tracker = BuildOrderTracker(send_event=events.append)
        tracker._startup_seen = True
        game = {
            'players': [{'id': 1, 'type': 'user'}, {'id': 2, 'type': 'user'}, {'id': 3, 'type': 'computer'}],
            'isReplay': False,
            'displayTime': 10,
        }
        tracker.update(game)
        assert not any(e.get('buildOrderStartEvent') for e in events)
        assert tracker.in_game and not tracker.done and not tracker.emitted

        # Steps become available mid-game (stand-in for the user saving a
        # custom build order) -> the next poll emits the start event.
        build_orders_defaults['Raynor'] = original_entry
        tracker.update(dict(game, displayTime=15))
        assert any(e.get('buildOrderStartEvent') for e in events)
        assert tracker.emitted
    finally:
        build_orders_defaults['Raynor'] = original_entry
        SM.settings = original_settings


def test_tracker_starts_next_game_when_clock_resets_without_menu_poll() -> None:
    original_settings = copy.deepcopy(SM.settings)
    events = []
    try:
        SM.settings['build_orders'] = {
            'default_commander': 'Mengsk',
            'display_minutes': 5,
            'ocr_enabled': True,
            'use_custom': {},
            'custom': {},
        }
        game = {
            'players': [
                {'id': 1, 'type': 'user'},
                {'id': 2, 'type': 'user'},
                {'id': 3, 'type': 'computer'},
            ],
            'isReplay': False,
            'displayTime': 2,
        }

        tracker = BuildOrderTracker(send_event=events.append)
        tracker._startup_seen = True
        SELECTION.update({'commander': 'Mengsk'})
        tracker.update(game)
        tracker.update(dict(game, displayTime=301))
        assert tracker.done

        # The API can keep reporting the old match and then jump straight into
        # the next one without returning a menu state in between.
        tracker.update(dict(game, displayTime=900))
        SELECTION.update({'commander': 'Stetmann'})
        tracker.update(dict(game, displayTime=4))

        starts = [event for event in events if event.get('buildOrderStartEvent')]
        assert [event['commander'] for event in starts] == ['Mengsk', 'Stetmann']
    finally:
        SELECTION.clear()
        SM.settings = original_settings


def test_tracker_reuses_last_detection_when_rapid_requeue_has_no_fresh_ocr() -> None:
    original_settings = copy.deepcopy(SM.settings)
    events = []
    try:
        SM.settings['build_orders'] = {
            'default_commander': 'Stetmann',
            'display_minutes': 5,
            'ocr_enabled': True,
            'use_custom': {},
            'custom': {},
        }
        game = {
            'players': [
                {'id': 1, 'type': 'user'},
                {'id': 2, 'type': 'user'},
                {'id': 3, 'type': 'computer'},
            ],
            'isReplay': False,
            'displayTime': 2,
        }

        tracker = BuildOrderTracker(send_event=events.append)
        tracker._startup_seen = True
        SELECTION.update({'commander': 'Mengsk'})
        tracker.update(game)

        # End the first game's display and enter another game without a menu
        # poll or a new click-triggered OCR result.
        tracker.update(dict(game, displayTime=301))
        assert tracker.done
        tracker.update(dict(game, displayTime=4))

        starts = [event for event in events if event.get('buildOrderStartEvent')]
        assert [event['commander'] for event in starts] == ['Mengsk', 'Mengsk']
        assert tracker.commander_source == 'previous selection OCR'
    finally:
        SELECTION.clear()
        SM.settings = original_settings


def test_ocr_fuzzy_match() -> None:
    text = _normalize_text('Commander: Stetmann  Ally: Raynor')
    match = _match_in_text(text, list(build_orders_defaults.keys()))
    assert match is not None
    assert match[0] in {'Stetmann', 'Raynor'}


def test_prestige_match_ignores_surrounding_ocr_noise() -> None:
    noisy = '600\nsi Is t 400:\nigna avan aD'
    prestige = _match_prestige('Stetmann', noisy)
    assert prestige is not None
    assert prestige['title'] == 'Signal Savant'

    inferred = _commander_from_prestige(noisy)
    assert inferred is not None
    assert inferred['commander'] == 'Stetmann'


def test_prestige_ocr_uses_block_mode_then_single_line_retry() -> None:
    original_ocr = CommanderSelection._ocr_image_to_text
    calls = []
    responses = iter(['|  Sseeess', 'Signal Savant'])
    try:
        def fake_ocr(image, psm=7):
            calls.append(psm)
            return next(responses)

        CommanderSelection._ocr_image_to_text = fake_ocr
        prestige, raw = _ocr_prestige(object(), 'Stetmann')
        assert prestige is not None
        assert prestige['title'] == 'Signal Savant'
        assert 'Signal Savant' in raw
        assert calls == [6, 7]
    finally:
        CommanderSelection._ocr_image_to_text = original_ocr


def test_difficulty_match_from_noisy_ocr() -> None:
    assert _match_difficulty('] BRUTAL\n---\nBONUS XP 100%') == 'Brutal'
    assert _match_difficulty('peal) nel\nBONUS XP 100%') == 'Brutal'
    assert _match_difficulty('BONUS XP. 100%') == 'Brutal'
    assert _match_difficulty('HARD\nBONUS XP 50%') == 'Hard'
    assert _match_difficulty('BONUS XP. 50%') == 'Hard'
    assert _match_difficulty('BONUS XP. SO%') == 'Hard'
    assert _match_difficulty('| H4RD |') == 'Hard'
    assert _match_difficulty('| HARO |') == 'Hard'


def test_difficulty_ocr_uses_multiline_then_focused_retry() -> None:
    class FakeImage:
        size = (200, 100)

        def crop(self, box):
            assert box == (0, 0, 200, 62)
            return self

    original_ocr = CommanderSelection._ocr_image_to_text
    calls = []
    responses = iter(['BONUS XP', '| BRUTAL |'])
    try:
        def fake_ocr(image, psm=7):
            calls.append(psm)
            return next(responses)

        CommanderSelection._ocr_image_to_text = fake_ocr
        difficulty, raw = _ocr_difficulty(FakeImage())
        assert difficulty == 'Brutal'
        assert 'BRUTAL' in raw
        assert calls == [6, 7]
    finally:
        CommanderSelection._ocr_image_to_text = original_ocr


def test_difficulty_ocr_recovers_noisy_hard_from_focused_retry() -> None:
    class FakeImage:
        size = (200, 100)

        def crop(self, box):
            assert box == (0, 0, 200, 62)
            return self

    original_ocr = CommanderSelection._ocr_image_to_text
    calls = []
    responses = iter(['unreadable', '| H4RD |'])
    try:
        def fake_ocr(image, psm=7):
            calls.append(psm)
            return next(responses)

        CommanderSelection._ocr_image_to_text = fake_ocr
        difficulty, raw = _ocr_difficulty(FakeImage())
        assert difficulty == 'Hard'
        assert 'H4RD' in raw
        assert calls == [6, 7]
    finally:
        CommanderSelection._ocr_image_to_text = original_ocr


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
    tracker._startup_seen = True
    tracker.update({
        'players': [
            {'id': 1, 'type': 'user'},
            {'id': 2, 'type': 'user'},
            {'id': 3, 'type': 'computer'},
        ],
        'isReplay': False,
        'displayTime': 100,
    })
    tracker.update({'players': [], 'isReplay': False, 'displayTime': 0})
    assert SELECTION.get(max_age=None) is None


def test_new_selection_survives_stale_score_screen_menu_transition() -> None:
    original = copy.deepcopy(SM.settings)
    events = []
    try:
        SM.settings['build_orders'] = {
            'default_commander': 'Mengsk',
            'display_minutes': 5,
            'ocr_enabled': True,
            'use_custom': {},
            'custom': {},
        }

        mission = MissionTracker(send_event=lambda event: None)
        mission._startup_seen = True
        mission._suppress_restart = True
        mission._suppressed_display_time = 100
        stale_score_screen = {
            'players': [
                {'id': 1, 'type': 'user'},
                {'id': 2, 'type': 'user'},
                {'id': 3, 'type': 'computer'},
            ],
            'isReplay': False,
            'displayTime': 100,
        }
        mission.update(stale_score_screen)
        assert mission.pending_game

        SELECTION.update({'commander': 'Stetmann', 'difficulty': 'Brutal'})
        mission.update({'players': [], 'isReplay': False, 'displayTime': 0})
        assert SELECTION.get(max_age=None)['commander'] == 'Stetmann'

        build_order = BuildOrderTracker(send_event=events.append)
        build_order._startup_seen = True
        build_order.update(dict(stale_score_screen, displayTime=5))
        assert any(
            event.get('buildOrderStartEvent') and event.get('commander') == 'Stetmann'
            for event in events
        )
    finally:
        SELECTION.clear()
        SM.settings = original


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
    test_tracker_retries_when_no_steps()
    test_tracker_starts_next_game_when_clock_resets_without_menu_poll()
    test_tracker_reuses_last_detection_when_rapid_requeue_has_no_fresh_ocr()
    test_ocr_fuzzy_match()
    test_prestige_match_ignores_surrounding_ocr_noise()
    test_prestige_ocr_uses_block_mode_then_single_line_retry()
    test_difficulty_match_from_noisy_ocr()
    test_difficulty_ocr_uses_multiline_then_focused_retry()
    test_difficulty_ocr_recovers_noisy_hard_from_focused_retry()
    test_selection_cache_expires()
    test_build_tracker_consumes_selection()
    test_mission_difficulty_snapshot_survives_cache_clear()
    test_idle_disconnect_does_not_clear_selection()
    test_pending_mission_clears_selection_on_menu_return()
    test_new_selection_survives_stale_score_screen_menu_transition()
    test_settings_repair_malformed_nested_values()
    print('All build order smoke tests passed.')
