# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
"""Indents BMX documents so nesting is visible: one level per open block.

    python3 tools/fmt.py FILE...            # rewrites in place
    python3 tools/fmt.py --check FILE...    # reports, changes nothing
    python3 tools/fmt.py --stdin < doc.bmx  # prints to stdout

Handles `.bmx` files and the ```bmx fences inside markdown, so the documentation's examples and the
documents they describe stay in the same shape.

**Indentation is insignificant to the parser (SPEC §1), which is exactly why a tool has to own it.**
A wrong indent cannot change what a document means — and cannot be caught by anything either, so a
reviewer who trusts the columns can be trusted into the wrong block. Two answers to that, and this is
one: make the columns mechanical. The other is `BMX-W005`, which warns when they disagree with the
nesting; a warning tells you, a formatter fixes it.

**One thing it will not touch: a document containing a code fence.** A fenced block's content keeps
everything past its OWN fence's indentation (§2.4), so moving the fence moves the content with it —
and if the content is a document showing BMX, reindenting it twice would be reindenting an example of
reindenting. Refused rather than half-done, and it says which file.

This is deliberately not a formatter. It does not touch line length, blank lines, head spacing or
inline content. It does the one thing whose absence Andre pointed at, and stops.
"""

import re
import sys

OPENER = re.compile(r"^[ \t]*:([A-Za-z][A-Za-z0-9_-]*):(.*)$")
CLOSER = re.compile(r"^[ \t]*:!([A-Za-z][A-Za-z0-9_-]*):[ \t]*$")
CODE = re.compile(r"^[ \t]*(`{3,})")
STEP = "  "


def one_liner(name, rest):
    """`:span: class=box :!span:` opens and closes on its line, so it does not change the depth."""
    target = f":!{name}:"
    return rest.rstrip().endswith(target)


def indent(lines, path):
    out, depth, problems = [], 0, []
    for n, line in enumerate(lines, 1):
        if CODE.match(line):
            problems.append(f"{path}: line {n} holds a code fence, whose content is relative to it — left alone")
            return lines, problems

        m = CLOSER.match(line)
        if m:
            depth = max(0, depth - 1)
            out.append(STEP * depth + line.strip())
            continue

        m = OPENER.match(line)
        if m:
            out.append(STEP * depth + line.strip())
            if not one_liner(m.group(1), m.group(2)):
                depth += 1
            continue

        stripped = line.strip()
        out.append(STEP * depth + stripped if stripped else "")
    if depth != 0:
        problems.append(f"{path}: {depth} block(s) left open — indented as far as it got")
    return out, problems


def process(text, path):
    """Markdown gets its ```bmx fences indented; a `.bmx` file is one document throughout."""
    if not path.endswith(".md"):
        lines, problems = indent(text.split("\n"), path)
        return "\n".join(lines), problems

    out, problems, block, fence = [], [], None, None
    for line in text.split("\n"):
        if block is not None:
            if line.strip().startswith(fence):
                done, ps = indent(block, path)
                out.extend(done)
                problems.extend(ps)
                out.append(line)
                block, fence = None, None
            else:
                block.append(line)
            continue
        m = CODE.match(line)
        if m and line.strip()[len(m.group(1)):].strip() in ("bmx", "sbmx"):
            fence, block = m.group(1), []
            out.append(line)
            continue
        out.append(line)
    if block is not None:
        problems.append(f"{path}: a ```bmx fence never closed")
        out.extend(block)
    return "\n".join(out), problems


def main():
    args = sys.argv[1:]
    if "--stdin" in args:
        text, problems = process(sys.stdin.read(), "<stdin>")
        sys.stdout.write(text)
        return 0
    check = "--check" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print("usage: fmt.py [--check] FILE...")
        return 1
    changed = 0
    for path in files:
        text = open(path).read()
        new, problems = process(text, path)
        for p in problems:
            print("  " + p)
        if new != text:
            changed += 1
            if check:
                print(f"  would reindent {path}")
            else:
                open(path, "w").write(new)
                print(f"  reindented {path}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
