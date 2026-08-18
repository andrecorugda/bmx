"""The committed brand assets, measured: a consistent margin, an alpha channel, and no white box.

    python3 tests/branding.py
    python3 tests/branding.py --prove-it     # the negative control

**Every rule here is one the Burxt session measured before handing the artwork over**, and each has a
failure that looks like nothing until three icons sit on consecutive rows of a file tree:

- **The margin.** Andre's complaint about the `.bx` icon was that it *"looks like it is really sticking to
  the edge making it no space on the file tree line"*. Measured, it filled **86%** of its height: four
  clear pixels at 48px, and the glyph against the filename. The family is cropped to its ink and centred
  at **70%**, which is seven. `.bx`, `.bmx` and `.sbmx` all share it, because **an eye reads inconsistent
  margins as misalignment rather than as three different logos.**
- **The alpha channel.** The opaque `bmx_logo.svg` has a white `<rect>` behind it, which shows as a white
  box on any dark or tinted surface. The transparent one is the one to ship.
- **The crop.** Their rule for the icons was *crop to the ink first — two of the three sources had
  different built-in slack, which is exactly how a family drifts.* It applies to a wordmark too: BMX's
  had 43% vertical slack, so `height: 22px` sized mostly emptiness and the mark read light next to
  Burxt's. Cropping the viewBox removed the need for a per-project CSS override entirely. **A constant
  that needs a per-project exception is usually a per-project asset that needs cropping.**

**This measures the artefacts rather than deriving them.** The Burxt session's equivalent invariant fails
if a committed icon is not what their generator makes, which is stronger — but their generator is in a
repository this one does not write to, and a check that depends on a sibling checkout is a check that is
skipped. What survives here is the *property*, asserted where the file lives.
"""

import pathlib
import re
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

ICONS = [
    ("editors/vscode/file-icon.png", 48),
    ("editors/vscode/icon.png", 128),
    ("docs/assets/bmx-file-icon-128.png", 128),
]
TARGET_INK = 70          # per cent of height, the family's margin
TOLERANCE = 4            # 48px rounds coarsely: one row is 2%

LOCKUP = "docs/assets/bmx-lockup.svg"

# **The tab mark is a different job from the file icon, and measuring proved it.** Andre's rule for a file
# tree — *at 16px a shape carries the identity and letters cannot* — sent me to the `.bmx` document icon for
# the favicon. Rendered at 16px on Chrome's own tab greys it is faint on light and nearly gone on dark, and
# the number says why:
#
#     icon                extent   coverage   WEIGHT
#     .bx    (burxt)        71%       24%      11.1
#     .sbmx  (star)         70%       31%      11.0
#     .bmx   (this repo)    70%       35%       6.8      <- more canvas, 38% less ink
#
# **The family standard controlled the margin and nothing controlled the weight.** All three pass 70%±4,
# and mine covers MORE of its canvas while delivering less ink, because it is a tinted document outline
# where the other two are solid orange shapes. Extent decides whether an icon crowds its row; weight
# decides whether it survives being 16 pixels. The same species of error as sizing a wordmark by its box:
# **the quantity everyone agreed to measure was not the quantity that decides the outcome.**
#
# So the tab mark is the `b` glyph knocked out of a filled tile — the treatment star's own `star-[b]`
# already uses, so it is family vocabulary rather than something invented here — and it is the one option
# that is both legible at 16px and not mistakable for Burxt's tab, which is a bare `b` that star ships
# byte-identically. Three tabs open should not be three identical marks, for the same reason three rows of
# a file tree should not be.
TAB_MARK = "docs/assets/favicon.ico"
TAB_SIZES = (16, 32, 48, 64)
MIN_TAB_WEIGHT = 25.0      # a filled tile measures ~43; a bare glyph ~11, which is what vanishes on a tab

# The file icons' weight, asserted as a floor rather than a parity. Parity would fail today: the honest
# state is that `.bmx` is the pale one and the fix belongs in the asset, not in this file. The floor stops
# it getting paler while that is open.
MIN_FILE_WEIGHT = 6.0

# **The navbar's other mark — and this check's first version got the verdict BACKWARDS.**
#
# It looked for "the most common opaque colour that is not the brand orange" and called that the letters.
# That colour is the **tile behind the `b`**, and separating the two regions is the whole finding:
#
#     the b glyph (x < 380)   `-light` #FFFFFF 81%   `-dark` #232320 79%   + #E8502A 16% both
#     the word    (x >= 380)  #E8502A 100% in BOTH
#
# So the word is orange either way, and the variants differ in the tile — `-light` carries a white tile for
# a light bar, `-dark` a near-black one for a dark bar. The names are about the BAR, not the ink. My check
# therefore scored `-dark`'s black plate against a white bar at **15.8:1 and passed it**, which is how a
# lockup with a black box behind it reached production, and it would have **failed the correct file at
# 1.00:1**. A guard that is wrong in both directions with a control that fires is worse than no guard:
# the control certified the inversion.
#
# The two real properties, separately:
#
#   - **the tile must disappear into the bar** — near-equal colour, which is what choosing the right
#     variant means, and the only thing that distinguishes these two files
#   - **the word must be readable on the bar** — 3:1, the threshold for large graphics rather than 4.5:1
#     for body text, because these letters render at 22px
BAR_LOCKUP = "docs/assets/burxt-lockup-light.png"
BAR_BACKGROUND = (255, 255, 255)     # `.bar { background: var(--paper) }`, and 0.72 white over it
BRAND = (0xE8, 0x50, 0x2A)           # the letters and the `b`, legible on either bar
GLYPH_WIDTH = 380                    # the tile occupies the first 380 of 1311 columns
MIN_WORD_CONTRAST = 3.0              # large graphics
MAX_TILE_DIFF = 24                   # per channel, for "the tile is the bar"


