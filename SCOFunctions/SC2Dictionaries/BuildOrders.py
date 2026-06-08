"""
Bundled commander build orders from starcraft2coop.com (CC-BY-NC-SA-4.0).

Source: https://starcraft2coop.com/commanders/
Author: Aommaster
License: CC-BY-NC-SA-4.0
source_date: 2026-06-08
"""

BUILD_ORDER_VERSION = '2026.06.08'
BUILD_ORDER_SOURCE = 'https://starcraft2coop.com/commanders/'
BUILD_ORDER_SOURCE_DATE = '2026-06-08'

build_orders_defaults = {
    'Abathur': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Overlord',
            '17 Roach Warren',
            '20 Spine Crawler',
            '19 Spine Crawler',
            '18 Extractor',
            '17 Extractor',
            '20 Roach',
            '22 Overlord',
            '22 Hatchery',
            '22 Extractor',
            '22 Extractor',
        ],
    },
    'Alarak': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Pylon',
            '15 Assimilator (No Probes)',
            '18 Pylon (Overcharge)',
            '20 Nexus Probes -> Assimilator',
            '21 Assimilator',
            '22 Gateway',
        ],
    },
    'Artanis': {
        'source_date': '2026-06-08',
        'steps': [
            '15 Gateway',
            '17 Assimilator',
            '18 Assimilator Chrono Gateway',
            '21 Zealot -> Rocks',
            '24 Zealot Chrono Nexus',
            '31 Nexus',
            '33 Cybernetics Core',
            '34 Pylon',
        ],
    },
    'Dehaka': {
        'source_date': '2026-06-08',
        'steps': [
            '23 Extractor',
            '23 Primal Warden',
            '25 Extractor',
            "29 Glevig's Den",
            '29 2x Zerglings -> Rocks Primal Warden -> Rocks',
            '31 Primal Hive',
        ],
    },
    'Fenix': {
        'source_date': '2026-06-08',
        'steps': [
            '15 Pylon',
            '16 Assimilator',
            '17 Robotics Facility',
            '17 Assimilator',
            '22 Immortal + AI -> Rocks',
            '26 Pylon',
            '31 Nexus',
        ],
    },
    'Horner': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Supply Depot',
            '17 Command Center',
            '18 Assault Galleon',
            '19 Refinery',
            '20 Refinery',
            '20 2x Hellions -> Rocks',
        ],
    },
    'Karax': {
        'source_date': '2026-06-08',
        'steps': [
            '15 Nexus',
            '15 Pylon',
            '17 Assimilator',
            '18 Assimilator',
            '20 Forge',
            '26 Cannon -> Gas Rock',
            '32 Cannon -> Gas Rock',
        ],
    },
    'Kerrigan': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Overlord',
            '14 Macro Hatchery at Rocks',
            '19 Extractor',
            '21 Extractor',
            '24 Macro Hatchery at Rocks',
            '28 Spawning Pool',
            '33 Overlord Kerrigan -> Rocks',
        ],
    },
    'Mengsk': {
        'source_date': '2026-06-08',
        'steps': [
            '13 Bunker Calldown at Expo',
            '16 laborers on Main',
            '24 Bunker keeping',
            '25 Unload expo bunker + clear rocks',
            '28 4 Laborers -> Expo',
            '30 Enlistment Center',
            '32 Troopers to Laborers to fast-build expo',
            '32 Bunker Calldown, Unload to Laborer',
            '38 Refinery (3 Laborers)',
            '39 Refinery (3 Laborers)',
            '41 Refinery (3 Laborers)',
            '45 Barracks (8 Laborers)',
            '50 Factory (8 Laborers)',
            '53 Starport (8 Laborers)',
            '56 Imperial Witness',
        ],
    },
    'Nova': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Refinery',
            '15 Refinery',
            '18 Command Center',
            '19 Barracks',
            '22 Marines -> Rocks',
        ],
    },
    'Raynor': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Supply Depot',
            '16 Command Center at Rocks',
            '19 Barracks',
            '20 Orbital Command Upgrade',
            '20 Command Center at Rocks',
            '21 Orbital Command Upgrade',
            '21 Refinery',
            '22 Refinery',
            '25 Command Center at Main',
        ],
    },
    'Stetmann': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Overlord',
            '14 Extractor (2 drones on completion)',
            '14 Extractor (2 drones on completion)',
            '19 Spawning Pool',
            '18 Lair',
            '18 2x Zerglings to Expo',
            '20 Drone',
            '21 Infestation Pit',
            '20 Drone',
            '21 Overlord',
            'Saturate gasses at 200 minerals',
            '21 Hive',
            'Saturate mineral line',
        ],
    },
    'Stukov': {
        'source_date': '2026-06-08',
        'steps': [
            '15 Overlord',
            '15 Refinery',
            '19 Command Center at Rocks',
            '21 Refinery',
            '21 Anaerobic Enhancement',
            '22 Engineering Bay',
            '22 Overlord',
            '24 Broodling Gestation',
            '25 Barracks',
        ],
    },
    'Swann': {
        'source_date': '2026-06-08',
        'steps': [
            '14 Supply Depot',
            "16 Factory (4 SCV's)",
            "18 Billy (4 SCV's)",
            "18 Billy (4 SCV's)",
            "21 Command Center (8 SCV's)",
        ],
    },
    'Tychus': {
        'source_date': '2026-06-08',
        'steps': [
            '17 Command Center',
            '18 Refinery',
            '19 Refinery',
            '20 Engineering Bay',
            '22 2x Turrets -> Rocks',
        ],
    },
    'Vorazun': {
        'source_date': '2026-06-08',
        'steps': [
            '13 Dark Pylon',
            '15 Assimilator',
            '16 Assimilator',
            '18 Gateway',
            '19 Pylon',
            '22 Change Rally to Expansion',
            '23 Cybernetics Core',
            '27 Shadowguard -> Gas -> Main',
            '28 Twilight + Warp Gate',
            '29 Assimilators + Nexus',
        ],
    },
    'Zagara': {
        'source_date': '2026-06-08',
        'steps': [
            '9 Extractor',
            '11 Spawning Pool',
            '11 Extractor',
            '11 Overlord',
            '11 Baneling Nest',
            '10 Zergling -> Rocks',
            '12 Zergling -> Rocks',
            '19 Hatchery',
        ],
    },
    'Zeratul': {
        'source_date': '2026-06-08',
        'steps': [
            '18 Probe -> Expo',
            '19 Zoraya Legion',
            '21 Nexus',
        ],
    },
}

build_orders = build_orders_defaults
