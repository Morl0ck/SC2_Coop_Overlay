"""
A bit messy module containing functionality responsible for 
sending info to the overlay with socket/JS. The oldest part of the app.

Checking for new replays and games. Uploading replays to AOM. And more.
"""
import asyncio
import json
import os
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests
import websockets
from PyQt5 import QtCore
from websockets.legacy.server import \
    serve as \
    websockets_serve  # This direct import is required for Pyinstaller and Nuitka to find it correctly

import SCOFunctions.HelperFunctions as HF
from SCOFunctions.HelperFunctions import get_hash
from SCOFunctions.IdentifyMap import identify_map
from SCOFunctions.MissionTracker import MissionTracker
from SCOFunctions.MLogging import Logger
from SCOFunctions.ReplayAnalysis import parse_and_analyse_replay
from SCOFunctions.Settings import Setting_manager as SM

OverlayMessages = []  # Storage for all messages
lock = threading.Lock()
logger = Logger('MAIN', Logger.levels.INFO)

initMessage = {'initEvent': True, 
               'colors': ['null', 'null', 'null', 'null'], 
               'duration': 60, 
               'charts': {
                    'army' : True,
                    'supply' : True,
                    'kills' : True,
                    'collection_rate' : True,
                    'minerals' : False,
                    'vespene' : False,
                    'resources' : False
                    },
               'mission_overlay': {}
                }

ReplayPosition = 0
AllReplays = dict()
player_winrate_data = dict()
PLAYER_HANDLES: Set[str] = set()  # Set of handles of the main player
PLAYER_NAMES: Set[str] = set()  # Set of names of the main player generated from handles and used in winrate notification
most_recent_playerdata = None
CAnalysis = None
APP_CLOSING = False
session_games = {'Victory': 0, 'Defeat': 0}
WEBPAGE = None
RNG_COMMANDER = dict()
session = requests.Session()


def stop_threads() -> None:
    """ Sets a variable that lets threads know they should finish early """
    global APP_CLOSING
    APP_CLOSING = True


def update_init_message() -> None:
    """ Through this function the main script passes all its settings here """
    initMessage['colors'] = [SM.settings['color_player1'], SM.settings['color_player2'], SM.settings['color_amon'], SM.settings['color_mastery']]
    initMessage['duration'] = SM.settings['duration']
    initMessage['charts'] = SM.settings['charts']
    initMessage['mission_overlay'] = SM.settings['mission_overlay']

def sendEvent(event: Dict[str, Any], raw: bool = False) -> None:
    """ Send message to the overlay """
    with lock:
        # Websocket connection for non-primary overlay
        OverlayMessages.append(event)

    # Send message directly thorugh javascript for the primary overlay.
    if WEBPAGE is None:
        return

    elif raw:
        WEBPAGE.runJavaScript(event)

    elif event.get('replaydata') is not None:
        data = json.dumps(event)
        WEBPAGE.runJavaScript(f"postGameStatsTimed({data});")

    elif event.get('hideEvent') is not None:
        WEBPAGE.runJavaScript("hidestats()")

    elif event.get('showEvent') is not None:
        WEBPAGE.runJavaScript("showstats()")

    elif event.get('showHideEvent') is not None:
        WEBPAGE.runJavaScript("showhide()")

    elif event.get('uploadEvent') is not None:
        data = json.dumps(event)
        WEBPAGE.runJavaScript(f"setTimeout(uploadStatus, 1500, '{event['response']}')")

    elif event.get('initEvent') is not None:
        data = json.dumps(event)
        WEBPAGE.runJavaScript(f"initColorsDuration({data})")

    elif event.get('playerEvent') is not None:
        data = json.dumps(event)
        logger.info(f'Sending player event with JS: {event}')
        WEBPAGE.runJavaScript(f"showHidePlayerWinrate({data})")

    elif event.get('missionStartEvent') is not None:
        data = json.dumps(event)
        logger.info(f"Sending mission start event: {event.get('map_name')}")
        WEBPAGE.runJavaScript(f"missionStart({data});")

    elif event.get('missionTimeEvent') is not None:
        data = json.dumps(event)
        WEBPAGE.runJavaScript(f"missionSyncTime({data});")

    elif event.get('missionEndEvent') is not None:
        WEBPAGE.runJavaScript("missionEnd();")