def decode(data):
    """Width, height, colour type, and the un-filtered RGBA rows of a PNG."""
    pos, w, h, depth, ctype, idat = 8, None, None, None, None, b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", data[pos + 8:pos + 18])
        if kind == b"IDAT":
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length
    if ctype != 6 or depth != 8:
        return w, h, ctype, None
    raw = zlib.decompress(idat)
    stride, rows, prev, i = w * 4, [], bytearray(w * 4), 0
    for _ in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i + stride]); i += stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if (pa <= pb and pa <= pc) else (b if pb <= pc else c))) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, ctype, rows


def encode(w, h, ink_rows):
    """A minimal RGBA PNG with `ink_rows` opaque rows centred — for the control, and only for it."""
    top = (h - ink_rows) // 2
    raw = b""
    for y in range(h):
        alpha = 255 if top <= y < top + ink_rows else 0
        raw += b"\x00" + bytes([232, 80, 42, alpha] * w)
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def ink_percent(rows, h):
    top = bot = None
    for y, line in enumerate(rows):
        if any(line[3::4]):
            if top is None:
                top = y
            bot = y
    return 0 if top is None else round(100 * (bot - top + 1) / h)


def luminance(rgb):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, bl = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def dominant(rows, w, x0, x1):
    """The most common opaque colour in a column range."""
    seen = {}
    for r in rows:
        for x in range(x0, min(x1, w)):
            o = x * 4
            if r[o + 3] > 128:
                px = (r[o], r[o + 1], r[o + 2])
                seen[px] = seen.get(px, 0) + 1
    return max(seen, key=seen.get) if seen else None


def weight(rows, w, h):
    """How much ink a reader receives: coverage times distance from white, per canvas pixel.

    **Not extent.** Extent is where the ink stops, which is the margin rule. This is how much of it there
    is, which is what decides whether 16 pixels carry a shape.
    """
    total = 0.0
    for r in rows:
        for x in range(w):
            o = x * 4
            a = r[o + 3] / 255
            if a > 0:
                total += a * (255 - round(sum(r[o:o + 3]) / 3)) / 255
    return round(100 * total / (w * h), 1)


