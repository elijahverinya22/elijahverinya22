"""Post-process profile images so everything follows the cloudy palette.

Run by .github/workflows/grs.yml after the stats cards are generated:
  1. recolor top-langs cards from GitHub's language colors to palette blues
  2. fetch skill icons (light + dark) and round their corners further
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
ICONS = "html,css,js,c,java,r,py,git,vscode,ps"
ICON_RADIUS = 96  # skillicons ships rx=60 on a 256 tile
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


def round_icons(theme: str, name: str) -> None:
    svg = fetch(f"https://skillicons.dev/icons?i={ICONS}&theme={theme}")
    svg, n = re.subn(r'rx="60"', f'rx="{ICON_RADIUS}"', svg)
    if n == 0:
        raise RuntimeError("skillicons markup changed: no rx=60 tiles found")
    (OUT / name).write_text(svg, encoding="utf-8")
    print(f"{name}: rounded {n} icon tiles")


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
    round_icons("light", "skills.svg")
    round_icons("dark", "skills-dark.svg")
    for name, spec in BADGES.items():
        pill_badge(name, spec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