def resend_init_message() -> None:
    """ Resends init message. In case duration of colors have changed. """
    sendEvent(initMessage)


def find_names_and_handles(ACCOUNTDIR: str, replays: Any = None) -> Tuple[Set[str], Set[str]]:
    """ Finds player handles and names from the account directory (or its subfolder) """
    # First walk up as far as possible in-case the user has selected one the of subfolders.
    folder = ACCOUNTDIR
    while True:
        parent = os.path.dirname(folder)
        if 'StarCraft' in parent:
            folder = parent
        else:
            break

    # Find handles & names
    handles = set()
    names = set()

    for root, directories, files in os.walk(folder):
        for directory in directories:
            if directory.count(
                    '-') >= 3 and not r'\Banks' in root and not 'Crash' in directory and not 'Desync' in directory and not 'Error' in directory:
                handles.add(directory)

        for file in files:
            if file.endswith('.lnk') and '_' in file and '@' in file:
                names.add(file.split('_')[0])

    # Fallbacks for finding player names: settings, replays, winrates
    if len(names) == 0 and len(SM.settings['main_names']) > 0:
        names = set(SM.settings['main_names'])
        logger.info(f'No player names found, falling back to settings: {names}')

    if len(names) == 0 and len(handles) > 0 and replays is not None:
        replays = [v.get('replay_dict', {'parser': None}).get('parser', None) for k, v in replays.items() if v is not None]
        replays = [r for r in replays if r is not None]
        names = names_fallback(handles, replays)
        logger.info(f'No player names found, falling back to replays: {names}')

    if len(names) == 0 and len(player_winrate_data) > 0:
        names = {list(player_winrate_data.keys())[0]}
        logger.info(f'No player names found, falling back to winrate: {names}')

    return names, handles


def names_fallback(handles: Set[str], replays: List[Any]) -> Set[str]:
    """ Finds new main player names from handles and replays.Assumes S2Parser format of replays. """
    shandles = set(handles)
    snames = set()

    for r in replays:
        if len(shandles) == 0:
            break
        for p in {1, 2}:
            if r.players[p]['handle'] in shandles:
                snames.add(r.players[p]['name'])
                shandles.remove(r.players[p]['handle'])
    return snames


def get_player_data(player_names: List[str]) -> Dict[str, List[Any]]:
    """ Takes the first player, gets its data from player_winrate_data.
    Appends player notes if there are any. Calculates the time difference from the last time played."""

    # No players
    if not player_names:
        return {}

    player = player_names[0]

    if player not in player_winrate_data:
        return {player: [None]}

    data = {player: player_winrate_data[player]['total'].copy()}

    # Get player notes
    if player in SM.settings['player_notes']:
        data[player].append(SM.settings['player_notes'][player])

    # Get time difference
    s = HF.get_time_difference(data[player][6])

    if s:
        data[player][6] = s
    return data


def update_names_and_handles(ACCOUNTDIR: str, AllReplays: Any) -> None:
    """ Takes player names and handles, and updates global variables with them"""
    global PLAYER_HANDLES
    global PLAYER_NAMES
    names, handles = find_names_and_handles(ACCOUNTDIR, replays=AllReplays)
    if len(handles) > 0:
        logger.info(f'Found {len(handles)} player handles: {handles}')
        with lock:
            PLAYER_HANDLES = handles
    else:
        logger.error('No player handles found!')

    if len(names) > 0:
        logger.info(f'Found {len(names)} player names: {names}')
        with lock:
            PLAYER_NAMES = names
    else:
        logger.error('No player names found!')


