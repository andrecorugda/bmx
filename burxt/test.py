#!/usr/bin/env python3
"""Level 2: a document becomes a view the COMPILER checks.

This is the reason the format was worth defining, and it is the one thing a level-1
implementation cannot copy. `tests/harness.py` asks whether this parser matches the spec;
this asks whether the generated view carries the guarantees the document could not.

**The five cases are four refusals and one acceptance, and the order matters.** A generator
that refused everything would pass every refusal test, so the accepting case is asserted
first — it is what makes the other four mean something.

It lived in Burxt's `tests/runner.rs` while `bmx.bx` lived in Burxt's `lib/`. It moved here
with the implementation rather than being left behind as a claim nobody runs.

    python3 burxt/test.py            # needs `burxt` on PATH and a built generator
"""

import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

TYPES = """\
class Order { reference: String, customer: String, total: Decimal<2, RoundHalfEven>, \
amount: Decimal<2>, rate: Decimal<2> }

pure function money2(value: Decimal<2>) -> String { return to_string(value); }
"""

failures = []


def check(name, condition, detail):
    if condition:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}\n{detail}")
        failures.append(name)


def main():
    work = pathlib.Path(tempfile.mkdtemp(prefix="bmx-level2-"))
    generator = work / "bmx-generate"

    built = subprocess.run(
        ["burxt", "build", str(HERE / "examples" / "generate.bx"), "-o", str(generator)],
        capture_output=True, text=True,
    )
    if built.returncode != 0:
        sys.exit(f"the generator does not build:\n{built.stdout}{built.stderr}")

    (work / "types.bx").write_text(TYPES)

    def generate(document, body, name):
        (work / document).write_text(body)
        out = subprocess.run(
            [str(generator), str(work / document), name, "order: Order"],
            cwd=work, capture_output=True, text=True,
        )
        return out.returncode == 0, (out.stdout if out.returncode == 0 else out.stderr)

    def compile_and_run(view, program):
        (work / "view.bx").write_text(view)
        (work / "app.bx").write_text(program)
        out = subprocess.run(["burxt", "run", "app.bx"], cwd=work, capture_output=True, text=True)
        return out.returncode == 0, out.stdout + out.stderr

    # 1. A correct document renders, the slot value is escaped, and the money keeps its scale.
    #    Asserted FIRST: without it, a generator that refused everything would score five out of
    #    five below.
    ok, view = generate(
        "receipt.bmx",
        "# Receipt {{ order.reference }}\n\n"
        "Thanks, **{{ order.customer }}** — {{ to_string(order.total) }}.\n",
        "receipt_view",
    )
    check("a valid document generates", ok, view)
    if ok:
        ran, said = compile_and_run(
            view,
            'use "types.bx";\nuse "view.bx";\n'
            'let o: Order = Order { reference: "R-1", customer: "Tom & <Co>", total: 59.97, '
            'amount: 1.00, rate: 1.00 };\nprint(html_render(receipt_view(o)));\n',
        )
        check("the generated view compiles and runs", ran, said)

        # **Generated code is read by people, so its SHAPE is part of the contract.**
        #
        # Nothing pinned this until 2026-08-17, when the generator was found putting `{` on its own
        # line for a clause-less function. Measured across Burxt 1.3.0's `lib/`: 338 functions put the
        # brace on the signature line, 79 hang it under contract clauses, 4 do neither — so the rule
        # is *the brace hangs only when a clause does*, and the generator was one of the 4.
        #
        # It compiled, ran, and rendered correctly the whole time, which is exactly why this needs an
        # assertion rather than a habit: a reviewer reading generated and hand-written Burxt in one
        # diff sees two styles, and the compiler will never mention it. `lib/`'s convention was uniform
        # and unwritten for 25,000 lines; that is the shape that has bitten this project twice.
        check(
            "a clause-less signature keeps its brace on the signature line, as `lib/` does",
            "-> Html {\n" in view,
            view.split("\n")[6] if len(view.split("\n")) > 6 else view,
        )

        check(
            "it renders what the document said, escaped, with the scale kept",
            "<h1>Receipt R-1</h1>" in said
            and "Tom &amp; &lt;Co&gt;" in said
            and "59.97" in said,
            said,
        )

    # 2. A slot naming a field that does not exist. THE case: in every other template language
    #    this renders an empty string and ships.
    ok, view = generate("typo.bmx", "Hi {{ order.custmer }}.\n", "typo_view")
    if check("a typo still generates", ok, view) is None and ok:
        ran, said = compile_and_run(view, 'use "types.bx";\nuse "view.bx";\n')
        check("a slot naming a missing field is refused", not ran, said)
        check("the refusal names the field the document got wrong",
              "has no field named `custmer`" in said, said)

    # 3. A slot holding something that is not a String. The conversion has to be written in the
    #    DOCUMENT, where a reviewer sees it.
    ok, view = generate("raw.bmx", "Total: {{ order.total }}\n", "raw_view")
    if ok:
        ran, said = compile_and_run(view, 'use "types.bx";\nuse "view.bx";\n')
        check("a Decimal in a String slot is refused", not ran, said)
        check("the refusal says the slot's type was wrong", "must be String" in said, said)

    # 4. Money that would silently re-round, inside a view. This is the thesis reaching the
    #    template: the exact product has four places, and reaching two means rounding, so the
    #    view is refused until the document says how.
    ok, view = generate("money.bmx", "Due: {{ money2(order.amount * order.rate) }}\n", "money_view")
    if ok:
        ran, said = compile_and_run(view, 'use "types.bx";\nuse "view.bx";\n')
        check("a view may not re-round money silently", not ran, said)
        check("the refusal is the rounding rule", "means rounding it" in said, said)

    # 5. A dangerous link target is refused by the GENERATOR, before any page exists.
    ok, said = generate("evil.bmx", "[click](javascript:steal)\n", "evil_view")
    check("a javascript: target is refused at generation", not ok, said)
    check("the generator's refusal carries its code", said.startswith("BMX-G001"), said)

    print()
    if failures:
        sys.exit(f"{len(failures)} failed: {', '.join(failures)}")
    print("level 2: every case passed")


if __name__ == "__main__":
    main()
