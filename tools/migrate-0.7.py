# not-burxt: gap — checks THIS REPOSITORY rather than the format, so the standalone argument never reached it
"""Rewrites BMX 0.6 fences to 0.7: `::: name head` / `:::` becomes `:name: head` / `:!name:`.

    python3 tools/migrate-0.7.py FILE...          # rewrites in place
    python3 tools/migrate-0.7.py --check FILE...  # reports, changes nothing

**This exists because a closer has to learn its own name, and only the document knows it.** A `sed`
cannot do this job: `:::` carries no name, so the replacement depends on which opener is still open —
which means tracking a stack, which means a program. Handing star-burxt a regex would have handed it a
silent mis-migration on its first nested component.

It rewrites markdown fences too (```bmx blocks in docs/), because the documentation's examples are
documents and a format change that leaves them behind is a format change that ships a lie.

**What it deliberately does NOT do:** guess. A closer with no matching opener, an unterminated block,
or a `::::` longer fence whose meaning depended on the length rule 0.7 deletes — all three stop the
file with a message rather than producing something plausible. A migration that half-works is worse
than one that refuses, because you find out from the diff instead of from the parser.
"""

import re
import sys

PLAIN = False

OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>:{3,})[ \t]*(?P<name>[A-Za-z][A-Za-z0-9_-]*)[ \t]*(?P<head>.*)$")
CLOSE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>:{3,})[ \t]*$")
CODE = re.compile(r"^[ \t]*(`{3,})")


def migrate(text, path):
    out, stack, problems = [], [], []
    in_code = None
    for n, line in enumerate(text.split("\n"), 1):
        # A code fence's content is never parsed (SPEC 2.4), so it is never rewritten either — except
        # that a ```bmx fence in the DOCS is a document, and those are exactly what has to change. The
        # info string decides: `bmx` and `sbmx` are documents, anything else is somebody's code.
        if in_code is not None:
            if line.strip().startswith(in_code):
                # **The closing fence has to `continue`.** Without it the line falls through to the
                # opener match below, which sees ``` and opens a NEW code block — so everything after
                # the first code fence in the file was treated as code and left unmigrated. It
                # reported `061-an-indented-code-fence-keeps-its-shape` as having an unclosed block,
                # which is how it was caught: the tool accused a fixture that was fine.
                in_code = None
                out.append(line)
                continue
            if not in_code_is_document:
                out.append(line)
                continue
        m = CODE.match(line)
        if m and in_code is None:
            in_code = m.group(1)
            info = line.strip()[len(m.group(1)):].strip()
            # `--plain-fences` also treats an info-less fence as a document. SPEC.md and errors.md
            # write their examples in bare ``` blocks, so without this the normative document keeps
            # 0.6 syntax while the parser refuses it — the worst possible split.
            in_code_is_document = info in ("bmx", "sbmx") or (PLAIN and info == "")
            out.append(line)
            continue

        m = CLOSE.match(line)
        if m:
            if not stack:
                problems.append(f"{path}:{n}: a closer with nothing open — migrate this file by hand")
                out.append(line)
                continue
            name, fence = stack.pop()
            if len(m.group("fence")) != len(fence):
                # 0.7 has no fence-length rule: a `::::` that closed a `:::` did so BECAUSE it was
                # longer, and that reason no longer exists. Naming the closer changes the meaning of
                # the document, so this one is a person's decision.
                problems.append(
                    f"{path}:{n}: `{m.group('fence')}` closed a `{fence}` by being longer, which 0.7 removes"
                )
            out.append(f"{m.group('indent')}:!{name}:")
            continue

        m = OPEN.match(line)
        if m:
            stack.append((m.group("name"), m.group("fence")))
            head = m.group("head").rstrip()
            out.append(f"{m.group('indent')}:{m.group('name')}:" + (f" {head}" if head else ""))
            continue

        out.append(line)

    if stack:
        problems.append(f"{path}: {len(stack)} block(s) never closed: " + ", ".join(n for n, _ in stack))
    return "\n".join(out), problems


def main():
    args = sys.argv[1:]
    global PLAIN
    check = "--check" in args
    PLAIN = "--plain-fences" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(__doc__.split("\n")[2].strip())
        return 1
    bad = 0
    for path in files:
        text = open(path).read()
        new, problems = migrate(text, path)
        for p in problems:
            print("  " + p)
            bad = 1
        if new != text:
            if check:
                print(f"  would rewrite {path}")
            else:
                open(path, "w").write(new)
                print(f"  rewrote {path}")
    return bad


if __name__ == "__main__":
    sys.exit(main())
