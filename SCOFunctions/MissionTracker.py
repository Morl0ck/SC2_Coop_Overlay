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
from typing import Any, Callable, Dict, List, Optional

from SCOFunctions.CommanderSelection import SELECTION
from SCOFunctions.CoopDifficulty import resolve_mission_difficulty
from SCOFunctions.CoopGameState import StallDetector, all_users, is_ingame
from SCOFunctions.IdentifyMap import identify_map
from SCOFunctions.MLogging import Logger
from SCOFunctions.MissionTimelineStore import MTS
from SCOFunctions.Settings import Setting_manager as SM

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
        # One-shot startup baseline (see update()): only set once, never in reset().
        self._startup_seen = False
        self.stall = StallDetector(self.STALL_LIMIT)
        self.reset()

    def reset(self) -> None:
        self.in_game = False
        self.idle = True
        self.current_map = None
        self.current_requested_difficulty = None
        self.current_timing_difficulty = None
        self.selection_difficulty = None
        self.pending_game = False
        self.last_sent_display_time = None
        self.last_sync_wallclock = 0.0
        self.stall.reset()

    # --- helpers -----------------------------------------------------------
    def _settings_requested_difficulty(
        self,
        players: List[Dict[str, Any]],
        game_resp: Optional[Dict[str, Any]] = None,
    ) -> str:
        override = SM.settings.get('mission_overlay', {}).get('difficulty', 'auto')
        # When on 'auto', use the difficulty read from the lobby selection screen
        # as a fallback if the live API doesn't expose it.
        fallback = self.selection_difficulty or 'Brutal'
        if override == 'auto' and self.selection_difficulty is None:
            selection = SELECTION.get()
            if selection and selection.get('difficulty'):
                self.selection_difficulty = selection['difficulty']
                fallback = self.selection_difficulty
        return resolve_mission_difficulty(players, game_resp, override=override, fallback=fallback)

    def _emit_timeline_start(self, map_name: str, requested: str, timeline: Dict[str, Any], display_time: float) -> None:
        timing = timeline.get('timing_difficulty', requested)
        self.current_map = map_name
        self.current_requested_difficulty = requested
        self.current_timing_difficulty = timing
        self.last_sent_display_time = display_time
        self.last_sync_wallclock = time.time()

        if timing != requested:
            logger.info(f'Mission timeline: {map_name} requested {requested}, using {timing} timings')
        else:
            logger.info(f'Mission started: {map_name} ({requested}, displayTime={display_time})')

        self._send_event({
            'missionStartEvent': True,
            'map_name': map_name,
            'difficulty': requested,
            'timing_difficulty': timing,
            'events': timeline['events'],
            'displayTime': display_time,
            # Layout settings ride along so secondary overlays (OBS browser
            # sources) connecting mid-game don't depend on a prior init message.
            'mission_overlay': dict(SM.settings.get('mission_overlay', {})),
        })

    def _reload_timeline(self, requested: str, display_time: float) -> bool:
        if not self.current_map:
            return False

        timeline = MTS.get_events(self.current_map, requested)
        if not timeline or not timeline.get('events'):
            logger.info(
                f'Mission tracker: no timeline data for "{self.current_map}" '
                f'(requested {requested})'
            )
            self._end()
            return False

        self._emit_timeline_start(self.current_map, requested, timeline, display_time)
        return True

    # --- lifecycle ---------------------------------------------------------
    def on_disconnect(self) -> None:
        """ SC2 connection lost (game closed). End any tracked mission. """
        had_game = self.in_game or self.pending_game
        if self.in_game:
            logger.info('SC2 disconnected -> mission end')
            self._end()
        else:
            self.reset()
            if had_game:
                SELECTION.clear()
        self.idle = True
        # A disconnect means we're no longer on the score screen.
        self._suppress_restart = False
        self._suppressed_display_time = None

    def _end(self, score_screen: bool = False) -> None:
        self._send_event({'missionEndEvent': True})
        ended_display_time = self.stall.last_display_time
        self.reset()
        SELECTION.clear()
        # The score screen keeps reporting a valid in-game state with a frozen
        # clock; remember it so we don't immediately re-start the same game.
        if score_screen:
            self._suppress_restart = True
            self._suppressed_display_time = ended_display_time

    def _start(self, players: List[Dict[str, Any]], display_time: float, game_resp: Optional[Dict[str, Any]] = None) -> None:
        # Snapshot the lobby fallback before another tracker clears the shared
        # selection cache. Map identification can require more than one poll.
        if self.selection_difficulty is None:
            selection = SELECTION.get()
            if selection and selection.get('difficulty'):
                self.selection_difficulty = selection['difficulty']

        try:
            map_found = identify_map(players)
        except Exception:
            logger.error(traceback.format_exc())
            map_found = None

        if not map_found:
            # Custom/unknown map - keep the panel hidden and keep checking.
            logger.debug('Mission tracker: map not identified, panel stays hidden')
            return

        requested = self._settings_requested_difficulty(players, game_resp)
        timeline = MTS.get_events(map_found, requested)
        if not timeline or not timeline.get('events'):
            logger.info(f'Mission tracker: no timeline data for "{map_found}" (requested {requested})')
            return

        self.in_game = True
        self.idle = False
        self.stall.reset(display_time)
        self._emit_timeline_start(map_found, requested, timeline, display_time)

    # --- main entry --------------------------------------------------------
    def update(self, resp: Dict[str, Any]) -> None:
        """ Called once per poll with the `:6119/game` response. """
        players = resp.get('players', list())
        is_replay = resp.get('isReplay', True)
        display_time = resp.get('displayTime', 0)

        # On the first poll after the app starts, snapshot any already-running
        # game as a baseline to ignore - the same way new-replay detection seeds
        # ReplayPosition with the existing replays. SC2 keeps reporting a finished
        # game's frozen score-screen state, so without this the overlay flashes
        # for a game that was already over when the app restarted. A genuinely new
        # game has a different displayTime and starts normally.
        if not self._startup_seen:
            self._startup_seen = True
            if not self.in_game and is_ingame(players, is_replay, display_time):
                self._suppress_restart = True
                self._suppressed_display_time = display_time
                self.idle = True
                return

        if not self.in_game:
            self.idle = True
            if is_ingame(players, is_replay, display_time):
                self.pending_game = True
                # Don't restart on the frozen score screen we just ended on
                # (or the one in progress when the app started).
                if self._suppress_restart and display_time == self._suppressed_display_time:
                    return
                self._suppress_restart = False
                self._suppressed_display_time = None
                self._start(players, display_time, resp)
            else:
                if self.pending_game:
                    SELECTION.clear()
                    self.pending_game = False
                # Back in menus / replay / versus -> clear the score-screen guard.
                self._suppress_restart = False
                self._suppressed_display_time = None
            return

        self.idle = False

        requested = self._settings_requested_difficulty(players, resp)
        if requested != self.current_requested_difficulty:
            logger.info(f'Mission tracker: difficulty changed to {requested}')
            self._reload_timeline(requested, display_time)

        # Hard game-end signals (returned to menus / replay / versus state).
        if is_replay or len(players) <= 2 or all_users(players):
            self._end()
            return

        # Score screen: `/game` keeps returning the final non-zero displayTime,
        # so detect end via the clock no longer advancing across several polls.
        if self.stall.update(display_time):
            logger.info('Game clock stalled (score screen) -> mission end')
            self._end(score_screen=True)
            return

        # Clock sync: only when the value changed, or as periodic drift correction.
        now = time.time()
        if display_time != self.last_sent_display_time or (now - self.last_sync_wallclock) >= self.SYNC_INTERVAL:
            self._send_event({'missionTimeEvent': True, 'displayTime': display_time})
            self.last_sent_display_time = display_time
            self.last_sync_wallclock = now

