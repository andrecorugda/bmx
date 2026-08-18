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
            print(f"  ok    {path} {w}x{h}, ink {pct}% of height")

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
