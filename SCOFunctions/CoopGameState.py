"""
Shared helpers for live co-op game-state detection from `:6119/game` responses.

Used by both `MissionTracker` and `BuildOrderTracker` so the definition of
"a live co-op game" and the frozen-clock score-screen detection can't drift
between the two features.
"""
from typing import Any, Dict, List


def all_users(players: List[Dict[str, Any]]) -> bool:
    """ True when every player is a human user (a versus game, not co-op). """
    for player in players:
        if player.get('type') != 'user':
            return False
    return True


def is_ingame(players: List[Dict[str, Any]], is_replay: bool, display_time: float) -> bool:
    """ A live co-op game: not a replay, >2 players, not all-human (versus), clock running. """
    if is_replay:
        return False
    if len(players) <= 2:
        return False
    if all_users(players):
        return False
    return bool(display_time and display_time > 0)


class StallDetector:
    """ Detects the score screen via the game clock no longer advancing.

    The `/game` API keeps returning the final non-zero displayTime after a match
    ends, so several consecutive polls with an unchanging clock reliably mean
    the game is over.
    """

    def __init__(self, limit: int = 3):
        self.limit = limit
        self.last_display_time = None
        self.count = 0

    def reset(self, display_time: float = None) -> None:
        self.last_display_time = display_time
        self.count = 0

    def update(self, display_time: float) -> bool:
        """ Feed one poll's displayTime; returns True once the clock has been
        frozen for `limit` consecutive polls. """
        if display_time == self.last_display_time:
            self.count += 1
            return self.count >= self.limit
        self.count = 0
        self.last_display_time = display_time
        return False
