---
layout: default
title: Implementing BMX
description: "Write a BMX reader in your language. The suite is data, so it is an afternoon rather than a port."
---

{% raw %}
# Writing an implementation

**BMX is a format, so nothing stops you reading it in your own language** — and this page is the
path, because until now the capability existed and the invitation did not.

There are two ways to extend BMX and they are different jobs:

| You are writing | Go to |
|---|---|
| a layer **above** BMX — a component system, a framework, a site generator | [Building on BMX](building-on.html) |
| a reader **of** BMX — a parser, a renderer, in any language | this page |

If you pick wrong you will read a page that is not for you and conclude the door is shut. It is
not: [why documents agree](promise.html) ends by saying 1.0 arrives when somebody who did not write
the rules builds a tool from them and it passes. **You are that person, and this is what to run.**

## What you are building

Three levels, and only the first is required to say you implement BMX. They are defined normatively
in [`BOUNDARY.md`](https://github.com/andrecorugda/bmx/blob/main/BOUNDARY.md).

| | What it does | Who can |
|---|---|---|
| **the parser** | source in, a tree out — or an error with a code | any language |
| **level 1 — renders** | the parser, plus slot values substituted and **escaped on output** | any language |
| **level 2 — checks** | level 1, plus every slot expression verified against a declared interface *before* the document renders | only a language with types |

Start at the parser. It is what the conformance suite measures, and it is a few hundred lines — no
lexer generator, no parser combinator library, no dependency of any kind. `reference/bmx.js` is
roughly seven hundred lines of code, with four hundred more explaining itself, and it is written to
be read top to bottom by exactly the person on this page.

**Say your level in your README, and do not claim level 2 without a check that fails.** That is the
one thing [`BOUNDARY.md`](https://github.com/andrecorugda/bmx/blob/main/BOUNDARY.md) asks of an
implementation.

## The suite is data, which is the whole design

The specification's executable half is a folder of documents paired with exactly what each must
produce. Clone the repository and look:

```text
tests/cases/024-block-simple.bmx     a document
tests/cases/024-block-simple.json    the tree it must produce, exactly
tests/errors/001-unterminated-slot.bmx    a document that must be refused
tests/errors/001-unterminated-slot.error  the code it must be refused with
```

More than ninety documents, across both folders. **There is no framework to port and no runner to
reimplement** — the pairs are JSON and text, so conformance costs an afternoon in any language
rather than a port. That claim is the reason the format is worth adopting, and it is the one this
page exists to stop being a secret.

**Read three `.json` files and you have the tree.** They are not a description of the AST; they are
the AST, for real documents, and where they and the prose disagree the files win. The normative
table of node kinds is [`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md) §5, but
you can write most of a parser from the fixtures alone.

Here is the shape, from the two constructs every document has. This document:

```bmx
# Receipt {{ order.reference }}

Thank you, {{ customer.name }}.
```

parses to this, and the fixtures look like it:

```json
{
  "type": "document",
  "children": [
    {
      "type": "heading",
      "level": 1,
      "children": [
        { "type": "text", "value": "Receipt " },
        { "type": "slot", "expression": "order.reference", "offset": 13 }
      ],
      "offset": 0
    },
    {
      "type": "paragraph",
      "children": [
        { "type": "text", "value": "Thank you, " },
        { "type": "slot", "expression": "customer.name", "offset": 47 },
        { "type": "text", "value": "." }
      ],
      "offset": 33
    }
  ]
}
```

## Running the suite against your implementation

```sh
burxt build tests/harness.bx -o harness
./harness '<your command>'
```

The command is run **once per case with the document's path appended**, and must either

- print the AST as JSON on stdout and exit 0, or
- print an error **beginning with its `BMX-Ennn` code** and exit non-zero.

So most people point it at a two-line wrapper:

```sh
./harness 'node reference/bmx.js'
./harness './my-bmx --ast'
./harness 'python3 -m mybmx.cli'
```

It prints one line per failure, then a count — which grows as cases are added, so treat the numbers
here as a shape rather than a target:

```text
024-block-simple.bmx:
  expected {"type":"document","children":[{"type":"block","name":"card",...
  actual   {"type":"document","children":[{"type":"block","name":"card",...
92 cases, 91 passed, 1 failed
```

**The harness is not part of the specification, and it needs a Burxt compiler to build.** That is a
prerequisite this page did not have when the harness was thirty lines of Python, and it is stated rather
than buried: **this repository builds its own tooling in the language it serves, and that choice is not a
claim on yours.**

**So if a Burxt toolchain is inconvenient where you are, throw the harness away and write your own.** The
loop is: for each `.bmx` in `cases/`, run your parser, compare the JSON to the `.json` beside it — as
parsed values, because key order is not specified; for each `.bmx` in `errors/`, expect a non-zero exit and
an error beginning with the code in the `.error` file. That is the whole contract, it is a page of code in
any language, and **the cases are the specification, not the program that walks them.** Nothing in BMX
requires you to run our tooling to claim conformance.

## The four things an implementation gets wrong

Not guesses. Each one is a defect that shipped here, in a release, and became a fixture.

**Offsets are the byte index of the first byte the author wrote.** The `#` of a heading, the `-` of
a list item, the `[` of a link, the first `:` of a block's fence. The cheap way to get this right is
to strip leading whitespace in **one** place — the line builder — so every offset downstream is
already a real source position; the alternative is adding the indent back at twenty call sites,
which is twenty chances to forget one. A slot is the one exception: its `offset` is the first byte
of the *trimmed expression*, because the host is handed the expression and must point inside it.

**Adjacent text nodes are always merged.** An implementation emitting `text("a")`, `text("b")` where
another emits `text("ab")` fails the suite, and rightly — they are the same document.

**Stop at the first error.** Recovery is a real want and an editor needs it, but recovery that
differs between implementations is worse than none, so it is outside conformance for now.

**The code is the conformance surface; the message is yours.** `tests/errors/*.error` holds a bare
`BMX-E001`, and the harness checks only that your output *starts with* it. Write the best message
your language can — but never one that tells an author to write something the format also refuses,
which is a trap this project has a runner for.

## If you render, escaping is not optional

The moment your implementation produces output rather than a tree, one rule binds it, and it is
normative in [`ESCAPING.md`](https://github.com/andrecorugda/bmx/blob/main/ESCAPING.md):

> **A slot's value is escaped for the output format, at render time, always. There is no
> configuration that turns it off, and no per-slot syntax that opts out.**

There is no `{{{ raw }}}` and there will not be one. A host that wants to allow trusted markup does
it in the host language, where the waiver is a named call a reviewer can grep. Two further hazards
the rule covers and a first implementation usually misses: **a link target is escaped per-context
and its scheme is checked** — a document must not reach the output through `javascript:` — and a
code fence's **info string** is metadata, so a host putting it in output escapes it there.

## Then ask the question the suite cannot

Passing the suite proves you match what was written down. It cannot prove that what was written down
covers everything, because a suite is made of the things somebody thought of.

```sh
burxt build tests/agree.bx -o agree
./agree 'node reference/bmx.js' '<your command>'
```

Both commands are run over every document in `tests/cases` and `tests/errors`. Success must produce
the same AST; failure must produce the same code — the message after it is each implementation's own
words and is not compared. **A disagreement here is a bug report against the specification**, not
against you: it is exactly where the prose left room. That is how the slot-offset defect in
`023-slot-offset-survives-a-stripped-line` was found, and planning a second implementation is what
surfaced it.

If you find one, [say so](https://github.com/andrecorugda/bmx/issues). A third implementation
disagreeing with these two is the most useful thing that can currently happen to this format.

## What you do not have to implement

Stated because an implementer who thinks these are required will conclude the job is bigger than it
is:

- **Anything inside `{{ … }}`.** BMX does not define what an expression is — you hand the trimmed
  bytes and the offset to whatever is rendering, and stop. That is the format's central boundary.
- **Lints.** The `BMX-W` codes on [when it refuses](errors.html) are a quality-of-life surface, not
  conformance. No fixture requires them.
- **Level 2.** If your language has no type system there is nothing to check a slot against, and
  saying so plainly is the honest answer rather than a gap.
- **Nested lists, quotes, reactivity, components, a dialect flag.** Not absent from your
  implementation — absent from the format. [`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md)
  §7 lists every omission with the trigger that would earn it a version.

## What you are signing up for, honestly

**BMX is 0.12, and inside 0.x a minor version may break a document.** Every such change is written
up in [`VERSIONING.md`](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md) with the
fixture it edited, and the rule is mechanical: an edited case in `tests/cases/` proves a major, so
`git diff --diff-filter=M tests/cases` tells you whether a release can move a document under you.
Pin a tag and re-run the suite when you bump it; that is the whole maintenance cost.

**Two things you should know before you start rather than after.** Both implementations here have
one author, so their agreement catches drift and regression — it does not prove the spec
unambiguous. And there is no npm package and no registry release of the reference parser, on
purpose: publishing one is a promise to maintain a release channel, and a format at 0.12 should not
make that promise yet. Copy the file.

**Which is why your implementation is worth more to this format than another feature is.** 1.0 is
not earned by the feature list looking finished. It needs an implementation written by somebody who
did not write this spec, passing the suite, plus a real document set that has tested
[`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md) §7's absences against something
other than imagination. Both halves are waiting on somebody who is not us.
{% endraw %}
