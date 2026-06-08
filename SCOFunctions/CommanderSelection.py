"""
Click-triggered OCR of the co-op lobby selection screen.

Instead of repeatedly OCR-ing the in-game UI (unreliable - it often reads the
ally), this watches for the user clicking on the co-op commander selection
screen and, one second after the last click (debounced), captures three regions:

    * commander name   (red box in the reference screenshot)
    * prestige title   (yellow box)
    * difficulty       (green box)

The most recent reading is cached in ``SELECTION`` and consumed by the build
order tracker (commander) and mission tracker (difficulty) when a game starts.

The global mouse hook is gated so detection only runs while StarCraft II is the
foreground window and we are NOT already in a game.
"""
from __future__ import annotations

import ctypes
import difflib
import threading
import time
import traceback
from typing import Any, Dict, Optional

from SCOFunctions.CommanderOCR import (
    _canonical_commanders,
    _match_in_text,
    _normalize_text,
    _ocr_image_to_text,
    commander_display_name,
    grab_screen_region,
)
from SCOFunctions.MLogging import Logger
from SCOFunctions.SC2Dictionaries import DIFFICULTIES, prestige_names
from SCOFunctions.Settings import Setting_manager as SM

logger = Logger('OCR', Logger.levels.INFO)

# Seconds to wait after the last click before running detection.
DEBOUNCE_SECONDS = 0.5
# Ignore lobby readings left behind for an unusually long time.
SELECTION_MAX_AGE_SECONDS = 30 * 60

# Screen regions as (left, top, right, bottom) fractions of the captured
# monitor. Calibrated from the co-op lobby on a 16:9 display; they scale with
# resolution as long as the aspect ratio is 16:9.
DEFAULT_REGIONS: Dict[str, tuple] = {
    'commander': (0.010, 0.420, 0.330, 0.510),
    'prestige': (0.135, 0.548, 0.560, 0.612),
    'difficulty': (0.290, 0.835, 0.450, 0.930),
}


def _regions() -> Dict[str, tuple]:
    cfg = SM.settings.get('build_orders', {}).get('ocr_regions')
    if isinstance(cfg, dict):
        merged = dict(DEFAULT_REGIONS)
        for key, value in cfg.items():
            if key in merged and isinstance(value, (list, tuple)) and len(value) == 4:
                merged[key] = tuple(value)
        return merged
    return DEFAULT_REGIONS


