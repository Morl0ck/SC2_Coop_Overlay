"""
Pure-logic module for the live build-order overlay.

`BuildOrderTracker` owns no thread. It is fed each `:6119/game` response by the
shared game-state poller and emits:

    buildOrderStartEvent - once per game, commander resolved
    buildOrderEndEvent   - when the display window expires or the game ends

The commander is no longer OCR-ed in-game. It is read from the co-op lobby
selection screen by `CommanderSelection` (click-triggered OCR) before the game
starts and cached in ``SELECTION``; we fall back to the configured default
commander when nothing was detected.
"""
from __future__ import annotations

from typing import Any, Callable, Dict

from SCOFunctions.BuildOrderStore import BOS
from SCOFunctions.CommanderSelection import SELECTION
from SCOFunctions.CoopGameState import StallDetector, is_ingame
from SCOFunctions.MLogging import Logger
from SCOFunctions.Settings import Setting_manager as SM

logger = Logger('BOTR', Logger.levels.INFO)


class BuildOrderTracker:
    # Consecutive polls with a frozen clock that mark the score screen.
    STALL_LIMIT = 3

    def __init__(self, send_event: Callable[[Dict[str, Any]], None]):
        self._send_event = send_event
        # One-shot startup baseline: only set once, never in reset().
        self._startup_seen = False
        self.stall = StallDetector(self.STALL_LIMIT)
        self.reset()

    def reset(self) -> None:
        self.in_game = False
        self.idle = True
        # True once the build order has been shown (and hidden) for the current
        # game; stays set until SC2 returns to menus so we don't re-trigger.
        self.done = False
        # True once the start event was actually sent for the current game.
        self.emitted = False
        self.current_commander = None
        self.commander_source = None
        self.display_cutoff = None
        self.last_seen_display_time = None
        self.stall.reset()

    def _build_order_settings(self) -> Dict[str, Any]:
        return SM.settings.get('build_orders', {})

    def _display_minutes(self) -> float:
        try:
            return float(self._build_order_settings().get('display_minutes', 5.0))
        except (TypeError, ValueError):
            return 5.0

    def _resolve_commander(self) -> tuple:
        """Pick the commander for this game: detected selection, else default."""
        cfg = self._build_order_settings()
        if cfg.get('ocr_enabled', True):
            selection = SELECTION.get()
            if selection and selection.get('commander'):
                return selection['commander'], 'selection OCR'
        default = cfg.get('default_commander', 'Raynor')
        if default:
            return default, 'default'
        return None, None

    def _emit_start(self, commander: str, display_time: float, source_label: str) -> bool:
        order = BOS.get(commander)
        if not order or not order.get('steps'):
            logger.debug(f'Build order tracker: no steps for "{commander}"')
            return False

        self.current_commander = commander
        self.display_cutoff = self._display_minutes() * 60.0

        overlay_cfg = dict(SM.settings.get('build_order_overlay', {}))
        logger.info(
            f'Build order overlay start: {order["display_name"]} '
            f'({len(order["steps"])} steps, via {source_label}, displayTime={display_time})'
        )
        self._send_event({
            'buildOrderStartEvent': True,
            'commander': commander,
            'display_name': order['display_name'],
            'steps': order['steps'],
            'build_order_overlay': overlay_cfg,
        })
        return True

    def _send_end(self) -> None:
        self._send_event({'buildOrderEndEvent': True})

    def on_disconnect(self) -> None:
        if self.in_game:
            logger.info('SC2 disconnected -> build order end')
            if self.emitted:
                self._send_end()
            SELECTION.clear()
        self.reset()

    def _start(self, display_time: float) -> None:
        self.in_game = True
        self.idle = False
        self.stall.reset(display_time)
        self.display_cutoff = self._display_minutes() * 60.0

        commander, source = self._resolve_commander()
        # MissionTracker runs first and snapshots the selected difficulty. Once
        # the commander is resolved, do not let this lobby reading leak forward
        # into the next game.
        SELECTION.clear()
        self.current_commander = commander
        self.commander_source = source
        self.emitted = bool(commander) and self._emit_start(commander, display_time, source)
        if not self.emitted:
            # Nothing to show yet (e.g. the commander has no steps). Keep the
            # game tracked and retry within the display window, so a custom
            # build order saved mid-game still shows up.
            logger.info(f'Build order tracker: nothing to show yet for "{commander}" (retrying within display window)')

    def update(self, resp: Dict[str, Any]) -> None:
        players = resp.get('players', list())
        is_replay = resp.get('isReplay', True)
        display_time = resp.get('displayTime', 0)
        ingame = is_ingame(players, is_replay, display_time)

        # First poll after app start: ignore any game already in progress (e.g. a
        # frozen score screen left over from before the restart) so the overlay
        # doesn't flash for a game we never tracked from the start.
        if not self._startup_seen:
            self._startup_seen = True
            if not self.in_game and ingame:
                self.done = True
                self.idle = True
                self.last_seen_display_time = display_time
                return

        # Back in menus / replay / versus -> reset, ready for the next game.
        if not ingame:
            if self.in_game and self.emitted:
                self._send_end()
            self.in_game = False
            self.done = False
            self.emitted = False
            self.idle = True
            self.last_seen_display_time = None
            return

        self.idle = False
        previous_display_time = self.last_seen_display_time
        self.last_seen_display_time = display_time

        # SC2 can transition directly from one game's stale score-screen state
        # to the next game without exposing a menu poll. The new game clock
        # resetting near zero is then the only lifecycle boundary we receive.
        if self.done:
            if previous_display_time is not None and display_time < previous_display_time:
                logger.info(
                    f'Game clock reset ({previous_display_time} -> {display_time}) '
                    '-> next game'
                )
                self.done = False
                self.emitted = False
                self.in_game = False
                self._start(display_time)
            return

        if not self.in_game:
            self._start(display_time)
            return

        # Currently tracking: detect the frozen score-screen clock...
        if self.stall.update(display_time):
            logger.info('Game clock stalled (score screen) -> build order end')
            if self.emitted:
                self._send_end()
            self.in_game = False
            self.done = True
            return

        # ...and the display window elapsing.
        if self.display_cutoff is not None and display_time >= self.display_cutoff:
            if self.emitted:
                logger.info('Build order display window elapsed -> build order end')
                self._send_end()
            self.in_game = False
            self.done = True
            return

        # Not shown yet: keep retrying within the display window (a custom
        # build order can be fixed/saved mid-game).
        if not self.emitted and self.current_commander:
            self.emitted = self._emit_start(self.current_commander, display_time, self.commander_source or 'retry')
