"""
Pure-logic module for the live mission "what's next" overlay.

`MissionTracker` owns no thread. It is fed each `:6119/game` response by the
shared game-state poller in `MainFunctions.py` and emits at most three kinds of
overlay events:

    missionStartEvent - once per game, when the map is identified
    missionTimeEvent  - clock sync (only on change, or every SYNC_INTERVAL)
    missionEndEvent   - once, when the game ends / SC2 disconnects

The tracker never sends per-second updates; the overlay JS runs the countdown
locally between syncs. Mission tracking is independent of replay parsing.
"""
import time
import traceback
from typing import Any, Callable, Dict, List

from SCOFunctions.IdentifyMap import identify_map
from SCOFunctions.MLogging import Logger
from SCOFunctions.MissionTimelineStore import MTS
from SCOFunctions.SC2Dictionaries import MISSION_TIMELINE_VERSION

logger = Logger('MTRK', Logger.levels.INFO)


class MissionTracker:
    # Wall-clock seconds between forced clock re-syncs (drift correction).
    SYNC_INTERVAL = 10
    # Number of consecutive polls with an unchanging clock that mark the game as
    # over (score screen). The poller runs roughly every 5s in-game, so ~3 polls
    # of a frozen clock (~15s) reliably means the match has ended.
    STALL_LIMIT = 3

    def __init__(self, send_event: Callable[[Dict[str, Any]], None]):
        self._send_event = send_event
        # Survives reset(): prevents re-starting the same game while we sit on
        # the frozen score screen (which keeps reporting a valid in-game state).
        self._suppress_restart = False
        self._suppressed_display_time = None
        self.reset()

    def reset(self) -> None:
        self.in_game = False
        self.idle = True
        self.current_map = None
        self.last_display_time = None
        self.last_sent_display_time = None
        self.last_sync_wallclock = 0.0
        self.stall_count = 0

    # --- helpers -----------------------------------------------------------
    @staticmethod
    def _all_users(players: List[Dict[str, Any]]) -> bool:
        for player in players:
            if player.get('type') != 'user':
                return False
        return True

    @staticmethod
    def _is_ingame(players: List[Dict[str, Any]], is_replay: bool, display_time: float) -> bool:
        """ A live co-op game: not a replay, >2 players, not all-human (versus), clock running. """
        if is_replay:
            return False
        if len(players) <= 2:
            return False
        if MissionTracker._all_users(players):
            return False
        return display_time and display_time > 0

    # --- lifecycle ---------------------------------------------------------
    def on_disconnect(self) -> None:
        """ SC2 connection lost (game closed). End any tracked mission. """
        if self.in_game:
            logger.info('SC2 disconnected -> mission end')
            self._end()
        self.idle = True
        # A disconnect means we're no longer on the score screen.
        self._suppress_restart = False
        self._suppressed_display_time = None

    def _end(self, score_screen: bool = False) -> None:
        self._send_event({'missionEndEvent': True})
        ended_display_time = self.last_display_time
        self.reset()
        # The score screen keeps reporting a valid in-game state with a frozen
        # clock; remember it so we don't immediately re-start the same game.
        if score_screen:
            self._suppress_restart = True
            self._suppressed_display_time = ended_display_time

    def _start(self, players: List[Dict[str, Any]], display_time: float) -> None:
        try:
            map_found = identify_map(players)
        except Exception:
            logger.error(traceback.format_exc())
            map_found = None

        if not map_found:
            # Custom/unknown map - keep the panel hidden and keep checking.
            logger.debug('Mission tracker: map not identified, panel stays hidden')
            return

        timeline = MTS.get_events(map_found, 'Brutal')
        if not timeline or not timeline.get('events'):
            logger.info(f'Mission tracker: no timeline data for "{map_found}"')
            return

        self.in_game = True
        self.idle = False
        self.current_map = map_found
        self.last_display_time = display_time
        self.last_sent_display_time = display_time
        self.last_sync_wallclock = time.time()
        self.stall_count = 0

        logger.info(f'Mission started: {map_found} (displayTime={display_time})')
        self._send_event({
            'missionStartEvent': True,
            'map_name': map_found,
            'events': timeline['events'],
            'displayTime': display_time,
            'version': MISSION_TIMELINE_VERSION,
        })

    # --- main entry --------------------------------------------------------
    def update(self, resp: Dict[str, Any]) -> None:
        """ Called once per poll with the `:6119/game` response. """
        players = resp.get('players', list())
        is_replay = resp.get('isReplay', True)
        display_time = resp.get('displayTime', 0)

        if not self.in_game:
            self.idle = True
            if self._is_ingame(players, is_replay, display_time):
                # Don't restart on the frozen score screen we just ended on.
                if self._suppress_restart and display_time == self._suppressed_display_time:
                    return
                self._suppress_restart = False
                self._suppressed_display_time = None
                self._start(players, display_time)
            else:
                # Back in menus / replay / versus -> clear the score-screen guard.
                self._suppress_restart = False
                self._suppressed_display_time = None
            return

        self.idle = False

        # Hard game-end signals (returned to menus / replay / versus state).
        if is_replay or len(players) <= 2 or self._all_users(players):
            self._end()
            return

        # Score screen: `/game` keeps returning the final non-zero displayTime,
        # so detect end via the clock no longer advancing across several polls.
        if display_time == self.last_display_time:
            self.stall_count += 1
            if self.stall_count >= self.STALL_LIMIT:
                logger.info('Game clock stalled (score screen) -> mission end')
                self._end(score_screen=True)
                return
        else:
            self.stall_count = 0
            self.last_display_time = display_time

        # Clock sync: only when the value changed, or as periodic drift correction.
        now = time.time()
        if display_time != self.last_sent_display_time or (now - self.last_sync_wallclock) >= self.SYNC_INTERVAL:
            self._send_event({'missionTimeEvent': True, 'displayTime': display_time})
            self.last_sent_display_time = display_time
            self.last_sync_wallclock = now