def find_replays(directory: str) -> Set[str]:
    """ Finds all replays in a directory. Returns a set."""
    replays = set()
    for root, directories, files in os.walk(directory):
        for file in files:
            if file.endswith('.SC2Replay'):
                file_path = os.path.join(root, file)
                file_path = os.path.normpath(file_path)
                replays.add(file_path)
    return replays


def initialize_AllReplays(ACCOUNTDIR: str) -> Dict[str, Dict[str, float]]:
    """ Creates a sorted dictionary of all replays with their last modified times """
    AllReplays = dict()
    try:
        AllReplays = find_replays(ACCOUNTDIR)
        # Get dictionary of all replays with their last modification time
        AllReplays = ((rep, os.path.getmtime(rep)) for rep in AllReplays)
        AllReplays = {k: {'created': v} for k, v in sorted(AllReplays, key=lambda x: x[1])}
    except Exception:
        logger.error(f'Error during replay initialization\n{traceback.format_exc()}')
    finally:
        return AllReplays


def set_player_winrate_data(winrate_data: Dict[str, Any]) -> None:
    global player_winrate_data
    with lock:
        player_winrate_data = winrate_data.copy()


def initialize_replays_names_handles() -> None:
    """ Checks every few seconds for new replays """
    global AllReplays
    global ReplayPosition

    with lock:
        AllReplays = initialize_AllReplays(SM.settings['account_folder'])
        logger.info(f'Initializing AllReplays with length: {len(AllReplays)}')
        ReplayPosition = len(AllReplays)

    check_names_handles()
    return None


def check_names_handles() -> None:
    try:
        update_names_and_handles(SM.settings['account_folder'], AllReplays)
    except Exception:
        logger.error(f'Error when finding player handles:\n{traceback.format_exc()}')


def check_replays() -> Optional[Dict[str, Any]]:
    """ Checks every few seconds for new replays
    Returns replay data """
    global AllReplays
    global session_games
    global ReplayPosition

    while True:
        logger.debug('Checking for replays....')
        # Check for new replays
        current_time = time.time()
        for root, directories, files in os.walk(SM.settings['account_folder']):
            for file in files:
                file_path = os.path.join(root, file)
                file_path = os.path.normpath(file_path)

                if not file.endswith('.SC2Replay') or file_path in AllReplays:
                    continue

                with lock:
                    AllReplays[file_path] = {'created': os.path.getmtime(file_path)}

                if current_time - os.path.getmtime(file_path) >= 60:
                    continue

                logger.info(f'New replay: {file_path}')
                replay_dict = dict()
                try:
                    replay_dict = parse_and_analyse_replay(file_path, PLAYER_HANDLES)

                    # First check if any commander found
                    if not replay_dict.get('mainCommander') and not replay_dict.get('allyCommander'):
                        logger.info('No commanders found, wont show replay')
                    # Then check if we have good
                    elif len(replay_dict) > 1:
                        logger.debug('Replay analysis result looks good, appending...')
                        with lock:
                            session_games[replay_dict['result']] += 1

                        # What to send
                        out = replay_dict.copy()
                        out['newReplay'] = True
                        if SM.settings.get('show_session', False):
                            out.update(session_games)
                        if SM.settings.get('show_random_on_overlay', False) and len(RNG_COMMANDER) > 0:
                            out.update(RNG_COMMANDER)

                        out['fastest'] = False
                        if CAnalysis is not None and not '[MM]' in file and replay_dict['parser']['isBlizzard']:
                            out['fastest'] = CAnalysis.check_for_record(replay_dict)

                        sendEvent(out)

                    # No output
                    else:
                        logger.error(f'ERROR: No output from replay analysis ({file})')
                    with lock:
                        ReplayPosition = len(AllReplays) - 1

                except Exception:
                    logger.error(traceback.format_exc())

                finally:
                    if len(replay_dict) > 1:
                        upload_to_aom(file_path, replay_dict)
                        # return just parser
                        return replay_dict

        # Wait while checking if the thread should end early
        for i in range(int(SM.settings['replay_check_interval'])):
            time.sleep(0.5)
            if APP_CLOSING:
                return None


