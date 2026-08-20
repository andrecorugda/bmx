---
layout: default
title: BMX
description: "Burxt Markup Language, Extensible — you write markdown, you get a page, and it tells you when the document is wrong."
---

<!-- **The mark, then the tagline as the heading** — star-burxt's arrangement, which Andre asked for by
     pointing at it: *"follow star where the tag line is big Build a front end by writing a document."*

     Their page reads mark → big `h1` sentence → explanatory paragraph, and the `h1` does not contain the
     product's name at all. That is the part worth copying: **a landing heading should say what you get,
     not what the thing is called.** The name is already in the mark above it, in the tab title, and in the
     paragraph below, so spending the one big line on it says nothing a visitor did not already know.

     So the mark moves out of the `h1` into its own `<p>`, exactly as star does, and the heading becomes the
     claim. `alt="BMX"` still carries the name for anyone without images.

     **The tagline is `SPEC.md` §1, not copy.** *"It always fails loudly… never output that looks nearly
     right."* Every word of "cannot be quietly wrong" is that sentence, which is the one thing BMX has that
     markdown does not — and the reason it is worth a heading is that it is the only claim here a reader
     cannot get from any other markdown dialect. -->
<p class="lockup">
  <img src="{{ site.baseurl }}/assets/bmx-lockup.svg" alt="BMX" width="239" height="96">
</p>

{% raw %}
# Write a page that cannot be quietly wrong

**Burxt Markup Language, Extensible.** You write markdown. You get a page.

{% endraw %}{% include showcase.html %}{% raw %}

The difference from markdown is that **BMX tells you when the document is wrong**, instead of
printing something that looks nearly right.

```bmx
# Receipt {{ order.reference }}

Thank you, **{{ customer.name }}**. Your total is {{ order.total }}.

- Delivery: {{ order.delivery }}
- Paid: {{ order.paid_at }}
```

That is a whole document. If you have written a README you can already write BMX — the `{{ … }}`
holes are the only new idea, and page 2 of the guide is about those.

And when a page needs to repeat, branch, or be built from reusable pieces, there is exactly one
more thing to learn:

```bmx
:for: line in order.lines
  - {{ line.sku }} × {{ to_string(line.qty) }}
:!for:
```

One construct — a **block** — which also gives you `:if:` and components you declare yourself.
BMX does not know what `for` means; the host does.

## Start here

**[1. Your first document](guide/01-your-first-document.html)** — write one, render it, see the
HTML that comes out. Five minutes.

Then:

- **[2. Putting values in](guide/02-putting-values-in.html)** — slots, and the form letter that
  posts *"Dear ,"*
- **[3. When BMX says no](guide/03-when-bmx-says-no.html)** — autocorrect versus spellcheck
- **[4. Views that check themselves](guide/04-views-that-check-themselves.html)** — the recipe
  card and the order ticket

## Or just look up what you need

| | |
|---|---|
| [In your editor](editor.html) | colour, a live preview, and mistakes underlined as you type |
| [How do I…?](how-do-i.html) | short answers — a list, a component, a class for CSS, a click |
| [Writing a document](syntax.html) | every construct, with the HTML it produces |
| [Styling the output](styling.html) | the tags you get, and how CSS, Tailwind and SCSS attach |
| [When it refuses](errors.html) | every message, with the input that causes it and the fix |

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

## Can you rely on it?

**Your document means the same thing in every tool that reads BMX**, and that is checked rather than
promised — more than ninety documents paired with exactly what each should produce, plus two
independent implementations run against each other.

BMX is **0.12**, and honest about what that means: both implementations have one author, so they
catch mistakes and not ambiguity. [Why documents agree](promise.html) is the short version, and it
says plainly what would have to happen for this to be 1.0 — which is an implementation by somebody
who did not write the rules. If that sounds like you, [writing an
implementation](implementing.html) is a suite that takes any command and an afternoon.

Free to use, MIT or Apache-2.0.
{% endraw %}
