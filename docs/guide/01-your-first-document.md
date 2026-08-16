---
layout: default
title: Your first document
section: guide
description: A BMX document is a text file. Write one, render it, and see exactly what comes out.
---

{% raw %}
# 1. Your first document

## What this is for

A BMX document is a **text file you can read**. That is the whole idea. Open it in any editor,
send it to a colleague who has never heard of BMX, and they can still tell what the page will say.

Here is one. Put it in a file called `hello.bmx`:

```bmx
# Hello

This is my first document.
```

That is a complete document. No boilerplate, no wrapper, no configuration.

## What comes out

Render it and you get HTML:

```html
<article class="bmx"><h1>Hello</h1><p>This is my first document.</p></article>
```

Three things happened, and none of them needed a decision from you:

| In the document | In the page |
|---|---|
| `# Hello` | `<h1>Hello</h1>` |
| a blank line | the end of that block |
| `This is my first document.` | `<p>This is my first document.</p>` |

Everything sits inside one `<article class="bmx">`. That wrapper is the only thing BMX adds, and
it exists so you have something to write CSS against — see [styling](../styling.html).

## The rule that decides everything

**A blank line ends a block.** That is it. Not indentation, not tags, not closing anything.

```bmx
# A heading

The first paragraph.

The second paragraph.
```

```html
<article class="bmx"><h1>A heading</h1><p>The first paragraph.</p><p>The second paragraph.</p></article>
```

Two blank lines, three blocks. If you have ever written a README, you already know this.

## Try changing it

Each of these does what it looks like:

```bmx
# A big heading
## A smaller one
### Smaller still
```

```bmx
- a bullet
- another bullet
```

```bmx
1. first step
2. second step
```

```bmx
> Something quoted.
```

And inside a sentence:

```bmx
Some *emphasis*, some **strong**, and some `code`.
```

→ `Some <em>emphasis</em>, some <strong>strong</strong>, and some <code>code</code>.`

The full list is on [Writing a document](../syntax.html), but you can build a real page with
what is on this screen.

## One difference from markdown, and it will save you

If you have used markdown, you have done this:

```bmx
This is *important
```

Markdown prints `This is *important` — the star just sits there, and you find out when somebody
reads the page. BMX stops:

```
BMX-E002 at 8: unterminated emphasis
```

It is the difference between **autocorrect and spellcheck**. Autocorrect silently changes what you
meant and moves on. Spellcheck stops and points. BMX is spellcheck.

That is the whole personality of the format, and the next two pages are about what it buys you.

---

**Next:** [Putting values in](02-putting-values-in.html) — the part that makes a document a page
about *something*.
{% endraw %}