def upload_to_aom(file_path: str, replay_dict: Dict[str, Any]) -> None:
    """ Function handling uploading the replay on the Aommaster's server"""
    # Credentials need to be set up
    if SM.settings['aom_account'] in {'', None} or SM.settings['aom_secret_key'] in {'', None}:
        return

    # Never upload old replays
    if (time.time() - os.path.getmtime(file_path)) > 60:
        return

    # Upload only valid non-arcade replays
    if replay_dict.get('mainCommander', None) in [None, ''] or '[MM]' in file_path:
        sendEvent({'uploadEvent': True, 'response': 'Not valid replay for upload'})
        return

    url = f"https://starcraft2coop.com/scripts/assistant/replay.php?username={SM.settings['aom_account']}&secretkey={SM.settings['aom_secret_key']}"
    try:
        with open(file_path, 'rb') as file:
            response = session.post(url, files={'file': file})
        logger.info(f'Replay upload reponse: {response.text}')

        if 'Success' in response.text or 'Error' in response.text:
            sendEvent({'uploadEvent': True, 'response': response.text})

    except Exception:
        sendEvent({'uploadEvent': True, 'response': 'Error'})
        logger.error(f'Failed to upload replay\n{traceback.format_exc()}')


def show_overlay(file: str, add_replay: bool = True) -> Union[str, Dict[str, Any]]:
    """ Shows overlay. If it wasn't analysed before, analyse now.
    Returns:
        'Error'
        Dict of parsed data
        """
    global ReplayPosition

    if file in AllReplays.keys():
        with lock:
            ReplayPosition = list(AllReplays.keys()).index(file)

    # Try to find if the replay is analysed in CAnalysis
    rhash = get_hash(file)
    if CAnalysis is not None:
        data = CAnalysis.get_data_for_overlay(rhash)
        if data is not None:
            sendEvent(data)
            return data

    # Didn't find the replay, analyse
    try:
        replay_dict = parse_and_analyse_replay(file, PLAYER_HANDLES)
        if len(replay_dict) > 1:
            sendEvent(replay_dict)
            if CAnalysis is not None and add_replay:
                CAnalysis.add_parsed_replay(replay_dict)
            return replay_dict
        else:
            logger.error('No output from replay analysis')
    except Exception:
        logger.error(f'Failed to analyse replay: {file}\n{traceback.format_exc()}')
        return 'Error'


async def manager(websocket: websockets.legacy.server.WebSocketServerProtocol, path: str) -> None:
    """ Manages websocket connection for each client """
    overlayMessagesSent = len(OverlayMessages)
    logger.info(f"Starting: {websocket}\nSending init message: {initMessage}")
    await websocket.send(json.dumps(initMessage))
    while True:
        try:
            if len(OverlayMessages) > overlayMessagesSent:
                message = json.dumps(OverlayMessages[overlayMessagesSent])
                overlayMessagesSent += 1
                logger.info(f'#{overlayMessagesSent-1} message is being sent through {websocket}')

                try:  # Send the message
                    await asyncio.wait_for(asyncio.gather(websocket.send(message)), timeout=1)
                except asyncio.TimeoutError:
                    logger.error(f'#{overlayMessagesSent-1} message was timed-out.')
                except websockets.exceptions.ConnectionClosedOK:
                    logger.info('Websocket connection closed (ok).')
                    break
                except websockets.exceptions.ConnectionClosedError:
                    logger.info('Websocket connection closed (error).')
                    break
                except websockets.exceptions.ConnectionClosed:
                    logger.info('Websocket connection closed.')
                    break
                except Exception:
                    logger.error(traceback.format_exc())
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            await asyncio.sleep(0.1)


def server_thread(PORT: int = 7305) -> None:
    """ Creates a websocket server """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        start_server = websockets_serve(manager, 'localhost', PORT)
        logger.info('Starting websocket server')
        loop.run_until_complete(start_server)
        loop.run_forever()
    except Exception:
        logger.error(traceback.format_exc())


