"""Post-process profile images so everything follows the cloudy palette.

Run by .github/workflows/grs.yml after the stats cards are generated:
  1. recolor top-langs cards from GitHub's language colors to palette blues
  2. draw the tech stack icons in palette colors on soft rounded tiles
  3. fetch social badges and clip them into soft pills
"""
import re
import sys
import urllib.request
from pathlib import Path

OUT = Path("profile")
PALETTE = {"FFFFFF", "F4FAFF", "EAF6FF", "BFE3FF", "9AD0F5", "6FB7E9", "3B6E99", "12233A"}
LANG_COLORS = {
    "top-langs.svg": ["3B6E99", "6FB7E9", "9AD0F5", "7FA6C6", "BFE3FF"],
    "top-langs-dark.svg": ["BFE3FF", "9AD0F5", "6FB7E9", "7FA6C6", "3B6E99"],
}
SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@16.38.0/icons"
# Tech stack in display order. Value: simple-icons slug, or a key in CUSTOM_GLYPHS
# for brands simple-icons no longer ships (VS Code, Photoshop).
STACK = ["html5", "css", "javascript", "c", "openjdk", "r", "python", "git", "vscode", "photoshop"]
ICON_THEMES = {  # file: (tile color, logo color)
    "skills.svg": ("BFE3FF", "3B6E99"),
    "skills-dark.svg": ("1E3A5F", "BFE3FF"),
}
TILE, GAP, TILE_RADIUS, DISPLAY_HEIGHT = 256, 44, 96, 48
CUSTOM_GLYPHS = {
    # VS Code ribbon outline (from skillicons.dev, MIT), flattened to one color; 256 grid
    "vscode": (
        '<path d="M33.7158 100.208C33.7158 100.208 28.9814 96.795 34.6627 92.2381L47.8994 80.402C47.8994 80.402 51.6869 76.4172 55.6915 79.8891L177.84 172.368V216.714C177.84 216.714 177.781 223.678 168.844 222.908L33.7158 100.208Z"/>'
        '<path d="M65.1997 128.792L33.7157 157.415C33.7157 157.415 30.4805 159.822 33.7157 164.123L48.3333 177.418C48.3333 177.418 51.8052 181.147 56.9341 176.905L90.3119 151.596L65.1997 128.792Z"/>'
        '<path d="M120.474 129.029L178.215 84.9391L177.84 40.83C177.84 40.83 175.374 31.2033 167.148 36.2139L90.312 106.145L120.474 129.029Z"/>'
        '<path d="M168.844 222.968C172.198 226.4 176.262 225.276 176.262 225.276L221.259 203.103C227.019 199.177 226.21 194.305 226.21 194.305V61.8982C226.21 56.0788 220.252 54.0667 220.252 54.0667L181.253 35.267C172.731 30 167.148 36.2139 167.148 36.2139C167.148 36.2139 174.328 31.0455 177.84 40.83V215.905C177.84 217.109 177.583 218.292 177.071 219.358C176.045 221.429 173.816 223.362 168.47 222.553L168.844 222.968Z"/>'
    ),
    # Photoshop "Ps" mark: rounded square outline with lettering; 256 grid
    "photoshop": (
        '<rect x="44" y="52" width="168" height="152" rx="36" fill="none" stroke="currentColor" stroke-width="14"/>'
        '<text x="128" y="160" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        'font-size="84" font-weight="bold">Ps</text>'
    ),
}

BADGES = {
    "badge-email.svg": "email-6FB7E9?style=for-the-badge&logo=gmail&logoColor=FFFFFF",
    "badge-facebook.svg": "facebook-3B6E99?style=for-the-badge&logo=facebook&logoColor=FFFFFF",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-build"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def recolor_langs(name: str, colors: list[str]) -> None:
    path = OUT / name
    svg = path.read_text(encoding="utf-8")
    mapping: dict[str, str] = {}

    def swap(match: re.Match) -> str:
        hex_ = match.group(1).upper()
        if hex_ in PALETTE:
            return match.group(0)
        if hex_ not in mapping:
            mapping[hex_] = colors[len(mapping) % len(colors)]
        return f'fill="#{mapping[hex_]}"'

    path.write_text(re.sub(r'fill="#([0-9a-fA-F]{6})"', swap, svg), encoding="utf-8")
    print(f"{name}: recolored {len(mapping)} languages")


def simple_icon_path(slug: str) -> str:
    svg = fetch(f"{SIMPLE_ICONS}/{slug}.svg")
    m = re.search(r'<path d="([^"]+)"', svg)
    if not m:
        raise RuntimeError(f"simple-icons markup changed for {slug}")
    return m.group(1)


def build_icons(glyphs: dict[str, str]) -> None:
    """Draw the stack as palette-colored rounded tiles, laid out like skillicons."""
    width = len(STACK) * (TILE + GAP) - GAP
    for name, (tile, logo) in ICON_THEMES.items():
        tiles = []
        for i, key in enumerate(STACK):
            x = i * (TILE + GAP)
            if key in CUSTOM_GLYPHS:
                art = f'<g fill="#{logo}" color="#{logo}">{CUSTOM_GLYPHS[key]}</g>'
            else:  # simple-icons are 24x24; center them at 144px
                art = f'<svg x="56" y="56" width="144" height="144" viewBox="0 0 24 24"><path fill="#{logo}" d="{glyphs[key]}"/></svg>'
            tiles.append(
                f'<svg x="{x}" width="{TILE}" height="{TILE}" viewBox="0 0 256 256">'
                f'<rect width="256" height="256" rx="{TILE_RADIUS}" fill="#{tile}"/>{art}</svg>'
            )
        display_width = round(width * DISPLAY_HEIGHT / TILE)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{display_width}" height="{DISPLAY_HEIGHT}" '
            f'viewBox="0 0 {width} {TILE}"><title>tech stack</title>{"".join(tiles)}</svg>'
        )
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name}: drew {len(STACK)} icons")


def pill_badge(name: str, spec: str) -> None:
    svg = fetch(f"https://img.shields.io/badge/{spec}")
    m = re.match(r'(<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"[^>]*>)(.*)</svg>\s*$', svg, re.S)
    if not m:
        raise RuntimeError(f"unexpected shields markup for {name}")
    head, w, h, body = m.groups()
    clip = f'<clipPath id="pill"><rect width="{w}" height="{h}" rx="{float(h) / 2}"/></clipPath>'
    (OUT / name).write_text(f'{head}{clip}<g clip-path="url(#pill)">{body}</g></svg>', encoding="utf-8")
    print(f"{name}: clipped to pill")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for name, colors in LANG_COLORS.items():
        recolor_langs(name, colors)
    build_icons({k: simple_icon_path(k) for k in STACK if k not in CUSTOM_GLYPHS})
    for name, spec in BADGES.items():
        pill_badge(name, spec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