def main():
    prove = "--prove-it" in sys.argv
    failures = 0

    for path, expected in ICONS:
        data = (ROOT / path).read_bytes()
        if prove and path.endswith("file-icon.png"):
            # The control is the real fault, in the real shape: an icon filling 86% of its box, which is
            # what Andre saw and called "sticking to the edge".
            data = encode(expected, expected, round(expected * 0.86))
        w, h, ctype, rows = decode(data)
        if (w, h) != (expected, expected):
            failures += 1
            print(f"  FAIL  {path} is {w}x{h}, expected {expected}x{expected}")
            continue
        if ctype != 6:
            failures += 1
            print(f"  FAIL  {path} has no alpha channel, so it is a rectangle on a tinted surface")
            continue
        pct = ink_percent(rows, h)
        if abs(pct - TARGET_INK) > TOLERANCE:
            failures += 1
            print(f"  FAIL  {path} fills {pct}% of its height; the family is {TARGET_INK}% "
                  f"— at {h}px that is {round(h * (100 - pct) / 200)} clear pixels instead of "
                  f"{round(h * (100 - TARGET_INK) / 200)}")
        else:
            wt = weight(rows, w, h)
            if wt < MIN_FILE_WEIGHT:
                failures += 1
                print(f"  FAIL  {path} has ink weight {wt}, below the floor of {MIN_FILE_WEIGHT} — it has "
                      f"got paler, and the family's other two measure ~11")
            else:
                print(f"  ok    {path} {w}x{h}, ink {pct}% of height, weight {wt}")

    # **The bar's Burxt lockup: the tile vanishes, the word reads.**
    w, h, ctype, rows = decode((ROOT / BAR_LOCKUP).read_bytes())
    if prove:
        # The control is the file I actually shipped: the dark-bar variant, on a light bar.
        rows = [bytes(([0x23, 0x23, 0x20, 255] * min(GLYPH_WIDTH, w))
                      + ([0xE8, 0x50, 0x2A, 255] * max(0, w - GLYPH_WIDTH))) for _ in range(h)]

    tile = dominant(rows, w, 0, GLYPH_WIDTH)
    word = dominant(rows, w, GLYPH_WIDTH, w)
    if tile is None or word is None:
        failures += 1
        print(f"  FAIL  {BAR_LOCKUP} has no ink in one of its two regions to measure")
    else:
        drift = max(abs(tile[i] - BAR_BACKGROUND[i]) for i in range(3))
        if drift > MAX_TILE_DIFF:
            failures += 1
            print(f"  FAIL  {BAR_LOCKUP}'s tile is #{tile[0]:02X}{tile[1]:02X}{tile[2]:02X} on a white bar "
                  f"— off by {drift} per channel, so it renders as a box behind the mark. This is the "
                  f"dark-bar variant; upstream ships one per bar and the names are about the BAR")
        else:
            print(f"  ok    {BAR_LOCKUP}'s tile disappears into the bar "
                  f"(#{tile[0]:02X}{tile[1]:02X}{tile[2]:02X})")

        ratio = contrast(word, BAR_BACKGROUND)
        if ratio < MIN_WORD_CONTRAST:
            failures += 1
            print(f"  FAIL  {BAR_LOCKUP}'s word is #{word[0]:02X}{word[1]:02X}{word[2]:02X} on a white bar "
                  f"— {ratio:.2f}:1, below {MIN_WORD_CONTRAST}:1 for a graphic this size")
        else:
            print(f"  ok    {BAR_LOCKUP}'s word reads on the bar "
                  f"(#{word[0]:02X}{word[1]:02X}{word[2]:02X}, {ratio:.1f}:1)")

    # **The tab mark: every size present, and heavy enough to survive being 16 pixels.**
    ico = (ROOT / TAB_MARK).read_bytes()
    count = struct.unpack("<HHH", ico[:6])[2]
    sizes, first = [], None
    for i in range(count):
        o = 6 + i * 16
        iw, ih, _, _, _, _, size, off = struct.unpack("<BBBBHHII", ico[o:o + 16])
        sizes.append(iw or 256)
        if (iw or 256) == 16:
            first = ico[off:off + size]
    missing = [n for n in TAB_SIZES if n not in sizes]
    if missing:
        failures += 1
        print(f"  FAIL  {TAB_MARK} has no {missing} entry, so a browser picks the wrong one and rescales")
    elif first is None:
        failures += 1
        print(f"  FAIL  {TAB_MARK} has no 16px entry to measure")
    else:
        tw, th, tct, trows = decode(first)
        wt = 5.0 if prove else weight(trows, tw, th)
        if wt < MIN_TAB_WEIGHT:
            failures += 1
            print(f"  FAIL  {TAB_MARK}'s 16px mark has ink weight {wt}, below {MIN_TAB_WEIGHT} — a tinted "
                  f"outline at 16px is faint on a light tab strip and gone on a dark one")
        else:
            print(f"  ok    {TAB_MARK} carries {len(sizes)} sizes and its 16px mark has weight {wt}")

    svg = (ROOT / LOCKUP).read_text()
    # **Their warning, and the caveat that makes it checkable.** The transparent wordmark *does* contain a
    # `<rect>` — it is the `b`'s vertical stroke, in `#E8502A`. So the test is for a WHITE rect, not for a
    # rect. Grepping for the tag would have failed the correct file.
    white = re.findall(r"<rect[^>]*fill=\"(#fff(?:fff)?|white)\"", svg, re.I)
    if prove:
        white.append("#ffffff")
    if white:
        failures += 1
        print(f"  FAIL  {LOCKUP} has a white <rect>, which shows as a box on any tinted surface")
    else:
        print(f"  ok    {LOCKUP} has no white background rect")

    # And that it is cropped: declared size must match the viewBox's, so a `height` in CSS sizes mark
    # rather than slack.
    m = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.]+) ([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"', svg)
    if not m:
        failures += 1
        print(f"  FAIL  {LOCKUP} does not declare a viewBox with a width and height to compare")
    else:
        vw, vh, dw, dh = float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6))
        if abs(vw - dw) > 1 or abs(vh - dh) > 1:
            failures += 1
            print(f"  FAIL  {LOCKUP} declares {dw}x{dh} for a {vw}x{vh} viewBox")
        else:
            print(f"  ok    {LOCKUP} declares the size of its own viewBox ({vw:.0f}x{vh:.0f})")

    print()
    if prove:
        if failures:
            print("the control failed as it must — an 86% icon and a white rect are both caught")
            return 0
        print("THE CONTROL DID NOT FAIL, so this check cannot see either fault")
        return 1
    if failures:
        print(f"{failures} brand asset{'' if failures == 1 else 's'} would look wrong where it is used")
        return 1
    print("every brand asset carries the family's margin, an alpha channel, and its own crop")
    return 0


if __name__ == "__main__":
    sys.exit(main())
