---
layout: default
title: BMX
description: "Burxt Markup Language, Extensible — you write markdown, you get a page, and it tells you when the document is wrong."
---

{% raw %}
# BMX

**Burxt Markup Language, Extensible.** You write markdown. You get a page. The difference is that
BMX tells you when the document is wrong, instead of printing something that looks nearly right.

```bmx
# Receipt {{ order.reference }}

Thank you, **{{ customer.name }}**. Your total is {{ order.total }}.

- Delivery: {{ order.delivery }}
- Paid: {{ order.paid_at }}
```

That is a whole document. If you have written a README you can already write BMX; the `{{ … }}`
holes are the only new idea, and page 2 of the guide is about those.

## Start here

**[1. Your first document](guide/01-your-first-document.html)** — write one, render it, see the
HTML that comes out. Five minutes.

Then:

- **[2. Putting values in](guide/02-putting-values-in.html)** — slots, and the form letter that
  posts *"Dear ,"*
- **[3. When BMX says no](guide/03-when-bmx-says-no.html)** — autocorrect versus spellcheck
- **[4. Views that check themselves](guide/04-views-that-check-themselves.html)** — the recipe
  card and the order ticket

## Then look things up

| | |
|---|---|
| [Writing a document](syntax.html) | every construct, with the HTML it produces |
| [Styling the output](styling.html) | the tags you get, and how CSS, Tailwind and SCSS attach |
| [When it refuses](errors.html) | every error code, with the input that causes it |
| [Turning it into a page](rendering.html) | the two rendering paths, in detail |
| [Building on BMX](building-on.html) | for anyone writing a framework on top |

## Why it exists

Two reasons, and neither is the syntax.

### It tells you when a document is wrong

Markdown never fails. Whatever you give it, something comes out — which is lovely in a comment box
and dangerous when the document was generated, truncated, or written in a hurry.

```bmx
Your balance is **£240.00
```

Markdown prints that with two stray asterisks and the page ships. BMX says:

```
BMX-E002 at 16: unterminated strong
```

Autocorrect quietly changes what you meant. Spellcheck stops and points. **BMX is spellcheck.**

### The blanks can be checked before the page exists

`{{ … }}` is a hole, and BMX deliberately has no opinion about what goes in it — that belongs to
whatever language is doing the rendering. Which means a language with types can check it:

| | What happens to a typo like `{{ order.custmer }}` |
|---|---|
| Most template languages | prints nothing; the page ships |
| **BMX, rendering** | **refuses; nothing renders** |
| **BMX, compiled** | **a build error naming the field, and what the fields actually are** |

**A template is the last place in most programs where nothing is checked.** The database checks
your data, the API checks it, your code checks it — and then the template prints whatever it is
handed. That is the gap BMX closes.

In [Burxt](https://burxt-lang.org) it goes further: a money value keeps its rounding rule all the
way to the tag, so a template cannot quietly round `£4.947525` to two places on your behalf.

## Status

**0.2**, and honest about it: two implementations, both written by one author, so this is a format
rather than a standard yet. [`VERSIONING.md`](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md)
says what 1.0 requires — an implementation by somebody who did not write the spec.

The grammar is [`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md), the
conformance suite is [`tests/`](https://github.com/andrecorugda/bmx/tree/main/tests), and where
they disagree the tests win. MIT OR Apache-2.0.
{% endraw %}
