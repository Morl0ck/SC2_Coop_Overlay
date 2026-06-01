"""Parse co-op mission difficulty from the live SC2 stream API or replay lobby data."""
from typing import Any, Dict, List, Optional

from SCOFunctions.SC2Dictionaries.MissionTimelines import DIFFICULTIES

# Co-op lobby difficulty ids (Amon AI slots) — same mapping as S2Parser.diff_dict.
_COOP_DIFF_BY_ID = {1: 'Casual', 2: 'Normal', 3: 'Hard', 4: 'Brutal'}
_AMON_SLOT_IDS = (3, 4)


def _normalize_difficulty(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, int):
        return _COOP_DIFF_BY_ID.get(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.upper().startswith('B+'):
            return 'Brutal'
        for name in DIFFICULTIES:
            if text.lower() == name.lower():
                return name
    return None


def _player_difficulty(player: Dict[str, Any]) -> Optional[str]:
    if player.get('type') not in ('computer', 'Computer'):
        return None
    return _normalize_difficulty(player.get('difficulty'))


def parse_coop_difficulty(
    players: List[Dict[str, Any]],
    game_resp: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Read mission difficulty from `:6119/game` player entries.

    Co-op stores difficulty on Amon AI slots (typically ids 3 and 4). Returns
    a canonical name (Casual/Normal/Hard/Brutal) or None if not found.
    """
    for slot_id in _AMON_SLOT_IDS:
        for player in players:
            if player.get('id') == slot_id:
                diff = _player_difficulty(player)
                if diff:
                    return diff

    for player in players:
        diff = _player_difficulty(player)
        if diff:
            return diff

    if game_resp:
        for key in ('difficulty', 'gameDifficulty', 'coopDifficulty'):
            diff = _normalize_difficulty(game_resp.get(key))
            if diff:
                return diff
        brutal_plus = game_resp.get('brutalPlus', game_resp.get('brutal_plus', 0))
        try:
            if int(brutal_plus) > 0:
                return 'Brutal'
        except (TypeError, ValueError):
            pass

    return None


def resolve_mission_difficulty(
    players: List[Dict[str, Any]],
    game_resp: Optional[Dict[str, Any]] = None,
    override: Optional[str] = 'auto',
    fallback: str = 'Brutal',
) -> str:
    """Difficulty for mission timeline lookup.

    When ``override`` is a concrete difficulty name, that value wins. ``auto``
    tries the live API first, then falls back to ``fallback`` (usually Brutal).
    """
    if override and override != 'auto':
        normalized = _normalize_difficulty(override)
        if normalized in DIFFICULTIES:
            return normalized

    parsed = parse_coop_difficulty(players, game_resp)
    if parsed in DIFFICULTIES:
        return parsed
    return fallback if fallback in DIFFICULTIES else 'Brutal'