def move_in_AllReplays(delta: int) -> None:
    """ Moves across all replays and sends info to overlay to show parsed data """
    global ReplayPosition
    logger.info(f'Attempt to move to {ReplayPosition + delta}/{len(AllReplays)-1}')

    # Check if valid position
    newPosition = ReplayPosition + delta
    if newPosition < 0 or newPosition >= len(AllReplays):
        logger.info(f'We have gone too far. Staying at {ReplayPosition}')
        return

    # Get replay_dict of given replay
    file = list(AllReplays.keys())[newPosition]
    result = show_overlay(file)
    if result == 'Error':
        move_in_AllReplays(delta)


def keyboard_OLDER() -> None:
    """ Show older replay"""
    move_in_AllReplays(-1)


def keyboard_NEWER() -> None:
    """ Show newer replay"""
    move_in_AllReplays(1)


def keyboard_SHOWHIDE() -> None:
    """ Show/hide overlay"""
    logger.info('Show-Hide event')
    sendEvent({'showHideEvent': True})


def keyboard_HIDE() -> None:
    """ Hide overlay """
    logger.info('Hide event')
    sendEvent({'hideEvent': True})


def keyboard_SHOW() -> None:
    """ Show overlay """
    logger.info('Show event')
    sendEvent({'showEvent': True})


def keyboard_PLAYERWINRATES() -> None:
    """Show/hide winrate & notes """
    if most_recent_playerdata:
        sendEvent({'playerEvent': True, 'data': most_recent_playerdata})
    else:
        logger.info(f'Could not send player data event since most_recent_playerdata was: {most_recent_playerdata}')


def wait_for_wake() -> Optional[float]:
    """
    The goal of this function is to detect when a PC was awaken from sleeping.
    It will be checking time, and if there is a big discrepancy, it will return it.
    This function will be run on a separate thread.
    """
    while True:
        start = time.time()

        # Wait 5s
        for i in range(20):
            time.sleep(0.5)
            if APP_CLOSING:
                return None

        # Check the difference
        diff = time.time() - start
        if diff > 20:
            return diff - 10


class WinrateState:
    """ Holds the interlocked state vars the winrate detector relies on.

    These exist because the localhost API briefly reports the *previous* game
    right after a new replay lands; reordering/dropping them reintroduces
    duplicate winrate popups. Do not change this logic - only its location.
    """
    def __init__(self) -> None:
        self.last_game_time = None
        self.last_replay_amount = 0
        self.last_replay_amount_flowing = len(AllReplays)  # Identifies when a replay has been parsed
        self.last_replay_time = 0  # Time when we got the last replay parsed


