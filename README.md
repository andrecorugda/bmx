# BMX

**Burxt Markup Language, Extensible** — markdown with one unambiguous reading and a typed hole
in it.

The name says where it came from and not where it can go. **Any language can implement BMX**;
the format is a grammar and a conformance suite, and [`BOUNDARY.md`](BOUNDARY.md) exists to keep
one host's semantics out of it. What the name honestly signals is where it goes *furthest* — the
checking level below is one only a language with types and contracts can reach.

```bmx
# Receipt {{ order.reference }}

Thank you, {{ customer.name }}. Your total is **{{ order.total }}**.

- Delivery: {{ order.delivery }}
- Paid: {{ order.paid_at }}
```

Two things make it different from every other template format, and neither is the syntax.

## 1. It always fails loudly

Markdown's defining property is that nothing is ever a syntax error. `*bold` with no closing
star renders as the characters `*bold`. An unterminated code fence swallows the rest of the
document. Three dialects — CommonMark, GFM, Pandoc — disagree about the rest, so the same file
means different things in different tools.

BMX has one reading, and input that is not valid BMX is an **error with a code**, never output
that looks nearly right:

```
BMX-E001 at 6: unterminated slot: no }} on this line
```

That matters most where documents are generated rather than typed. A truncated document gets
told, instead of shipping a page with a stray brace in it.

## 2. The expression slot belongs to the host language

`{{ … }}` is where an expression goes. **BMX does not define what an expression is** — that is
the host's, and it is why a format this small can be adopted by a language with types and by one
without.

[`BOUNDARY.md`](BOUNDARY.md) draws that line precisely, and defines two conformance levels:

| Level | What it means | Who can reach it |
|---|---|---|
| **1 — renders** | parses per the spec, substitutes slot values, escapes on output | any language |
| **2 — checks** | every slot expression verified against a declared interface *before* the document renders | a language with a type system |

Level 2 is why the format was worth defining. **A template is the last place in most programs
where nothing is checked** — the slot names a field that may not exist, holds a type it cannot
state, and escapes by convention. Level 2 is the level at which that stops being true.

## The documents

| | |
|---|---|
| [`SPEC.md`](SPEC.md) | the grammar. Normative |
| [`BOUNDARY.md`](BOUNDARY.md) | what BMX owns and what the host owns, and the conformance levels |
| [`ESCAPING.md`](ESCAPING.md) | normative, and the one place BMX is opinionated about output |
| [`VERSIONING.md`](VERSIONING.md) | the conformance suite *is* the semver |
| [`tests/`](tests) | the specification's executable half |

**Where the spec and the tests disagree, the tests win.** A claim not in `tests/` is a claim no
implementation has to honour.

**Documentation: [bmx.burxt-lang.org](https://bmx.burxt-lang.org)** — how to write a document,
how to turn it into a page, how to style the output, and every error it can give you.

## Two implementations, on purpose

BMX ships a **reference parser** — [`reference/bmx.js`](reference/bmx.js), zero dependencies,
written to be read — alongside the spec, not instead of one. CommonMark shipped `cmark` the same
way, and the three-dialect mess this format exists to fix came from a spec that had no reference.

The second implementation is [`burxt/bmx.bx`](burxt/bmx.bx), for
[Burxt](https://burxt-lang.org). It lived in Burxt's standard library until it had a version worth
pinning; it lives here now, for the same reason `bmx.js` does. The two directory names mean
different things and that is deliberate: **`reference/` is a role and `burxt/` is an audience.**
`bmx.js` exists to define what the format does, `bmx.bx` exists to be used by Burxt programs.

**They must agree**, and that is a test:

```sh
python3 tests/agree.py 'node reference/bmx.js' '<the other one>'
```

The conformance suite asks *does this implementation match what we wrote down*. Agreement asks
the harder question — *do two implementations reach the same answer where nothing was written
down* — and those come apart exactly where a spec is ambiguous. A suite cannot find its own blind
spots, because it is made of them.

It already earned this. A slot's `offset` was being reported three bytes early inside a
multi-line paragraph, off by the trailing spaces stripped from an earlier line. Nothing in the
suite covered it; planning the second implementation is what surfaced it. It is
`tests/cases/023-slot-offset-survives-a-stripped-line` now.

**Stated so it is not overclaimed:** both current implementations have one author, so their
agreement catches drift and regression rather than proving the spec unambiguous. Only a
third-party implementation does that — see [`VERSIONING.md`](VERSIONING.md) on what 1.0 requires.

## Running the suite

The cases are **data** — `input → expected AST` files. That is the whole design: conformance
costs an afternoon in any language rather than a port.

```sh
python3 tests/harness.py '<your parser command>'
```

The command is run once per case with the document's path appended, and must print the AST as
JSON and exit 0, or print an error beginning with its `BMX-Ennn` code and exit non-zero.

The harness is thirty lines and is deliberately not part of the specification. If it is
inconvenient for your language, throw it away and write your own.

## Status

**0.12. Two implementations, one author — so this is not yet a standard**, and the difference is
worth being blunt about. [`VERSIONING.md`](VERSIONING.md) says what 1.0 requires: an
implementation written by someone who did **not** write this spec, and a real document set that
has tested the absences in `SPEC.md` §7 against something other than imagination.

| Implementation | Level | Where |
|---|---|---|
| `reference/bmx.js` | 1 — renders | here, zero dependencies |
| `burxt/bmx.bx` | 1 today; level 2 is its road | [Burxt](https://burxt-lang.org) |

Level 2 in Burxt is a generator that turns a document into a `pure function … -> Html` whose
slots are ordinary typed expressions — so the compiler checks them, and a rounding contract
survives all the way to the tag. That is the capability no level-1 host can copy, and it is why
the format is worth adopting rather than merely readable.

## Licence

MIT OR Apache-2.0.
