"""
Click-triggered OCR of the co-op lobby selection screen.

Instead of repeatedly OCR-ing the in-game UI (unreliable - it often reads the
ally), this watches for the user clicking on the co-op commander selection
screen and, shortly after the last click (trailing-edge debounce of
``DEBOUNCE_SECONDS``), captures three regions:

    * commander name   (red box in the reference screenshot)
    * prestige title   (yellow box)
    * difficulty       (green box)

Regions are computed relative to the StarCraft II window's client rect when it
can be resolved (works in windowed mode and on any monitor), falling back to
fractions of the configured monitor otherwise.

The most recent reading is cached in ``SELECTION`` and consumed by the build
order tracker (commander) and mission tracker (difficulty) when a game starts.

The global mouse hook is gated so detection only runs while StarCraft II is the
foreground window and we are NOT already in a game.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import difflib
import os
import re
import threading
import time
import traceback
from typing import Any, Dict, Optional, Tuple

from SCOFunctions.CommanderOCR import (
    _canonical_commanders,
    _match_in_text,
    _normalize_text,
    _ocr_image_to_text,
    commander_display_name,
    grab_screen_region,
    grab_screen_regions,
)
from SCOFunctions.MLogging import Logger
from SCOFunctions.SC2Dictionaries import DIFFICULTIES, prestige_names
from SCOFunctions.Settings import Setting_manager as SM

logger = Logger('OCR', Logger.levels.INFO)

# Seconds to wait after the *last* click before running detection.
DEBOUNCE_SECONDS = 0.5
# Ignore lobby readings left behind for an unusually long time.
SELECTION_MAX_AGE_SECONDS = 30 * 60

# Screen regions as (left, top, right, bottom) fractions of the SC2 client
# area (or of the captured monitor in the fallback path). Calibrated from the
# co-op lobby on a 16:9 display.
DEFAULT_REGIONS: Dict[str, tuple] = {
    'commander': (0.010, 0.420, 0.330, 0.510),
    'prestige': (0.135, 0.548, 0.560, 0.612),
    'difficulty': (0.290, 0.835, 0.450, 0.930),
}

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _regions() -> Dict[str, tuple]:
    cfg = SM.settings.get('build_orders', {}).get('ocr_regions')
    if isinstance(cfg, dict):
        merged = dict(DEFAULT_REGIONS)
        for key, value in cfg.items():
            if key in merged and isinstance(value, (list, tuple)) and len(value) == 4:
                merged[key] = tuple(value)
        return merged
    return DEFAULT_REGIONS


def _ocr_debug_enabled() -> bool:
    return bool(SM.settings.get('build_orders', {}).get('ocr_debug', False))


def _window_process_is_sc2(hwnd) -> bool:
    """Check the window's process executable to weed out impostor windows
    (a browser tab or folder titled 'StarCraft II' would pass the title check)."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return True
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            # Can't inspect the process (permissions); trust the title check.
            return True
        try:
            buffer = ctypes.create_unicode_buffer(1024)
            size = ctypes.wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                exe = os.path.basename(buffer.value).lower()
                return exe.startswith('sc2')
            return True
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return True