def winrate_path(resp: Dict[str, Any], st: 'WinrateState', progress_callback: QtCore.pyqtSignal) -> None:
    """ Player-winrate detection. This is the original `check_for_new_game` body,
    relocated verbatim behind its own state object. It is gated on replay-file
    state and MUST NOT be merged with the mission-tracking path. """
    global most_recent_playerdata

    # Skip if winrate data not showing OR no new replay analysed, meaning it's the same game (excluding the first game)
    if len(player_winrate_data) == 0 or len(AllReplays) == st.last_replay_amount:
        return

    # When we get a new replay, mark the time
    if len(AllReplays) > st.last_replay_amount_flowing:
        st.last_replay_amount_flowing = len(AllReplays)
        st.last_replay_time = time.time()

    players = resp.get('players', list())

    # Don't show in if all players are type user - versus game
    all_users = True
    for player in players:
        if player['type'] != 'user':
            all_users = False

    if all_users:
        return

    # Check if we have players in, and it's not a replay
    if len(players) <= 2 or resp.get('isReplay', True):
        return

    # If the last time is the same, then we are in menus. Otherwise in-game.
    if st.last_game_time is None or resp['displayTime'] == 0:
        st.last_game_time = resp['displayTime']
        return

    if st.last_game_time == resp['displayTime']:
        logger.debug(f"The same time (curent: {resp['displayTime']}) (last: {st.last_game_time}) skipping...")
        return

    st.last_game_time = resp['displayTime']

    # Don't show too soon after a replay has been parsed, false positive.
    if time.time() - st.last_replay_time < 15:
        logger.debug('Replay added recently, wont show player winrates right now')
        return

    # Mark this game so it won't be checked it again
    st.last_replay_amount = len(AllReplays)

    # Add the first player name that's not the main player. This could be expanded to any number of players.
    if len(PLAYER_NAMES) > 0:
        test_names_against = [p.lower() for p in PLAYER_NAMES]
    elif len(SM.settings['main_names']) > 0:
        test_names_against = [p.lower() for p in SM.settings['main_names']]
    else:
        logger.error('No main names to test against')
        return

    # Find ally player and get your current player position
    player_names = list()
    player_position = 1
    for player in players:
        if player['id'] in {1, 2} and not player['name'].lower() in test_names_against and player['type'] != 'computer':
            player_names.append(player['name'])
            player_position = 2 if player['id'] == 1 else 1
            break

    # If we have players to show
    if player_names:
        most_recent_playerdata = get_player_data(player_names)
        sendEvent({'playerEvent': True, 'data': most_recent_playerdata})

    # Identify map
    try:
        map_found = identify_map(players)
        if map_found:
            progress_callback.emit([map_found, str(player_position)])
        else:
            logger.error(f"Map not identified: {players}")
    except Exception:
        logger.error(traceback.format_exc())


def poll_interval(resp: Optional[Dict[str, Any]]) -> float:
    """ Adaptive poll cadence. Replaces the old flat 0.5s loop:
        - 10s when SC2 isn't running / connection issues
        - 3s in menus (detect game start without busy-wait)
        - 5s in an active co-op game (only needed to sync clock + detect end)
    """
    if resp is None:
        return 10
    display_time = resp.get('displayTime', 0)
    in_game = (display_time and display_time > 0 and not resp.get('isReplay', True) and len(resp.get('players', list())) > 2)
    return 5 if in_game else 3


def game_state_poller(progress_callback: QtCore.pyqtSignal) -> None:
    """ Single shared poller for everything that needs the live `:6119/game` state.

    Fetches `/game` once per tick, then fans out to two independent paths that
    each own their gating/state: player-winrate detection and mission tracking.
    Settings are re-read every tick so a feature can be effectively on/off
    without a thread-start guard (the thread itself is created once - see SCO.py).
    """
    # Wait a bit for the replay initialization to complete
    time.sleep(4)

    winrate_state = WinrateState()
    tracker = MissionTracker(send_event=sendEvent)

    while True:
        if APP_CLOSING:
            break

        # --- single shared fetch ---
        resp = None
        connection_error = False
        try:
            timeout = 2 if tracker.idle else 5  # short timeout when idle/menus
            resp = session.get('http://localhost:6119/game', timeout=timeout).json()
        except requests.exceptions.ConnectionError:
            connection_error = True
            logger.debug('SC2 request failed. Game not running.')
        except json.decoder.JSONDecodeError:
            logger.info('SC2 request json decoding failed (SC2 is starting or closing)')
        except requests.exceptions.ReadTimeout:
            logger.info('SC2 request timeout')
        except Exception:
            logger.info(traceback.format_exc())

        # --- fan out (each path applies its own gating; no shared continues) ---
        if resp is not None:
            if SM.settings['show_player_winrates']:
                winrate_path(resp, winrate_state, progress_callback)
            if SM.settings.get('show_mission_timeline', True):
                tracker.update(resp)
        elif connection_error and SM.settings.get('show_mission_timeline', True):
            tracker.on_disconnect()

        # --- adaptive sleep (replaces flat 0.5s) ---
        time.sleep(poll_interval(resp))


# Backwards-compatible alias: the shared poller still serves winrate detection.
check_for_new_game = game_state_poller
