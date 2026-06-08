"""
Screen OCR to detect the local player's commander at co-op game start.

Uses a thread-safe screen capture (mss) and Tesseract via pytesseract.
Commander names are fuzzy-matched against bundled prestige_names keys.
"""
from __future__ import annotations

import difflib
import os
import re
import shutil
import time
import traceback
from typing import Dict, List, Optional, Sequence, Tuple

from SCOFunctions.MLogging import Logger
from SCOFunctions.SC2Dictionaries import prestige_names
from SCOFunctions.Settings import Setting_manager as SM

logger = Logger('OCR', Logger.levels.INFO)

# Minimum difflib ratio to accept a fuzzy commander match.
CONFIDENCE_THRESHOLD = 0.85
# Lock immediately when we see a near-exact match.
HIGH_CONFIDENCE = 0.95

# OCR aliases -> canonical prestige_names key.
COMMANDER_ALIASES: Dict[str, str] = {
    'han & horner': 'Horner',
    'han and horner': 'Horner',
    'han horner': 'Horner',
    'hanhorner': 'Horner',
    'mira han': 'Horner',
    'matt horner': 'Horner',
    'mira han & matt horner': 'Horner',
    'mira han and matt horner': 'Horner',
}

DISPLAY_NAMES: Dict[str, str] = {
    'Horner': 'Han & Horner',
}

_tesseract_configured = False


def commander_display_name(commander: str) -> str:
    return DISPLAY_NAMES.get(commander, commander)


def _canonical_commanders() -> List[str]:
    return sorted(prestige_names.keys())


def _alias_targets() -> Dict[str, str]:
    out = {name.lower(): name for name in _canonical_commanders()}
    out.update(COMMANDER_ALIASES)
    return out


def _configure_tesseract() -> bool:
    global _tesseract_configured
    if _tesseract_configured:
        return True
    try:
        import pytesseract
    except ImportError:
        logger.error('pytesseract is not installed')
        return False

    if shutil.which('tesseract'):
        _tesseract_configured = True
        return True

    for candidate in (
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ):
        if os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            _tesseract_configured = True
            return True

    logger.error('Tesseract executable not found in PATH or default install locations')
    return False


def _screenshot_to_image(shot):
    from PIL import Image

    if hasattr(shot, 'rgb'):
        return Image.frombytes('RGB', shot.size, shot.rgb)
    if hasattr(shot, 'bgra'):
        return Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')
    if hasattr(shot, 'bgr'):
        return Image.frombytes('RGB', shot.size, shot.bgr, 'raw', 'BGRX')
    return Image.frombytes('RGB', shot.size, shot.raw, 'raw', 'BGRX')


def grab_screen_region(monitor_index: Optional[int] = None) -> Optional['Image.Image']:
    """Capture the configured monitor (or full virtual screen). Thread-safe via mss."""
    try:
        import mss
    except ImportError:
        logger.error('mss/Pillow not installed for screen capture')
        return None

    idx = monitor_index if monitor_index is not None else int(SM.settings.get('monitor', 1))
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if idx < 1 or idx >= len(monitors):
                idx = 1
            shot = sct.grab(monitors[idx])
            return _screenshot_to_image(shot)
    except Exception:
        logger.error(f'Screen capture failed:\n{traceback.format_exc()}')
        return None


def _ocr_image_to_text(image) -> str:
    if not _configure_tesseract():
        return ''
    try:
        import pytesseract
        return pytesseract.image_to_string(image, config='--psm 6')
    except Exception:
        logger.error(f'OCR failed:\n{traceback.format_exc()}')
        return ''


def _normalize_text(text: str) -> str:
    text = text.replace('\n', ' ')
    text = re.sub(r'[^\w\s&]', ' ', text, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', text).strip().lower()


def _match_in_text(text: str, candidates: Sequence[str]) -> Optional[Tuple[str, float]]:
    if not text:
        return None

    aliases = _alias_targets()
    best_name = None
    best_score = 0.0
    normalized = _normalize_text(text)

    for alias, canonical in aliases.items():
        if alias in normalized:
            return canonical, 1.0

    tokens = normalized.split()
    for canonical in candidates:
        for alias, mapped in aliases.items():
            if mapped != canonical:
                continue
            score = difflib.SequenceMatcher(None, alias, normalized).ratio()
            if score > best_score:
                best_score = score
                best_name = canonical

        display = commander_display_name(canonical).lower()
        for probe in (canonical.lower(), display):
            score = difflib.SequenceMatcher(None, probe, normalized).ratio()
            if score > best_score:
                best_score = score
                best_name = canonical
            for window in (' '.join(tokens[i:i + len(probe.split())]) for i in range(max(1, len(tokens)))):
                score = difflib.SequenceMatcher(None, probe, window).ratio()
                if score > best_score:
                    best_score = score
                    best_name = canonical

    if best_name and best_score >= CONFIDENCE_THRESHOLD:
        return best_name, best_score
    return None


def _region_for_player(image, player_position: int):
    """Crop to left or right half to disambiguate ally vs local commander text."""
    width, height = image.size
    if player_position == 2:
        return image.crop((width // 2, 0, width, height))
    return image.crop((0, 0, width // 2, height))


def detect_commander_once(player_position: int = 1) -> Optional[Tuple[str, float]]:
    """Single capture + OCR attempt. Returns (commander, score) or None."""
    image = grab_screen_region()
    if image is None:
        return None

    candidates = _canonical_commanders()

    # Prefer the local player's screen half — full-screen OCR often picks the ally.
    player_text = _ocr_image_to_text(_region_for_player(image, player_position))
    player_match = _match_in_text(player_text, candidates)
    if player_match:
        logger.info(f'OCR detected commander: {player_match[0]} (score={player_match[1]:.2f}, player side)')
        return player_match

    full_text = _ocr_image_to_text(image)
    full_match = _match_in_text(full_text, candidates)
    if full_match:
        logger.info(f'OCR detected commander: {full_match[0]} (score={full_match[1]:.2f}, full screen fallback)')
        return full_match
    return None


def detect_commander_name(player_position: int = 1) -> Optional[str]:
    """Convenience wrapper returning only the commander name."""
    match = detect_commander_once(player_position)
    return match[0] if match else None


def detect_commander(
    player_position: int = 1,
    *,
    retries: int = 5,
    retry_delay: float = 3.0,
) -> Optional[str]:
    """Retry OCR over several seconds to catch the loading screen."""
    for attempt in range(max(1, retries)):
        match = detect_commander_once(player_position)
        if match:
            return match[0]
        if attempt < retries - 1:
            time.sleep(retry_delay)
    logger.info('OCR could not detect commander confidently')
    return None
