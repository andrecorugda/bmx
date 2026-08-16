---
layout: default
title: When BMX says no
section: guide
description: Markdown never fails. That sounds generous until a machine writes your documents.
---

{% raw %}
# 3. When BMX says no

## What this is for

Markdown has one property that everybody likes and nobody examines: **it never fails.**

Whatever you give it, something comes out. That is genuinely lovely when you are typing a comment
into a text box. It is a different thing entirely when the document was generated, or edited by
somebody in a hurry, or written by a program.

## The wrong kind of forgiving

Here is a document that got truncated — a network hiccup, a script that stopped, a copy-paste that
took nine lines of ten:

```bmx
# Invoice 4417

Thank you for your order. Your balance is **£240.00
```

Markdown renders that. The page goes out looking almost right:

> **Invoice 4417**
>
> Thank you for your order. Your balance is \*\*£240.00

A stray pair of asterisks. Somebody notices next week, or nobody does.

BMX stops:

```
BMX-E002 at 46: unterminated strong
```
<figure class="shot">
  <img src="/assets/examples/refused-unterminated-strong.png" alt="A truncated document, and BMX refusing to render it">
  <figcaption>The truncated invoice. Markdown renders this with two stray asterisks and the page ships; BMX renders nothing at all.</figcaption>
</figure>


Nothing renders. The build fails, the job fails, and you find out at the moment the document was
wrong rather than at the moment a customer reads it.

## Autocorrect and spellcheck

This is the whole distinction, and it is worth holding on to.

**Autocorrect** decides what you probably meant and changes it. It is right most of the time, and
when it is wrong it is wrong *silently* — you find out when somebody replies to your message
confused.

**Spellcheck** stops and points. It costs you a second. It never quietly changes what you said.

Markdown is autocorrect. BMX is spellcheck. Neither is better in the abstract; they are for
different situations. **The situation BMX is built for is the one where a document might not have
been written by a careful human**, and the cost of a page that looks nearly right is somebody's
money or somebody's afternoon.

## Every refusal has a code

Not a stack trace, not a guess — a code, a position, and a sentence:

```
BMX-E011 at 0: a heading needs exactly one space after its #
```

The code is the part that is the same in **every** implementation of BMX, in every language. So a
build script can key on `BMX-E011` and keep working when you switch renderers.

Here are the ones you will actually meet:

| You wrote | You get |
|---|---|
| `#Heading` | `BMX-E011` — a heading needs one space after its `#` |
| `a *bold sentence` | `BMX-E002` — unterminated emphasis |
| `Hi {{ name` | `BMX-E001` — unterminated slot |
| `see [docs](x` | `BMX-E004` — unterminated link target |
| an indented `- item` | `BMX-E012` — 0.1 has no nesting |
| `a \q b` | `BMX-E021` — only `` ` `` `*` `[` `{` `\` may be escaped |

The [full list](../errors.html) has one entry for each, with the input that produces it.

## Why `#Heading` is an error

This one surprises people, so it is worth doing properly.

```bmx
#Heading
```

Markdown reads that as a paragraph that happens to start with `#`. Reasonable! And it means a
missing space silently demotes your heading to body text — same file, different meaning, no
warning. You get a page where one heading is mysteriously not a heading.

BMX will not choose for you. One space after the `#`, or say what you meant.

The same reasoning covers the rest: **when a document could mean two things, BMX asks rather than
picks.** Every place that feels strict is a place where markdown quietly decided something.

## It stops at the first one

You get one error, not a list. That is deliberate for now: reporting every error at once means
guessing how to carry on past the first, and two implementations that guess differently would
disagree about a document — which is the entire thing this format exists to prevent.

Better diagnostics are a real want and they are on the list. Being *wrong together* is not.

---

**Next:** [Views that check themselves](04-views-that-check-themselves.html) — where the document
stops being text and starts being checked code.
{% endraw %}