def sc2_foreground_client_rect() -> Optional[Tuple[int, int, int, int]]:
    """``(left, top, width, height)`` of the SC2 client area in screen pixels,
    or None when the foreground window isn't the StarCraft II client."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if 'StarCraft II' not in buffer.value:
            return None
        if not _window_process_is_sc2(hwnd):
            return None

        rect = ctypes.wintypes.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return None
        origin = ctypes.wintypes.POINT(0, 0)
        if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            return None
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        # A minimized/degenerate window is useless for OCR.
        if width < 200 or height < 200:
            return None
        return (origin.x, origin.y, width, height)
    except Exception:
        return None


def sc2_is_foreground() -> bool:
    """True when the focused window is the StarCraft II client."""
    return sc2_foreground_client_rect() is not None


def _prestige_text_score(title: str, text: str) -> float:
    """Score a title against OCR text that may contain surrounding UI noise."""
    expected = _normalize_text(title)
    observed = _normalize_text(text)
    if not expected or not observed:
        return 0.0

    best = difflib.SequenceMatcher(None, expected, observed).ratio()
    if expected in observed:
        best = max(best, 0.95)
    if len(observed) >= max(4, len(expected) // 2) and observed in expected:
        best = max(best, 0.9)

    words = observed.split()
    target_words = len(expected.split())
    for size in range(max(1, target_words - 1), target_words + 2):
        for start in range(max(0, len(words) - size + 1)):
            window = ' '.join(words[start:start + size])
            best = max(best, difflib.SequenceMatcher(None, expected, window).ratio())
    return best


def _match_prestige(commander: str, text: str) -> Optional[Dict[str, Any]]:
    if not _normalize_text(text):
        return None
    titles = prestige_names.get(commander, {})
    best_idx, best_title, best_score = None, None, 0.0
    for idx, title in titles.items():
        score = _prestige_text_score(title, text)
        if score > best_score:
            best_idx, best_title, best_score = idx, title, score
    if best_title and best_score >= 0.6:
        return {'index': best_idx, 'title': best_title, 'score': best_score}
    return None


def _commander_from_prestige(text: str) -> Optional[Dict[str, Any]]:
    """Infer the commander from the prestige title alone.

    The commander-name region OCR can read empty, but the prestige titles are
    unique across all commanders, so a confident prestige match doubles as a
    commander identification.
    """
    if not _normalize_text(text):
        return None
    best = None  # (commander, index, title, score)
    for commander, titles in prestige_names.items():
        for idx, title in titles.items():
            score = _prestige_text_score(title, text)
            if best is None or score > best[3]:
                best = (commander, idx, title, score)
    # Require a fairly strong match: a wrong commander is worse than none.
    if best and best[3] >= 0.75:
        return {
            'commander': best[0],
            'prestige': {'index': best[1], 'title': best[2], 'score': best[3]},
        }
    return None


def _ocr_prestige(image, commander: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], str]:
    """Read a prestige title in block mode, then retry as a single line."""
    matcher = (
        (lambda text: _match_prestige(commander, text))
        if commander
        else _commander_from_prestige
    )

    raw = _ocr_image_to_text(image, psm=6)
    match = matcher(raw)
    if match:
        return match, raw

    retry_raw = _ocr_image_to_text(image, psm=7)
    match = matcher(retry_raw)
    combined = '\n'.join(part for part in (raw, retry_raw) if part)
    return match, combined


def _match_difficulty(text: str) -> Optional[str]:
    # Check the raw text for a Brutal+ marker first - normalization strips '+'.
    raw = (text or '').lower()
    if 'brutal' in raw or 'b+' in raw.replace(' ', ''):
        return 'Brutal'
    # The difficulty crop also includes the bonus line. On Brutal, that line is
    # consistently easier for Tesseract to read than the selected button.
    if re.search(r'\bbonus\s*xp\W*100\s*%?', raw):
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


def _ocr_difficulty(image) -> Tuple[Optional[str], str]:
    """Read the two-line difficulty block, then retry only its top line."""
    raw = _ocr_image_to_text(image, psm=6)
    difficulty = _match_difficulty(raw)
    if difficulty:
        return difficulty, raw

    width, height = image.size
    focused = image.crop((0, 0, width, max(1, int(height * 0.62))))
    focused_raw = _ocr_image_to_text(focused, psm=7)
    combined = '\n'.join(part for part in (raw, focused_raw) if part)
    return _match_difficulty(combined), combined


def _capture_region_images(monitor: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Capture the three region crops.

    Prefers grabbing only the small region bboxes relative to the SC2 client
    rect (cheap, windowed-mode/multi-monitor safe). Falls back to capturing
    the configured monitor and cropping by fractions.
    """
    regions = _regions()

    rect = sc2_foreground_client_rect()
    if rect:
        left0, top0, win_w, win_h = rect
        bboxes = {}
        for name, (left, top, right, bottom) in regions.items():
            bboxes[name] = (
                left0 + int(left * win_w),
                top0 + int(top * win_h),
                max(1, int((right - left) * win_w)),
                max(1, int((bottom - top) * win_h)),
            )
        images = grab_screen_regions(bboxes)
        if images:
            return {'images': images, 'capture': f'SC2 window {win_w}x{win_h}'}

    image = grab_screen_region(monitor)
    if image is None:
        return None
    width, height = image.size
    images = {}
    for name, (left, top, right, bottom) in regions.items():
        images[name] = image.crop((int(left * width), int(top * height), int(right * width), int(bottom * height)))
    return {'images': images, 'capture': f'monitor {width}x{height}'}


