# The boundary — what BMX owns, and what the host owns

**This file exists so that host semantics cannot leak into the format by accident.** It was
written before the first parser, because the leak is always retroactive: a host implements
something convenient, the format quietly acquires it, and the next language cannot implement
BMX without also implementing the first host's type system.

## The line

| BMX owns | The host owns |
|---|---|
| Document structure — what a heading, a list, a paragraph is | What an expression *is* |
| Where an expression may appear, and its delimiters | Whether that expression is valid |
| That an expression's text is non-empty and on one line | Its types, its scope, its evaluation |
| The escaping **rule** — see [`ESCAPING.md`](ESCAPING.md) | The escaping **function** for its output format |
| Error codes for anything structural | Error messages for anything semantic |

The test: **could a language with no types implement this?** If a rule cannot be checked without
knowing what a value is, it is the host's. If it can, it is BMX's.

## What a host receives

A slot node, and nothing more:

```json
{"type": "slot", "expression": "order.total", "offset": 142}
```

`expression` is the trimmed bytes between `{{` and `}}`. `offset` is where they started, so the
host can report an error at a real position in the *source file the author wrote*, not in
whatever it generated. **A host that cannot point at the original text will produce diagnostics
nobody can act on**, which is why the offset is mandatory rather than optional.

## What a host may not ask BMX for

- **A type.** BMX has none, and adding one would make it a language.
- **An evaluation order.** BMX emits nodes in document order; anything else is the host's.
- **A variable scope.** `{{ x }}` is text. Whether `x` exists is not a structural question.
- **A dialect flag.** There is one BMX. A host that wants different structure wants a different
  format, and should say so rather than passing an option.

## Conformance levels

This is how BMX stays adoptable without the guarantee becoming meaningless.

**Level 1 — renders.** The implementation parses per [`SPEC.md`](SPEC.md), passes
[`tests/cases`](tests/cases) and [`tests/errors`](tests/errors), and substitutes slot values at
render time with the host's escaping applied. Any language can reach level 1. It is what
JavaScript, PHP or Python would implement.

**Level 2 — checks.** Everything in level 1, plus: **every slot expression is checked before the
document renders**, against a declared interface for the data. A slot naming something that does
not exist, or something of the wrong type, is an error at build time and not a blank on a page.

Level 2 is not a courtesy. It is the reason this format was worth defining: a template is the
last place in most programs where nothing is checked, and level 2 is the level at which that
stops being true. **Only a host with a type system can reach it, and only a host with contracts
can carry a promise like a rounding rule through a slot** — which today is one language.

State your level in your README. Claiming level 2 without a check that fails is the one thing
this document asks implementations not to do.

## Why the guarantee is not in the format

The obvious alternative was to put the checking in BMX — a type annotation on every slot, or a
schema block at the top. It was rejected, and the reason is worth keeping because it will come
up again:

**A format cannot enforce anything.** It has no compiler. Whatever it declares, some
implementation renders without checking, and then the guarantee is a comment. Putting the
structure in the format and the enforcement in the host means the part that travels is the part
that can travel, and the part that cannot be faked stays where it can be verified.
