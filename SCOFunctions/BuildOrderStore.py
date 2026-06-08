"""Resolve bundled and user-custom build orders."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from SCOFunctions.CommanderOCR import commander_display_name
from SCOFunctions.SC2Dictionaries.BuildOrders import (
    BUILD_ORDER_SOURCE,
    BUILD_ORDER_SOURCE_DATE,
    BUILD_ORDER_VERSION,
    build_orders_defaults,
)
from SCOFunctions.SC2Dictionaries import prestige_names
from SCOFunctions.Settings import Setting_manager as SM


def parse_build_order_text(text: str) -> List[str]:
    """Parse newline or comma-separated build order text into steps."""
    if not text or not text.strip():
        return []

    steps: List[str] = []
    for raw_line in text.replace('\r', '').split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        if ',' in line and not re.match(r'^\d+\s', line):
            parts = [p.strip() for p in line.split(',') if p.strip()]
            steps.extend(parts)
        else:
            steps.append(line)
    return steps


def commander_names() -> List[str]:
    return sorted(prestige_names.keys())


class CBuildOrderStore:
    def get(self, commander: str) -> Optional[Dict[str, object]]:
        if commander not in prestige_names:
            return None

        cfg = SM.settings.get('build_orders', {})
        use_custom = cfg.get('use_custom', {}).get(commander, False)
        custom_text = (cfg.get('custom', {}).get(commander) or '').strip()

        if use_custom and custom_text:
            steps = parse_build_order_text(custom_text)
            source = 'custom'
        else:
            default = build_orders_defaults.get(commander, {})
            steps = list(default.get('steps', []))
            source = 'bundled'

        if not steps:
            return None

        return {
            'commander': commander,
            'display_name': commander_display_name(commander),
            'steps': steps,
            'source': source,
            'version': BUILD_ORDER_VERSION,
            'source_url': BUILD_ORDER_SOURCE,
            'source_date': BUILD_ORDER_SOURCE_DATE,
        }


BuildOrderStore = CBuildOrderStore()
BOS = BuildOrderStore