def sc2_is_foreground() -> bool:
    """True when the focused window looks like the StarCraft II client."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return 'StarCraft II' in buffer.value
    except Exception:
        return False


def _match_prestige(commander: str, text: str) -> Optional[Dict[str, Any]]:
    norm = _normalize_text(text)
    if not norm:
        return None
    titles = prestige_names.get(commander, {})
    best_idx, best_title, best_score = None, None, 0.0
    for idx, title in titles.items():
        normalized_title = _normalize_text(title)
        if not normalized_title:
            continue
        score = difflib.SequenceMatcher(None, normalized_title, norm).ratio()
        if normalized_title in norm or norm in normalized_title:
            score = max(score, 0.9)
        if score > best_score:
            best_idx, best_title, best_score = idx, title, score
    if best_title and best_score >= 0.6:
        return {'index': best_idx, 'title': best_title, 'score': best_score}
    return None


def _commander_from_prestige(text: str) -> Optional[Dict[str, Any]]:
    """Infer the commander from the prestige title alone.

    The commander-name region OCR is flaky (it sometimes reads empty), but the
    prestige titles are unique across all commanders, so a confident prestige
    match doubles as a commander identification.
    """
    norm = _normalize_text(text)
    if not norm:
        return None
    best = None  # (commander, index, title, score)
    for commander, titles in prestige_names.items():
        for idx, title in titles.items():
            normalized_title = _normalize_text(title)
            if not normalized_title:
                continue
            score = difflib.SequenceMatcher(None, normalized_title, norm).ratio()
            if normalized_title in norm or norm in normalized_title:
                score = max(score, 0.9)
            if best is None or score > best[3]:
                best = (commander, idx, title, score)
    # Require a fairly strong match: a wrong commander is worse than none.
    if best and best[3] >= 0.75:
        return {
            'commander': best[0],
            'prestige': {'index': best[1], 'title': best[2], 'score': best[3]},
        }
    return None


def _match_difficulty(text: str) -> Optional[str]:
    # Check the raw text for a Brutal+ marker first - normalization strips '+'.
    raw = (text or '').lower()
    if 'brutal' in raw or 'b+' in raw.replace(' ', ''):
        return 'Brutal'
    norm = _normalize_text(text)
    if not norm:
        return None
    for name in ('casual', 'normal', 'hard'):
        if name in norm:
            return name.capitalize()
    best, best_score = None, 0.0
    for name in DIFFICULTIES:
        score = difflib.SequenceMatcher(None, name.lower(), norm).ratio()
        if score > best_score:
            best, best_score = name, score
    return best if best_score >= 0.7 else None


def detect_selection(monitor: Optional[int] = None, log_regions: bool = False) -> Optional[Dict[str, Any]]:
    """Capture and OCR the selection-screen regions.

    Returns ``{'commander', 'prestige', 'difficulty', 'score'}`` or ``None`` if
    the commander region doesn't confidently read a commander name (which also
    means we're probably not on the lobby screen).

    When ``log_regions`` is True the raw OCR text of each region is logged - use
    this to calibrate the region coordinates.
    """
    image = grab_screen_region(monitor)
    if image is None:
        if log_regions:
            logger.info('Selection OCR: screen capture returned nothing (check the "monitor" setting)')
        return None

    width, height = image.size
    regions = _regions()

    def crop(name: str):
        left, top, right, bottom = regions[name]
        return image.crop((int(left * width), int(top * height), int(right * width), int(bottom * height)))

    commander_raw = _ocr_image_to_text(crop('commander'))
    prestige_raw = _ocr_image_to_text(crop('prestige'))
    difficulty_raw = _ocr_image_to_text(crop('difficulty'))

    if log_regions:
        logger.info(
            f'Selection OCR regions (capture {width}x{height}): '
            f'commander={commander_raw.strip()!r} '
            f'prestige={prestige_raw.strip()!r} '
            f'difficulty={difficulty_raw.strip()!r}'
        )

    difficulty = _match_difficulty(difficulty_raw)

    commander_match = _match_in_text(commander_raw, _canonical_commanders())
    if commander_match:
        commander = commander_match[0]
        return {
            'commander': commander,
            'prestige': _match_prestige(commander, prestige_raw),
            'difficulty': difficulty,
            'score': commander_match[1],
        }

    # Commander-name region failed to read (it's flaky). Fall back to inferring
    # the commander from the prestige title, which is unique per commander.
    fallback = _commander_from_prestige(prestige_raw)
    if fallback:
        prestige = fallback['prestige']
        if log_regions:
            logger.info(
                f"Selection OCR: commander region unreadable; inferred "
                f"{commander_display_name(fallback['commander'])} from prestige "
                f"'{prestige['title']}'"
            )
        return {
            'commander': fallback['commander'],
            'prestige': prestige,
            'difficulty': difficulty,
            'score': prestige['score'],
        }

    return None


class _SelectionState:
    """Thread-safe cache of the most recent selection-screen reading."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Optional[Dict[str, Any]] = None

    def update(self, data: Dict[str, Any]) -> None:
        with self._lock:
            stored = dict(data)
            stored['time'] = time.time()
            self._data = stored

    def get(self, max_age: Optional[float] = SELECTION_MAX_AGE_SECONDS) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._data and max_age is not None:
                age = time.time() - self._data.get('time', 0)
                if age > max_age:
                    self._data = None
            return dict(self._data) if self._data else None

    def clear(self) -> None:
        with self._lock:
            self._data = None


