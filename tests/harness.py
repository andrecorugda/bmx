#!/usr/bin/env python3
"""Run the BMX conformance suite against any implementation.

    python3 tests/harness.py '<command>'

The command is run once per case with the document's path appended. It must print the AST as
JSON on stdout and exit 0, or print an error beginning with a `BMX-Ennn` code and exit non-zero.

**This file is not part of the specification.** It is thirty lines of a language that is not the
reference implementation's, and its only job is to demonstrate the claim the format makes about
itself: the suite is DATA, so conformance costs an afternoon in any language rather than a port.
If this harness is inconvenient for your language, throw it away and write your own — the cases
in `cases/` and `errors/` are the specification's executable half, not this script.
"""
import json
import pathlib
import shlex
import subprocess
import sys

HERE = pathlib.Path(__file__).parent


def run(command, path):
    return subprocess.run(shlex.split(command) + [str(path)], capture_output=True, text=True)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    command = sys.argv[1]
    failures = []
    total = 0

    for source in sorted((HERE / "cases").glob("*.bmx")):
        total += 1
        expected = json.loads(source.with_suffix(".json").read_text())
        result = run(command, source)
        if result.returncode != 0:
            failures.append("%s: expected an AST, got %s" % (source.name, result.stderr.strip()))
        else:
            try:
                actual = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                failures.append("%s: stdout is not JSON (%s)" % (source.name, e))
                continue
            if actual != expected:
                failures.append("%s:\n  expected %s\n  actual   %s"
                                % (source.name, json.dumps(expected), json.dumps(actual)))

    for source in sorted((HERE / "errors").glob("*.bmx")):
        total += 1
        expected = source.with_suffix(".error").read_text().strip()
        result = run(command, source)
        if result.returncode == 0:
            failures.append("%s: expected %s, but it parsed" % (source.name, expected))
        else:
            said = (result.stderr or result.stdout).strip()
            if not said.startswith(expected):
                failures.append("%s: expected %s, got %r" % (source.name, expected, said))

    for line in failures:
        print(line)
    print("%d cases, %d passed, %d failed" % (total, total - len(failures), len(failures)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