def detect_selection(monitor: Optional[int] = None, log_regions: bool = False) -> Optional[Dict[str, Any]]:
    """Capture and OCR the selection-screen regions.

    Returns ``{'commander', 'prestige', 'difficulty', 'score'}`` or ``None``
    when neither the commander region nor the prestige region reads anything
    recognisable (which also means we're probably not on the lobby screen).

    OCR is short-circuited: the commander region is read first, the prestige
    region only when needed, and the difficulty region only once a commander
    was identified - clicking around regular menus costs one Tesseract call,
    not three.

    When ``log_regions`` is True the raw OCR text of each region is logged -
    use this to calibrate the region coordinates.
    """
    captured = _capture_region_images(monitor)
    if captured is None:
        if log_regions:
            logger.info('Selection OCR: screen capture returned nothing (check the "monitor" setting)')
        return None

    images = captured['images']
    raw_texts: Dict[str, str] = {}

    def log_raw():
        if log_regions:
            parts = ' '.join(f'{name}={text.strip()!r}' for name, text in raw_texts.items())
            logger.info(f"Selection OCR regions ({captured['capture']}): {parts}")

    commander_raw = _ocr_image_to_text(images['commander'])
    raw_texts['commander'] = commander_raw
    commander_match = _match_in_text(commander_raw, _canonical_commanders())

    if commander_match:
        commander, score = commander_match
        prestige, prestige_raw = _ocr_prestige(images['prestige'], commander)
        raw_texts['prestige'] = prestige_raw
    else:
        # Commander-name region failed to read. Fall back to inferring the
        # commander from the prestige title, which is unique per commander.
        fallback, prestige_raw = _ocr_prestige(images['prestige'])
        raw_texts['prestige'] = prestige_raw
        if not fallback:
            log_raw()
            return None
        commander = fallback['commander']
        prestige = fallback['prestige']
        score = prestige['score']
        if log_regions:
            logger.info(
                f"Selection OCR: commander region unreadable; inferred "
                f"{commander_display_name(commander)} from prestige '{prestige['title']}'"
            )

    difficulty, difficulty_raw = _ocr_difficulty(images['difficulty'])
    raw_texts['difficulty'] = difficulty_raw
    log_raw()

    return {
        'commander': commander,
        'prestige': prestige,
        'difficulty': difficulty,
        'score': score,
    }


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

    def clear_if_unchanged(self, observed: Optional[Dict[str, Any]]) -> bool:
        """Clear only when no newer OCR result replaced the observed value."""
        observed_time = observed.get('time') if observed else None
        with self._lock:
            current_time = self._data.get('time') if self._data else None
            if current_time != observed_time:
                return False
            self._data = None
            return True


SELECTION = _SelectionState()

# --- watcher ---------------------------------------------------------------
_timer: Optional[threading.Timer] = None
_timer_lock = threading.Lock()
_in_game = False
_hooked = False
_hook_handle = None
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
    global _timer
    with _timer_lock:
        _timer = None
    try:
        foreground = sc2_is_foreground()
        if _in_game or not foreground:
            logger.debug(f'Selection OCR skipped (in_game={_in_game}, sc2_foreground={foreground})')
            return
        result = detect_selection(log_regions=_ocr_debug_enabled())
        if not result:
            logger.debug('Selection OCR: nothing recognised (not the lobby screen, or calibration is off)')
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
            global _last_skip_log
            now = time.time()
            if now - _last_skip_log >= _SKIP_LOG_INTERVAL:
                _last_skip_log = now
                logger.debug(
                    'Selection watcher: click ignored '
                    f'(in_game={_in_game}, sc2_foreground={foreground})'
                )
            return
        global _timer
        with _timer_lock:
            # Trailing-edge debounce: each click cancels any pending detection
            # and re-arms the timer, so the capture always happens
            # DEBOUNCE_SECONDS after the *last* click and reads the final
            # selection (never a mid-burst or mid-animation frame).
            if _timer is not None:
                _timer.cancel()
            _timer = threading.Timer(DEBOUNCE_SECONDS, _run_detection)
            _timer.daemon = True
            _timer.start()
        logger.debug(f'Selection watcher: click -> detection in {DEBOUNCE_SECONDS:g}s')
    except Exception:
        logger.error(f'Selection watcher click handler failed:\n{traceback.format_exc()}')


def start_watcher() -> None:
    """Register the global left-click hook (idempotent)."""
    global _hooked, _hook_handle
    if _hooked:
        return
    try:
        import mouse
    except ImportError:
        logger.error('mouse package not installed; click-triggered OCR disabled')
        return
    try:
        # on_click returns the internal handler; keep it for a targeted unhook.
        _hook_handle = mouse.on_click(_on_click)
        _hooked = True
        logger.info('Commander selection watcher started (click-triggered OCR)')
    except Exception:
        logger.error(f'Failed to start selection watcher:\n{traceback.format_exc()}')


def stop_watcher() -> None:
    global _hooked, _hook_handle, _timer
    with _timer_lock:
        if _timer is not None:
            _timer.cancel()
            _timer = None
    if not _hooked:
        return
    try:
        import mouse
        if _hook_handle is not None:
            mouse.unhook(_hook_handle)
        else:
            mouse.unhook_all()
    except Exception:
        pass
    _hook_handle = None
    _hooked = False
