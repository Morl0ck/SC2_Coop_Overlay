"""
Shared OCR primitives for reading the co-op lobby selection screen.

Provides thread-safe screen capture (mss), Tesseract via pytesseract with
image preprocessing tuned for SC2's light-text-on-dark UI, and fuzzy matching
of commander names against bundled prestige_names keys.

The actual selection-screen detection lives in `CommanderSelection`.
"""
from __future__ import annotations

import difflib
import os
import re
import shutil
import traceback
from typing import Dict, List, Optional, Sequence, Tuple

from SCOFunctions.MLogging import Logger
from SCOFunctions.SC2Dictionaries import prestige_names
from SCOFunctions.Settings import Setting_manager as SM

logger = Logger('OCR', Logger.levels.INFO)

# Minimum difflib ratio to accept a fuzzy commander match.
CONFIDENCE_THRESHOLD = 0.85

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

# Tri-state: None = not checked yet, True/False = cached result. A negative
# result is cached too, so a missing Tesseract install doesn't re-run path
# discovery and re-log an error on every OCR call.
_tesseract_available: Optional[bool] = None

# Cap the longest preprocessed edge so upscaling small crops can't blow up
# into huge images on high-resolution monitors.
_MAX_OCR_EDGE = 4000


def commander_display_name(commander: str) -> str:
    return DISPLAY_NAMES.get(commander, commander)


def _canonical_commanders() -> List[str]:
    return sorted(prestige_names.keys())


def _alias_targets() -> Dict[str, str]:
    out = {name.lower(): name for name in _canonical_commanders()}
    out.update(COMMANDER_ALIASES)
    return out


def _configure_tesseract() -> bool:
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available

    try:
        import pytesseract
    except ImportError:
        logger.error('pytesseract is not installed; OCR disabled')
        _tesseract_available = False
        return False

    if shutil.which('tesseract'):
        _tesseract_available = True
        return True

    for candidate in (
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ):
        if os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            _tesseract_available = True
            return True

    logger.error('Tesseract executable not found in PATH or default install locations; OCR disabled')
    _tesseract_available = False
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


def grab_screen_regions(bboxes: Dict[str, Tuple[int, int, int, int]]) -> Optional[Dict[str, 'Image.Image']]:
    """Capture several small screen regions in one mss session.

    ``bboxes`` maps a name to ``(left, top, width, height)`` in absolute screen
    pixels. Much cheaper than grabbing a full monitor and cropping when only a
    few small regions are needed.
    """
    try:
        import mss
    except ImportError:
        logger.error('mss/Pillow not installed for screen capture')
        return None

    try:
        with mss.mss() as sct:
            out = {}
            for name, (left, top, width, height) in bboxes.items():
                shot = sct.grab({'left': left, 'top': top, 'width': width, 'height': height})
                out[name] = _screenshot_to_image(shot)
            return out
    except Exception:
        logger.error(f'Screen capture failed:\n{traceback.format_exc()}')
        return None


def _preprocess_for_ocr(image):
    """Prepare a UI crop for Tesseract.

    SC2 renders light text on a dark, textured background - Tesseract's worst
    case. Upscale (small UI text), grayscale, and invert to dark-on-light so
    Tesseract's internal binarization gets a clean input.
    """
    from PIL import Image, ImageOps, ImageStat

    gray = ImageOps.grayscale(image)
    width, height = gray.size
    if not width or not height:
        return gray

    longest = max(width, height)
    scale = 3 if longest * 3 <= _MAX_OCR_EDGE else max(1, _MAX_OCR_EDGE // longest)
    if scale > 1:
        resample = getattr(Image, 'Resampling', Image).LANCZOS
        gray = gray.resize((width * scale, height * scale), resample)

    if ImageStat.Stat(gray).mean[0] < 128:
        gray = ImageOps.invert(gray)

    return ImageOps.autocontrast(gray)


def _ocr_image_to_text(image, psm: int = 7) -> str:
    """OCR a region crop. ``psm`` defaults to 7 (single text line)."""
    if not _configure_tesseract():
        return ''
    try:
        import pytesseract
        return pytesseract.image_to_string(_preprocess_for_ocr(image), config=f'--psm {psm}')
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

    # Word-bounded exact alias hit ('nova' must not match inside another word).
    for alias, canonical in aliases.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', normalized):
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
