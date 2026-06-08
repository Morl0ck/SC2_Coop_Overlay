"""Fetch build orders from starcraft2coop.com commander guides.

Run from repo root:
    python Development/extract_build_orders.py

Prints a Python dict snippet for BuildOrders.py (not written automatically).
"""
from __future__ import annotations

import re
import urllib.request

BASE = 'https://starcraft2coop.com/commanders/'

COMMANDER_PAGES = {
    'Abathur': 'abathur',
    'Alarak': 'alarak',
    'Artanis': 'artanis',
    'Dehaka': 'dehaka',
    'Fenix': 'fenix',
    'Horner': 'horner',
    'Karax': 'karax',
    'Kerrigan': 'kerrigan',
    'Mengsk': 'mengsk',
    'Nova': 'nova',
    'Raynor': 'raynor',
    'Stetmann': 'stetmann',
    'Stukov': 'stukov',
    'Swann': 'swann',
    'Tychus': 'tychus',
    'Vorazun': 'vorazun',
    'Zagara': 'zagara',
    'Zeratul': 'zeratul',
}


def fetch_html(slug: str) -> str:
    url = BASE + slug
    req = urllib.request.Request(url, headers={'User-Agent': 'SCO-BuildOrder-Extractor/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='replace')


def strip_tags(html: str) -> str:
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    html = re.sub(r'<[^>]+>', '', html)
    return html.replace('&nbsp;', ' ').strip()


def parse_build_order(html: str) -> list[str]:
    # Locate Build Order section until next h2/h3 section.
    m = re.search(r'Build Order\s*</h2>(.*?)(?:<h2|<h3|$)', html, flags=re.I | re.S)
    if not m:
        return []
    section = strip_tags(m.group(1))

    # Primary format: supply-count steps separated by spaces in one paragraph.
    lines = [ln.strip() for ln in section.split('\n') if ln.strip()]
    if not lines:
        return []

    body = ' '.join(lines)
    # Drop leading explanatory sentences before first supply token.
    start = re.search(r'\b\d+\s+[A-Za-z]', body)
    if start:
        body = body[start.start():]

    # Split on supply numbers while keeping them attached to the step text.
    parts = re.split(r'(?=\b\d+\s+)', body)
    steps = []
    for part in parts:
        part = part.strip(' ,.;')
        if not part:
            continue
        if re.match(r'^\d+\s', part):
            steps.append(part)
        elif steps:
            steps[-1] = steps[-1] + ' ' + part
        else:
            steps.append(part)

    cleaned = []
    for step in steps:
        step = re.sub(r'\s+', ' ', step).strip()
        if step.lower().startswith('note that'):
            break
        if len(step) > 3:
            cleaned.append(step)
    return cleaned


def main() -> None:
    all_orders = {}
    for commander, slug in COMMANDER_PAGES.items():
        try:
            html = fetch_html(slug)
            steps = parse_build_order(html)
            all_orders[commander] = steps
            print(f'# {commander}: {len(steps)} steps')
        except Exception as exc:
            print(f'# {commander}: FAILED ({exc})')
            all_orders[commander] = []

    print('\nbuild_orders_defaults = {')
    for commander, steps in all_orders.items():
        print(f"    '{commander}': {{")
        print("        'source_date': '2026-06-08',")
        print(f"        'steps': {steps!r},")
        print('    },')
    print('}')


if __name__ == '__main__':
    main()
