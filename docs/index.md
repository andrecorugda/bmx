---
layout: default
title: BMX
---

{% raw %}
# BMX

**Burxt Markup Language, Extensible** — markdown with one unambiguous reading and a typed hole
in it.

```bmx
# Receipt {{ order.reference }}

Thank you, **{{ customer.name }}**. Your total is {{ to_string(order.total) }}.

- Delivery: {{ order.delivery }}
- Paid: {{ order.paid_at }}
```

That is a whole document. It renders to HTML, and in a host with a type system every `{{ … }}`
is checked before the page exists.

- **[Writing a document](syntax.html)** — every construct, with what it renders to
- **[Turning it into a page](rendering.html)** — the two ways, and which to use
- **[Styling the output](styling.html)** — the HTML you get, and how to write CSS against it
- **[Building on BMX](building-on.html)** — for anyone writing a layer above it, star-burxt included
- **[When it refuses](errors.html)** — every error code and what to do about it

The normative documents live beside these: [`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md)
is the grammar, [`BOUNDARY.md`](https://github.com/andrecorugda/bmx/blob/main/BOUNDARY.md) draws
the line between the format and its host, and
[`ESCAPING.md`](https://github.com/andrecorugda/bmx/blob/main/ESCAPING.md) is the one place BMX
is opinionated about output. **These pages are for people writing documents. Those are for people
writing parsers.**

## Why not just markdown

Two reasons, and neither is the syntax.

### It always fails loudly

Markdown is designed so that nothing is ever a syntax error. `*bold` with no closing star renders
as the characters `*bold`. An unterminated code fence swallows the rest of the file. Three
dialects — CommonMark, GFM, Pandoc — disagree about the rest, so the same document means
different things in different tools.

BMX has one reading, and anything else is an error with a code:

```
BMX-E002 at 2: unterminated emphasis
```

That matters most where documents are generated rather than typed. A truncated document gets
told, instead of shipping a page with a stray asterisk in it.

### The hole is typed

`{{ … }}` is where an expression goes, and **BMX does not define what an expression is.** That
belongs to whichever language is rendering the document, which is why a format this small can be
adopted by a language with types and by one without.

That gives two levels of conformance, and the second is the reason BMX exists:

| Level | What it means | Who can reach it |
|---|---|---|
| **1 — renders** | parses, substitutes values, escapes on output | any language |
| **2 — checks** | every expression verified against a declared interface *before* the document renders | a language with a type system |

**A template is the last place in most programs where nothing is checked.** The slot names a field
that may not exist, holds a type it cannot state, and escapes by convention. Level 2 is where that
stops being true — a missing field becomes a build error, and in [Burxt](https://burxt-lang.org) a
rounding contract on a money value survives all the way to the tag.

## Status

**0.1.** Two implementations, one author, so this is not yet a standard — see
[`VERSIONING.md`](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md) for what 1.0
requires. The reference parser is `reference/bmx.js`, zero dependencies, written to be read.
Burxt's is `lib/bmx.bx` and is the only implementation at level 2.

The format is [MIT OR Apache-2.0](https://github.com/andrecorugda/bmx).
{% endraw %}
