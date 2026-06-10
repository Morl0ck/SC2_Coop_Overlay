import copy
import os
import json
import traceback
from datetime import datetime

from SCOFunctions.MLogging import Logger
logger = Logger('SETT', Logger.levels.INFO)


def update_with_defaults(loaded: dict, default: dict):
    """ Checks `loaded` dictionary, and fills all keys that are not present with values
    from `default` dictionary. This is done recursively for any dictionaries inside"""
    if not isinstance(default, dict) or not isinstance(loaded, dict):
        raise TypeError('default and loaded has to be dictionaries')

    for key in default:
        if key not in loaded:
            loaded[key] = copy.deepcopy(default[key])
        elif isinstance(default[key], dict) and not isinstance(loaded[key], dict):
            loaded[key] = copy.deepcopy(default[key])
        elif isinstance(default[key], dict):
            update_with_defaults(loaded[key], default[key])


class CSettings:
    def __init__(self):
        self.filepath = None
        self.default_settings = {
            'start_with_windows': False,
            'start_minimized': False,
            'enable_logging': True,
            'show_player_winrates': True,
            'show_mission_timeline': True,
            'mission_overlay': {
                'anchor_h': 'left',      # 'left' | 'right'
                'anchor_v': 'bottom',    # 'top' | 'bottom'
                'offset_x': 2.0,         # distance from horizontal edge (vh)
                'offset_y': 27.0,        # distance from vertical edge (vh)
                'opacity': 0.9,          # overall panel opacity when shown (0-1)
                'background_opacity': 0.4,  # mission panel background alpha (0-1)
                'show_previous': True,
                'show_upcoming': True,
                'upcoming_count': 3,     # upcoming events shown, incl. the NEXT line (1-3)
                'font_next': 1.55,       # font size for the NEXT line (vh)
                'font_other': 1.2,       # font size for name / previous / upcoming (vh)
                'panel_width': 22.0,     # mission panel width (vh)
                'difficulty': 'auto',    # 'auto' | Casual | Normal | Hard | Brutal
            },
            'show_build_orders': True,
            'build_orders': {
                'default_commander': 'Raynor',
                'display_minutes': 5.0,
                'ocr_enabled': True,
                'ocr_debug': False,
                'use_custom': {},
                'custom': {},
            },
            'build_order_overlay': {
                'anchor_h': 'left',
                'anchor_v': 'top',
                'offset_x': 2.0,
                'offset_y': 2.0,
                'opacity': 0.9,
                'background_opacity': 0.4,
                'font_title': 1.55,
                'font_step': 1.2,
                'panel_width': 22.0,
                'max_steps': 0,
            },
            'duration': 60,
            'monitor': 1,
            'force_hide_overlay': False,
            'show_session': True,
            'show_random_on_overlay': False,
            'dark_theme': True,
            'fast_expand': False, 
            'minimize_to_tray': True,
            'account_folder': None,
            'screenshot_folder': None,
            'hotkey_show/hide': 'Ctrl+Shift+*',
            'hotkey_show': None,
            'hotkey_hide': None,
            'hotkey_newer': 'Ctrl+Alt+/',
            'hotkey_older': 'Ctrl+Alt+*',
            'hotkey_winrates': 'Ctrl+Alt+-',
            'color_player1': '#0080F8',
            'color_player2': '#00D532',
            'color_amon': '#FF0000',
            'color_mastery': '#FFDC87',
            'aom_account': None,
            'aom_secret_key': None,
            'player_notes': dict(),
            'main_names': list(),
            'right_offset': 0,
            'top_offset': 0,
            'width': 0.7,
            'force_width': False,
            'show_charts': True,
            'replay_check_interval': 3,
            'height': 1,
            'font_scale': 1,
            'check_for_multiple_instances': True,
            'subtract_height': 1,
            'rng_choices': dict(),
            'performance_geometry': None,
            'performance_show': False,
            'performance_hotkey': None,
            'performance_processes': ['SC2_x64.exe', 'SC2.exe'],
            'show_chat': False,
            'chat_geometry': (700, 300, 500, 500),
            'chat_font_scale': 1.3,
            'webflag': 'CoverWindow',
            'full_analysis_atstart': False,
            'charts' : {
                'army' : True,
                'supply' : True,
                'kills' : True,
                'collection_rate' : True,
                'minerals' : False,
                'vespene' : False,
                'resources' : False
            },
            'twitchbot': {
                'channel_name': '',
                'bot_name': '',
                'bot_oauth': '',
                'bank_locations': {
                    'Default': '',
                    'Current': ''
                },
                'responses': {
                    'commands': '!names, !syntax, !overlay, !join, !message, !mutator, !spawn, !wave, !resources',
                    'syntax':
                    '!spawn unit_type amount for_player (e.g. !spawn marine 10 2), !wave size tech (e.g. !wave 7 7), !resources minerals vespene for_player \
                                                            (e.g. !resources 1000 500 2), !mutator mutator_name (e.g. !mutator avenger), !mutator mutator_name disable, !join player (e.g. !join 2).',
                    'overlay': 'https://github.com/FluffyMaguro/SC2_Coop_overlay',
                    'maguro': 'www.maguro.one',
                    'names': 'https://www.maguro.one/p/unit-names.html'
                },
                'greetings': {
                    'fluffymaguro': 'Hello Maguro!'
                },
                'banned_mutators': ['Vertigo', 'Propagators', 'Fatal Attraction'],
                'banned_units': [
                    '',
                ],
                'host': 'irc.twitch.tv',
                'port': 6667,
                'auto_start': False,
            }
        }

        self.settings = copy.deepcopy(self.default_settings)

    def load_settings(self, filepath: str):
        """ Load settings from a file"""
        self.filepath = filepath
        try:
            # Try to load base config if there is one
            if os.path.isfile(self.filepath):
                with open(self.filepath, 'r') as f:
                    self.settings = json.load(f)
                if not isinstance(self.settings, dict):
                    raise TypeError('Settings root has to be a dictionary')

            # If it's not there, save default settings
            else:
                with open(self.filepath, 'w') as f:
                    json.dump(self.settings, f, indent=2)
        except Exception:
            logger.error(f'Error while loading settings:\n{traceback.format_exc()}')
            # Save corrupted file on the side
            if os.path.isfile(self.filepath):
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.replace(self.filepath, f'{self.filepath.replace(".json","")}_corrupted ({now}).json')
            self.settings = copy.deepcopy(self.default_settings)

        # Make sure all keys are here. This checks dictionaries recursively and fill missing keys.
        update_with_defaults(self.settings, self.default_settings)

    def save_settings(self):
        """ Save settings to an already definied filepath"""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info('Settings saved')
        except Exception:
            logger.error(f'Error while saving settings\n{traceback.format_exc()}')

    def settings_for_logs(self):
        """ Returns current settings that can be safely saved into logs"""
        out = self.settings.copy()
        out['aom_secret_key'] = "set" if out['aom_secret_key'] else None
        del out['rng_choices']
        del out['player_notes']
        out['twitchbot'] = out['twitchbot'].copy()
        out['twitchbot']['bot_oauth'] = "set" if out['twitchbot']['bot_oauth'] else None
        del out['twitchbot']['greetings']
        del out['twitchbot']['responses']
        return out

    def width_for_graphs(self):
        """ Checks whether the width needs to be changed for graphs"""
        if self.settings['show_charts'] and self.settings['width'] < 0.7 and not self.settings['force_width']:
            self.settings['width'] = 0.7


Setting_manager = CSettings()