SELECTION = _SelectionState()

# --- watcher ---------------------------------------------------------------
_timer: Optional[threading.Timer] = None
_timer_lock = threading.Lock()
_in_game = False
_hooked = False
_click_seen = False
# Throttle for the "click ignored" diagnostic so a game's worth of clicks
# doesn't flood the log; we still want to see *why* clicks are dropped.
_last_skip_log = 0.0
_SKIP_LOG_INTERVAL = 5.0


def set_in_game(flag: bool) -> None:
    """Called by the game-state poller so we skip detection during a game."""
    global _in_game
    _in_game = bool(flag)


def _run_detection() -> None:
    # Free the slot so a click during/after this run can schedule the next one.
    global _timer
    with _timer_lock:
        _timer = None
    try:
        foreground = sc2_is_foreground()
        if _in_game or not foreground:
            logger.info(f'Selection OCR skipped (in_game={_in_game}, sc2_foreground={foreground})')
            return
        result = detect_selection(log_regions=True)
        if not result:
            logger.info('Selection OCR: no commander recognised in the commander region (calibration may be off)')
            return
        SELECTION.update(result)
        prestige = result.get('prestige')
        prestige_title = prestige['title'] if prestige else 'unknown'
        logger.info(
            f"Selection detected: {commander_display_name(result['commander'])} "
            f"| prestige: {prestige_title} | difficulty: {result.get('difficulty') or 'unknown'}"
        )
    except Exception:
        logger.error(f'Selection detection failed:\n{traceback.format_exc()}')


def _on_click() -> None:
    # Wrapped in try/except: boppreh's listener loop has no error handling, so an
    # unhandled exception in a handler would silently kill the click thread.
    try:
        global _click_seen
        if not _click_seen:
            _click_seen = True
            logger.info('Selection watcher: receiving mouse clicks')

        foreground = sc2_is_foreground()
        if _in_game or not foreground:
            # This used to drop the click silently, which made "only one
            # detection" impossible to diagnose. Log (throttled) the reason so
            # we can see whether the live-game gate or the foreground check is
            # eating the clicks.
            global _last_skip_log
            now = time.time()
            if now - _last_skip_log >= _SKIP_LOG_INTERVAL:
                _last_skip_log = now
                logger.info(
                    'Selection watcher: click ignored '
                    f'(in_game={_in_game}, sc2_foreground={foreground})'
                )
            return
        global _timer
        with _timer_lock:
            # Throttle, not debounce: if a detection is already pending, let it
            # run. A burst of fast clicks collapses into one detection that
            # captures whatever is selected ~1s later (i.e. your final choice).
            if _timer is not None and _timer.is_alive():
                logger.info('Selection watcher: click (detection already pending, throttled)')
                return
            _timer = threading.Timer(DEBOUNCE_SECONDS, _run_detection)
            _timer.daemon = True
            _timer.start()
            logger.info('Selection watcher: click -> detection scheduled in '
                        f'{DEBOUNCE_SECONDS:g}s')
    except Exception:
        logger.error(f'Selection watcher click handler failed:\n{traceback.format_exc()}')


def start_watcher() -> None:
    """Register the global left-click hook (idempotent)."""
    global _hooked
    if _hooked:
        return
    try:
        import mouse
    except ImportError:
        logger.error('mouse package not installed; click-triggered OCR disabled')
        return
    try:
        mouse.on_click(_on_click)
        _hooked = True
        logger.info('Commander selection watcher started (click-triggered OCR)')
    except Exception:
        logger.error(f'Failed to start selection watcher:\n{traceback.format_exc()}')


def stop_watcher() -> None:
    global _hooked, _timer
    with _timer_lock:
        if _timer is not None:
            _timer.cancel()
            _timer = None
    if not _hooked:
        return
    try:
        import mouse
        mouse.unhook_all()
    except Exception:
        pass
    _hooked = False
